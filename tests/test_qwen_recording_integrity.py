"""Future-recorder regressions; historical study v1 remains byte-frozen."""
import io
import json
from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch

from experiments import qwen_code_adapter as adapter


class RecordingIntegrityTests(unittest.TestCase):
    def test_handler_error_prevents_success_receipt_even_when_process_exits_zero(self):
        # A synthetic local Python client, not Qwen or a model process. Its
        # malformed request fails before any upstream connection is attempted.
        with tempfile.TemporaryDirectory(prefix='qwen-record-fence-') as temporary:
            root = Path(temporary)
            profile = root / 'qwen-home/catalog'
            profile.mkdir(parents=True)
            (root / 'catalog.txt').write_text('synthetic fixture')
            script = '''
import http.client, json, sys
from urllib.request import Request, urlopen
settings = json.load(open(sys.argv[1]))
endpoint = settings['modelProviders']['openai'][0]['baseUrl']
try:
    urlopen(Request(endpoint + '/chat/completions', data=b'[]'), timeout=5)
except http.client.RemoteDisconnected:
    pass
print('{"type":"result","subtype":"success"}')
'''
            command = [sys.executable, '-I', '-c', script, str(profile / 'settings.json')]
            plan = {'sessions': {'catalog': 'synthetic-session'}, 'endpoint': 'http://127.0.0.1:1/v1',
                'model': 'synthetic', 'context_window': 230000, 'server_effort': 'xhigh',
                'pi_enabled': False, 'timeout_seconds': 5}
            popen = adapter.subprocess.Popen

            def synthetic_process(*args, **kwargs):
                process = popen(*args, **kwargs)
                self.addCleanup(process.stdout.close)
                return process

            with patch.object(adapter, 'argv', return_value=command), \
                    patch.object(adapter, 'sandbox', return_value=command), \
                    patch.object(adapter.subprocess, 'Popen', side_effect=synthetic_process):
                with self.assertRaisesRegex(RuntimeError, 'refusing to finalize'):
                    adapter.record(root, 'catalog', plan)
            self.assertIn('success', (root / 'catalog/stdout.jsonl').read_text())
            self.assertFalse((root / 'catalog/result.json').exists())
            errors = [json.loads(line) for line in (root / 'catalog/transport.jsonl').read_text().splitlines()]
            self.assertEqual(errors[0]['event'], 'handler_error')
            self.assertEqual(errors[0]['type'], 'AttributeError')

    def measured(self, rows):
        with tempfile.TemporaryDirectory(prefix='qwen-usage-integrity-') as temporary:
            path = Path(temporary) / 'transport.jsonl'
            path.write_text('\n'.join(map(json.dumps, rows)))
            return adapter.usage(path)

    def test_usage_record_without_required_fields_is_not_complete(self):
        value = self.measured([{'event': 'request', 'request': 1},
            {'event': 'usage', 'request': 1, 'usage': {'total_tokens': 123}}])
        self.assertFalse(value['complete_usage'])
        self.assertFalse(value['complete_reasoning_usage'])

    def test_same_count_wrong_request_coverage_is_not_complete(self):
        value = self.measured([{'event': 'request', 'request': 1},
            {'event': 'usage', 'request': 2, 'usage': {'prompt_tokens': 100, 'completion_tokens': 20}}])
        self.assertFalse(value['complete_usage'])
        self.assertEqual(value['input_tokens'], 0)

    def test_invalid_counts_and_partial_reasoning_are_explicit(self):
        value = self.measured([{'event': 'request', 'request': 1},
            {'event': 'request', 'request': 2},
            {'event': 'usage', 'request': 1, 'usage': {'prompt_tokens': 100,
                'completion_tokens': 20, 'reasoning_tokens': 10}},
            {'event': 'usage', 'request': 2, 'usage': {'prompt_tokens': 50, 'completion_tokens': 5}}])
        self.assertTrue(value['complete_usage'])
        self.assertEqual(value['reasoning_tokens'], 10)
        self.assertFalse(value['complete_reasoning_usage'])
        for invalid in (-1, True, '100', 2.5):
            bad = self.measured([{'event': 'request', 'request': 1},
                {'event': 'usage', 'request': 1, 'usage': {'prompt_tokens': invalid, 'completion_tokens': 20}}])
            self.assertFalse(bad['complete_usage'])

    def test_native_reader_requires_eof_not_just_thread_exit(self):
        state = {}
        output, events = io.BytesIO(), io.StringIO()
        adapter.consume_native(io.BytesIO(b'{"type":"result"}\n'), output, events, state)
        self.assertTrue(state['eof'])
        self.assertIsNone(state['error_type'])
        self.assertEqual(output.getvalue(), b'{"type":"result"}\n')

        class BrokenOutput(io.BytesIO):
            def write(self, value):
                raise OSError('simulated evidence disk failure')

        state = {}
        adapter.consume_native(io.BytesIO(b'{"type":"result"}\n'), BrokenOutput(), io.StringIO(), state)
        self.assertFalse(state['eof'])
        self.assertEqual(state['error_type'], 'OSError')


if __name__ == '__main__':
    unittest.main()
