"""Versioned self-organizing analysis; post-run only, no messages or model execution."""
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys


def jsonl(path):
    result = []
    for number, line in enumerate(Path(path).read_text(errors='replace').splitlines(), 1):
        try:
            result.append(json.loads(line))
        except ValueError:
            result.append({'parse_error_line': number})
    return result


def last_usage(native):
    samples = [r['payload']['info']['total_token_usage'] for r in native
               if r.get('type') == 'event_msg' and r.get('payload', {}).get('type') == 'token_count'
               and (r['payload'].get('info') or {}).get('total_token_usage')]
    return samples[-1] if samples else None


def native_calls(native, started_at):
    """Use paired native call timestamps, not buffered CLI event delivery gaps."""
    origin = datetime.fromisoformat(started_at).timestamp()
    pending = {}
    rows = []
    for event in native:
        payload = event.get('payload', {})
        if event.get('type') != 'response_item':
            continue
        kind = payload.get('type')
        call_id = payload.get('call_id')
        if kind in ('function_call', 'custom_tool_call'):
            text = str(payload.get('input', payload.get('arguments', '')))
            stamp = datetime.fromisoformat(event['timestamp']).timestamp()
            pending[call_id] = {'id': call_id, 'start_seconds': stamp - origin,
                'input': text, 'name': payload.get('name'),
                'pi_related': any(s in text for s in ('_worker_cli.py', '$PI', 'project-intent', '/.pi/'))}
        elif kind in ('function_call_output', 'custom_tool_call_output') and call_id in pending:
            row = pending.pop(call_id)
            row['end_seconds'] = datetime.fromisoformat(event['timestamp']).timestamp() - origin
            row['seconds'] = row['end_seconds'] - row['start_seconds']
            output = payload.get('output', '')
            row['output'] = '\n'.join(r.get('text', '') for r in output) if isinstance(output, list) else str(output)
            row['output_bytes'] = len(row['output'].encode())
            rows.append(row)
    return rows


