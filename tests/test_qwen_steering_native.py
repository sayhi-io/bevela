"""Real native CLI + scripted local provider; no model or benchmark inference."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest

from experiments import qwen_steering as route

SOURCE = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get('QWEN_STEERING_TEST_RUNTIME'), 'native runtime not explicitly supplied')
class NativeSteeringTests(unittest.TestCase):
    def test_native_context_delivery_and_source_change_notice(self):
        with tempfile.TemporaryDirectory() as temp:
            requests = []
            target = {}
            class Handler(BaseHTTPRequestHandler):
                def log_message(self, *args):
                    pass

                def do_GET(self):
                    raw = json.dumps({'object': 'list', 'data': [{'id': 'qwen38-27b-dflash2', 'object': 'model'}]}).encode()
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(raw)))
                    self.end_headers()
                    self.wfile.write(raw)

                def do_POST(self):
                    body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                    requests.append(body)
                    index = len(requests)
                    if index <= 2:
                        name = 'read_file' if index == 1 else 'write_file'
                        args = {'file_path': str(target['file'])}
                        if index == 2:
                            args['content'] = target['original'] + '\n# Native hook transport probe\n'
                        delta = {'role': 'assistant', 'content': None, 'tool_calls': [{
                            'index': 0, 'id': 'probe-call-' + str(index), 'type': 'function',
                            'function': {'name': name, 'arguments': json.dumps(args)}}]}
                        finish = 'tool_calls'
                    else:
                        delta = {'role': 'assistant', 'content': 'Scripted native transport probe complete.'}
                        finish = 'stop'
                    def chunk(delta, finish=None):
                        return {'id': 'probe-' + str(index), 'object': 'chat.completion.chunk',
                                'created': 0, 'model': body['model'],
                                'choices': [{'index': 0, 'delta': delta, 'finish_reason': finish}]}
                    frames = [chunk(delta), chunk({}, finish),
                              {'id': 'usage', 'choices': [], 'usage': {'prompt_tokens': 1, 'completion_tokens': 1,
                               'total_tokens': 2, 'completion_tokens_details': {'reasoning_tokens': 0}}}]
                    raw = (''.join('data: ' + json.dumps(frame) + '\n\n' for frame in frames) + 'data: [DONE]\n\n').encode()
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/event-stream')
                    self.send_header('Content-Length', str(len(raw)))
                    self.end_headers()
                    self.wfile.write(raw)

            server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                engine = route.runner(True, 1)
                root = engine.prepare(Path(temp) / 'trial', 'C', SOURCE,
                    Path(os.environ['QWEN_STEERING_TEST_RUNTIME']),
                    f'http://127.0.0.1:{server.server_port}/v1', 45)
                target['file'] = root / 'work/catalog.py'
                target['original'] = target['file'].read_text()
                plan = engine.verify(root, before=True)
                row = engine.adapter.record(root, 'producer', plan)
                self.assertEqual(row['exit_code'], 0, (root / 'producer/stderr.bin').read_text()[-2000:])
                self.assertEqual(len(requests), 3)
                self.assertTrue(any('PI update:' in json.dumps(r['messages']) for r in requests))
                journal = root / 'qwen-home/producer/pi-steering/events.jsonl'
                events = [json.loads(line) for line in journal.read_text().splitlines()]
                source_notice = next(e['message'] for e in events if e['message'] and
                                     '"source_changes": ["catalog.py"]' in e['message'])
                self.assertIn(source_notice, json.dumps(requests[-1]['messages'], ensure_ascii=False)
                              .replace('\\n', '\n').replace('\\"', '"'))
                self.assertIn('Native hook transport probe', target['file'].read_text())
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)


if __name__ == '__main__':
    unittest.main()
