"""Native Qwen Code adapter; no model loop, task steering or SparkOps dependency.

The CLI owns tools, reasoning and compaction. An outer mount namespace owns
disposable filesystem isolation. A byte-preserving local relay records request
controls and returned usage without adding context or altering model responses.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import http.client
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import threading
import time
from urllib.parse import urlsplit

from experiments import isolation_v2
from experiments.concurrency_study import write_json, utc


def settings(model, endpoint, context=230000, effort='xhigh'):
    if not 32768 <= context <= 230000:
        raise ValueError('Study context must be between 32768 and 230000')
    address = urlsplit(endpoint)
    if (address.scheme not in ('http', 'https') or not address.hostname
            or address.username or address.password or address.query or address.fragment):
        raise ValueError('Credential-free OpenAI-compatible endpoint required')
    return {
        '$version': 4,
        'general': {'enableAutoUpdate': False},
        'telemetry': {'enabled': False},
        'security': {'auth': {'selectedType': 'openai'}},
        'context': {'fileName': ['AGENTS.md', 'QWEN.md'], 'autoCompactThreshold': .85},
        'model': {'name': model, 'reasoningEffort': 'high', 'maxSessionTurns': 150},
        'modelProviders': {'openai': [{'id': model, 'baseUrl': endpoint, 'envKey': 'OPENAI_API_KEY',
            'generationConfig': {'contextWindowSize': context, 'timeout': 300000, 'maxRetries': 0,
                'modalities': {'image': False}, 'toolResultContentFormat': 'string',
                'samplingParams': {'temperature': .6, 'top_p': .95, 'max_tokens': 32768},
                'extra_body': {'reasoning_effort': effort, 'chat_template_kwargs': {'enable_thinking': True}}}}]},
    }


class Relay:
    """Passive per-worker HTTP transport observer, not a coordination channel."""
    def __init__(self, endpoint, output):
        self.endpoint = urlsplit(endpoint.rstrip('/'))
        if (self.endpoint.scheme not in ('http', 'https') or not self.endpoint.hostname
                or self.endpoint.username or self.endpoint.password or self.endpoint.query or self.endpoint.fragment):
            raise ValueError('Invalid upstream')
        self.output = Path(output)
        self.output.touch(exist_ok=False)
        self.lock = threading.Lock()
        self.sequence = 0
        self.connections = set()
        self.sockets = set()
        self.handlers = set()
        self.handler_errors = []
        self.stopping = False
        relay = self
        class Handler(BaseHTTPRequestHandler):
            protocol_version = 'HTTP/1.0'
            def log_message(self, *_):
                pass
            def do_POST(self):
                if self.path != '/v1/chat/completions':
                    self.send_error(404)
                    return
                length = int(self.headers.get('Content-Length', 0))
                if not 0 < length <= 8 * 1024 * 1024:
                    self.send_error(413)
                    return
                raw = self.rfile.read(length)
                body = json.loads(raw)
                with relay.lock:
                    relay.sequence += 1
                    identity = relay.sequence
                relay.log({'event': 'request', 'request': identity, 'model': body.get('model'),
                    'reasoning_effort': body.get('reasoning_effort'),
                    'chat_template_kwargs': body.get('chat_template_kwargs'),
                    'max_tokens': body.get('max_tokens', body.get('max_completion_tokens')),
                    'message_count': len(body.get('messages', [])), 'bytes': length,
                    'tool_count': len(body.get('tools', []))})
                cls = http.client.HTTPSConnection if relay.endpoint.scheme == 'https' else http.client.HTTPConnection
                connection = cls(relay.endpoint.hostname, relay.endpoint.port, timeout=300)
                with relay.lock:
                    relay.connections.add(connection)
                path = relay.endpoint.path.rstrip('/') + '/chat/completions'
                headers = {'Content-Type': 'application/json'}
                # The study's configured endpoint uses no private bearer credential.
                # Never accept a caller-selected destination or log authorization.
                if self.headers.get('Authorization'):
                    headers['Authorization'] = self.headers['Authorization']
                pending = b''
                response = None
                try:
                    connection.connect()
                    with relay.lock:
                        if relay.stopping:
                            raise OSError('Relay is stopping')
                        upstream_socket = connection.sock
                        relay.sockets.add(upstream_socket)
                    connection.request('POST', path, body=raw, headers=headers)
                    response = connection.getresponse()
                    self.send_response(response.status)
                    self.send_header('Content-Type', response.getheader('Content-Type', 'application/json'))
                    self.end_headers()
                    relay.log({'event': 'response', 'request': identity, 'status': response.status})
                    while chunk := response.read1(65536):
                        self.wfile.write(chunk)
                        self.wfile.flush()
                        pending += chunk
                        while body.get('stream') and b'\n' in pending:
                            line, pending = pending.split(b'\n', 1)
                            if line.startswith(b'data: ') and line[6:] != b'[DONE]':
                                try:
                                    event = json.loads(line[6:])
                                except ValueError:
                                    continue
                                if event.get('usage'):
                                    relay.log({'event': 'usage', 'request': identity, 'usage': event['usage']})
                                for choice in event.get('choices', []):
                                    delta = choice.get('delta', {})
                                    if delta.get('reasoning_content') or delta.get('reasoning'):
                                        relay.log({'event': 'reasoning_observed', 'request': identity,
                                            'characters': len(delta.get('reasoning_content') or delta['reasoning'])})
                    if pending and not body.get('stream'):
                        try:
                            event = json.loads(pending)
                            if event.get('usage'):
                                relay.log({'event': 'usage', 'request': identity, 'usage': event['usage']})
                        except ValueError:
                            pass
                except (OSError, http.client.HTTPException) as error:
                    relay.log({'event': 'transport_error', 'request': identity, 'type': type(error).__name__})
                finally:
                    # The handler alone owns HTTPResponse/HTTPConnection cleanup.
                    # Shutdown may interrupt sockets, but must not race read1()
                    # by closing the response from the recorder's main thread.
                    try:
                        if response is not None:
                            response.close()
                    finally:
                        try:
                            connection.close()
                        finally:
                            with relay.lock:
                                relay.connections.discard(connection)
                                if 'upstream_socket' in locals():
                                    relay.sockets.discard(upstream_socket)
        class Server(ThreadingHTTPServer):
            def handle_error(self, request, client_address):
                # ThreadingMixIn catches handler exceptions internally. Fence
                # completion here instead of printing a private traceback and
                # silently treating the stopped thread as successful recording.
                relay.handler_failed(sys.exc_info()[1])

            def process_request(self, request, client_address):
                current = threading.Thread(target=self.process_request_thread,
                    args=(request, client_address), daemon=True)
                with relay.lock:
                    if relay.stopping:
                        self.shutdown_request(request)
                        return
                    relay.handlers.add(current)
                    relay.sockets.add(request)
                    current.start()
            def process_request_thread(self, request, client_address):
                current = threading.current_thread()
                try:
                    super().process_request_thread(request, client_address)
                except BaseException as error:
                    # Also cover cleanup failures and abnormal thread exits
                    # outside ThreadingMixIn's Exception handler.
                    relay.handler_failed(error)
                finally:
                    with relay.lock:
                        relay.handlers.discard(current)
                        relay.sockets.discard(request)
        self.server = Server(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def log(self, event):
        with self.lock, self.output.open('a') as stream:
            stream.write(json.dumps({'at': utc(), 'mono_ns': time.monotonic_ns(), **event}) + '\n')

    def handler_failed(self, error):
        error_type = type(error).__name__
        with self.lock:
            self.handler_errors.append(error_type)
        try:
            self.log({'event': 'handler_error', 'type': error_type})
        except Exception:
            # The in-memory fence must survive an unavailable evidence sink.
            pass

    def __enter__(self):
        self.thread.start()
        return f'http://127.0.0.1:{self.server.server_port}/v1'

    def __exit__(self, *_):
        with self.lock:
            self.stopping = True
        self.server.shutdown()
        # A timed-out native process must not leave inference in flight when the
        # sequential recorder advances to another project.
        with self.lock:
            sockets = list(self.sockets)
            handlers = list(self.handlers)
        for active_socket in sockets:
            try:
                active_socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        self.server.server_close()
        self.thread.join(timeout=5)
        deadline = time.monotonic() + 10
        for handler in handlers:
            handler.join(timeout=max(0, deadline - time.monotonic()))
        if any(handler.is_alive() for handler in handlers):
            raise RuntimeError('Relay handler did not terminate; refusing to finalize transport evidence')
        if self.handler_errors:
            raise RuntimeError('Relay handler failed; refusing to finalize transport evidence')


def sandbox(root, role, argv, session, *, pi=False):
    root = Path(root).resolve()
    resources = [root / 'runtime']
    if pi:
        resources.append(root / 'pi-source')
    command = isolation_v2.command(root, root / 'work', argv, readonly=resources)
    position = command.index('--')
    # Fresh native home for each worker, shared source only. No operator homes,
    # provider credentials, prior trials, reference solution or peer logs mounted.
    command[position:position] = ['--bind', str(root / 'qwen-home' / role), '/home/worker/.qwen',
        '--setenv', 'OPENAI_API_KEY', 'EMPTY', '--setenv', 'QWEN_SESSION_ID', session,
        '--setenv', 'NO_COLOR', '1', '--setenv', 'QWEN_CODE_DISABLE_AUTO_UPDATE', '1']
    return command


def argv(root, prompt, model, session):
    return ['/usr/bin/node', str(Path(root) / 'runtime/bin/qwen'), '--auth-type', 'openai',
            '--model', model, '--session-id', session, '--approval-mode', 'yolo',
            '--output-format', 'stream-json', '--chat-recording', prompt]


def consume_native(source, output, events, state, observer=None, role='worker'):
    """A stopped reader is not evidence of EOF; preserve recorder failures."""
    state.update(eof=False, error_type=None)
    try:
        for raw in source:
            output.write(raw)
            output.flush()
            try:
                event = json.loads(raw)
            except ValueError:
                event = {'unparsed': raw.decode(errors='replace')}
            events.write(json.dumps({'at': utc(), 'mono_ns': time.monotonic_ns(), 'event': event}) + '\n')
            events.flush()
            if observer:
                observer.capture(role + ':native-event')
        state['eof'] = True
    except Exception as error:
        state['error_type'] = type(error).__name__


def record(root, role, plan, observer=None):
    directory = root / role
    directory.mkdir()
    profile = root / 'qwen-home' / role
    session = plan['sessions'][role]
    row = {'role': role, 'session': session}
    with Relay(plan['endpoint'], directory / 'transport.jsonl') as endpoint:
        write_json(profile / 'settings.json', settings(plan['model'], endpoint,
            plan['context_window'], plan['server_effort']))
        native = argv(root, (root / (role + '.txt')).read_text(), plan['model'], session)
        command = sandbox(root, role, native, session, pi=plan['pi_enabled'])
        write_json(directory / 'command.json', native)
        write_json(directory / 'isolation-command.json', command)
        row.update(started_at=utc(), start_monotonic_ns=time.monotonic_ns())
        with (directory / 'stdout.jsonl').open('wb') as out, (directory / 'stderr.bin').open('wb') as err, \
                (directory / 'events.jsonl').open('w') as events:
            try:
                process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                    stderr=err, start_new_session=True)
            except OSError as error:
                row.update(exit_code=None, launch_error=str(error), stream_complete=False,
                    finished_at=utc(), end_monotonic_ns=time.monotonic_ns())
                row['elapsed_seconds'] = (row['end_monotonic_ns'] - row['start_monotonic_ns']) / 1e9
                write_json(directory / 'result.json', row)
                return row
            row['pid'] = process.pid
            write_json(directory / 'started.json', row)
            reader_state = {}
            reader = threading.Thread(target=consume_native,
                args=(process.stdout, out, events, reader_state, observer, role), daemon=True)
            reader.start()
            try:
                row['exit_code'] = process.wait(timeout=plan['timeout_seconds'])
            except subprocess.TimeoutExpired:
                row['timed_out'] = True
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                row['exit_code'] = process.returncode
            reader.join(timeout=10)
            row['stream_eof'] = reader_state.get('eof', False)
            row['stream_error_type'] = reader_state.get('error_type')
            row['stream_complete'] = (not reader.is_alive() and row['stream_eof']
                and row['stream_error_type'] is None)
        row.update(finished_at=utc(), end_monotonic_ns=time.monotonic_ns())
    row['relay_complete'] = True
    row['elapsed_seconds'] = (row['end_monotonic_ns'] - row['start_monotonic_ns']) / 1e9
    write_json(directory / 'result.json', row)
    return row


def usage_fields(value):
    """Only observed nonnegative integer counts; never coerce provider text."""
    if not isinstance(value, dict):
        return {}
    prompt_details = value.get('prompt_tokens_details')
    completion_details = value.get('completion_tokens_details')
    fields = {'input': value.get('prompt_tokens'), 'output': value.get('completion_tokens'),
        'cached_input': prompt_details.get('cached_tokens') if isinstance(prompt_details, dict) else None,
        'reasoning': value.get('reasoning_tokens', completion_details.get('reasoning_tokens')
            if isinstance(completion_details, dict) else None)}
    return {field: count for field, count in fields.items() if type(count) is int and count >= 0}


def usage(path):
    totals = {'input_tokens': 0, 'cached_input_tokens': 0, 'output_tokens': 0,
              'reasoning_tokens': None, 'requests': 0, 'usage_requests': 0, 'reasoning_observed': False}
    records = [json.loads(line) for line in Path(path).read_text().splitlines()] if Path(path).exists() else []
    requests = [r['request'] for r in records if r['event'] == 'request']
    identities = set(requests)
    values = {r['request']: r['usage'] for r in records if r['event'] == 'usage'}
    totals['requests'] = len(requests)
    totals['usage_requests'] = len(values)
    totals['reasoning_observed'] = any(r['event'] == 'reasoning_observed' for r in records)
    coverage = dict.fromkeys(('input', 'output', 'cached_input', 'reasoning'), 0)
    for identity, value in values.items():
        if identity not in identities or not isinstance(value, dict):
            continue
        for field, count in usage_fields(value).items():
            totals[field + '_tokens'] = (totals[field + '_tokens'] or 0) + count
            coverage[field] += 1
    exact_ids = bool(requests) and len(requests) == len(identities) and set(values) == identities
    for field, count in coverage.items():
        totals[field + '_usage_requests'] = count
        totals['complete_' + field + '_usage'] = exact_ids and count == len(requests)
    totals['complete_usage'] = totals['complete_input_usage'] and totals['complete_output_usage']
    return totals