def worker(root, row, window):
    role = row['role']
    events = jsonl(root / role / 'events.jsonl')
    stream = [r.get('event', {}) for r in events]
    sessions = [r.get('thread_id') for r in stream if r.get('type') == 'thread.started']
    native = []
    native_path = None
    if len(sessions) == 1 and re.fullmatch(r'[0-9a-f-]{36}', sessions[0]):
        matches = [root / ('native-' + role + '.jsonl')] if (root / ('native-' + role + '.jsonl')).exists() else []
        if len(matches) == 1:
            native_path = matches[0]
            native = jsonl(native_path)
    contexts = sorted({(r['payload'].get('model'), r['payload'].get('effort'))
                       for r in native if r.get('type') == 'turn_context'})
    commands = []
    starts = {}
    edits = []
    for event in events:
        body = event.get('event', {})
        item = body.get('item', {})
        stamp = (event['mono_ns'] - window['start_ns']) / 1e9
        if body.get('type') == 'item.started':
            starts[item.get('id')] = stamp
        if body.get('type') != 'item.completed':
            continue
        if item.get('type') == 'file_change':
            edits.append({'seconds': stamp, 'status': item.get('status'), 'changes': item.get('changes', [])})
        if item.get('type') != 'command_execution':
            continue
        command = item.get('command', '')
        pi_related = any(s in command for s in ('_worker_cli.py', '$PI', 'project-intent', '/.pi/'))
        operations = sorted(set(re.findall(r'\b(onboard|discover|enroll|start|repair-status|repair-claim|repair-ack|repair-complete|repair-release|report-status|report|docs)\b', command))) if pi_related else []
        commands.append({'id': item.get('id'), 'start_seconds': starts.get(item.get('id')),
            'end_seconds': stamp, 'seconds': stamp - starts[item['id']] if item.get('id') in starts else None,
            'command': command, 'exit_code': item.get('exit_code'), 'pi_related': pi_related,
            'pi_operation_candidates': operations,
            'output_bytes': len(item.get('aggregated_output', '').encode()),
            'output': item.get('aggregated_output', '')})
    usage = last_usage(native)
    calls_with_time = native_calls(native, row['started_at'])
    pi_calls = [c for c in calls_with_time if c['pi_related']]
    enrolled_calls = [c for c in pi_calls if re.search(r'\benroll\b', c['input'])
                      and '--inactive' not in c['input']
                      and re.search(r'"status"\s*:\s*"active"', c['output'])]
    enrollment = min((c['end_seconds'] for c in enrolled_calls), default=None)
    cli_usage = [r.get('usage') for r in stream if r.get('type') == 'turn.completed']
    suspicious = []
    for command in commands:
        if any(s in command['command'] for s in ('check_contract.py', 'seven_seams_check.py', '/evaluations/', '/.codex/sessions/', '/reference/')):
            suspicious.append(command['command'])
    texts = [str(r.get('payload', {}).get('input', r.get('payload', {}).get('arguments', '')))
             for r in native if r.get('type') == 'response_item'
             and r.get('payload', {}).get('type') in ('function_call', 'custom_tool_call')]
    patch_calls = []
    calls = {}
    for event in native:
        payload = event.get('payload', {})
        if event.get('type') != 'response_item':
            continue
        if payload.get('type') in ('function_call', 'custom_tool_call'):
            text = str(payload.get('input', payload.get('arguments', '')))
            if 'apply_patch' in text or payload.get('name') == 'apply_patch':
                calls[payload.get('call_id')] = len(patch_calls)
                patch_calls.append({'at': event.get('timestamp'), 'call_id': payload.get('call_id'),
                                    'input': text, 'output': None})
        elif payload.get('call_id') in calls:
            patch_calls[calls[payload['call_id']]]['output'] = payload.get('output')
    return {'role': role, 'sessions': sessions, 'native_contexts': contexts,
        'native_log': str(native_path) if native_path else None,
        'native_sha256': hashlib.sha256(native_path.read_bytes()).hexdigest() if native_path else None,
        'tokens': usage, 'cli_usage': cli_usage,
        'duration_seconds': row['elapsed_seconds'], 'exit_code': row.get('exit_code'),
        'start_seconds': (row['start_monotonic_ns'] - window['start_ns']) / 1e9,
        'end_seconds': (row['end_monotonic_ns'] - window['start_ns']) / 1e9,
        'commands': commands, 'edits': edits, 'patch_calls': patch_calls, 'evidence_access_flags': suspicious,
        'native_tool_calls': calls_with_time,
        'native_tool_call_count': len(calls_with_time),
        'agent_messages': [e['event']['item'].get('text', '') for e in events if e.get('event', {}).get('item', {}).get('type') == 'agent_message'],
        'delegation_flags': [text for text in texts if re.search(r'spawn_agent|codex exec|session-continue', text)],
        'pi_command_candidates': sum(c['pi_related'] for c in commands),
        'pi_native_tool_seconds': sum(c['seconds'] for c in pi_calls),
        'pi_native_calls': pi_calls,
        'enrollment_completed_seconds': enrollment,
        'onboarding_observed_span_seconds': enrollment - min(c['start_seconds'] for c in pi_calls) if enrollment is not None else None,
        'pi_buffered_delivery_span_seconds': sum(c['seconds'] or 0 for c in commands if c['pi_related']),
        'pi_output_bytes': sum(c['output_bytes'] for c in commands if c['pi_related']),
        'pi_failed_commands': sum(c['exit_code'] not in (None, 0) for c in commands if c['pi_related']),
        'pi_operation_candidate_counts': dict(Counter(op for c in commands for op in c['pi_operation_candidates'])),
        'pi_attribution_note': 'Native paired tool timestamps measure wrapped-call wall time; mixed calls include non-PI work. '
            'CLI item start/end events can be buffered and are NOT execution durations. '
            'Onboarding span includes intervening reasoning/discovery. Exact PI token attribution unavailable. '
            'Cached input/reasoning are subsets, not extra tokens.'}


def analyze(batch):
    batch = Path(batch)
    data = json.loads((batch / 'results.json').read_text())
    rows = []
    for trial in data['trials']:
        root = batch / (trial['condition'] + str(trial['repetition']))
        result = trial['result']
        workers = [worker(root, r, result['concurrency']) for r in result['workers']]
        totals = None
        if all(w['tokens'] is not None for w in workers):
            fields = set().union(*(w['tokens'].keys() for w in workers))
            totals = {field: sum(w['tokens'].get(field, 0) for w in workers) for field in fields}
        row = {'condition': trial['condition'], 'repetition': trial['repetition'], 'root': str(root),
            'score': result['result'].get('score'), 'accepted': result['accepted'],
            'producer_seams': sum(r['producer']['passed'] for r in result['result'].get('problems', {}).values()),
            'consumer_seams': sum(r['consumer']['passed'] for r in result['result'].get('problems', {}).values()),
            'failed_seams': [k for k, v in result['result'].get('problems', {}).items() if not v['both_preserved']],
            'project_seconds': result['project_seconds'], 'setup_seconds': result['setup_seconds'],
            'verification_seconds': result['verification_seconds'], 'archive_seconds': result['archive_seconds'],
            'concurrency': result['concurrency'], 'tokens': totals, 'workers': workers}
        rows.append(row)
    output = batch / 'analysis.json'
    with output.open('x') as stream:
        json.dump(rows, stream, indent=2)
    return output


if __name__ == '__main__':
    print(analyze(sys.argv[1]))
