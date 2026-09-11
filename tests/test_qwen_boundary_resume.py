import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments import qwen_boundary_resume as resume


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='qwen-boundary-unit-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / 'a').mkdir()
        self.plan = {'model': 'q', 'timeout_seconds': 10, 'sessions': {'a': 's'}}
        self.result = {'native_identity_verified': False, 'infrastructure_errors': [],
            'workers': [{'role': 'a', 'session': 's', 'timed_out': True, 'stream_complete': True,
                'stream_eof': True, 'stream_error_type': None, 'relay_complete': True,
                'exit_code': -15, 'elapsed_seconds': 10.1, 'start_monotonic_ns': 0, 'end_monotonic_ns': 10100000000}]}
        self.telemetry = [{'role': 'a', 'session': 's', 'native_identity_verified': False,
            'native_initialization': [{'model': 'q', 'session_id': 's'}], 'native_final': []}]
        self.transport = [{'event': 'request', 'request': 1, 'model': 'q', 'reasoning_effort': 'xhigh',
            'chat_template_kwargs': {'enable_thinking': True}},
            {'event': 'response', 'request': 1, 'status': 200, 'mono_ns': 1000000000},
            {'event': 'transport_error', 'request': 1, 'type': 'ConnectionResetError', 'mono_ns': 10100000000}]

    def evaluate(self):
        for name, value in [('plan.json', self.plan), ('result.json', self.result), ('worker-analysis.json', self.telemetry)]:
            (self.root / name).write_text(json.dumps(value))
        (self.root / 'a/transport.jsonl').write_text('\n'.join(map(json.dumps, self.transport)))
        with patch.object(resume.study, 'verify', return_value=self.plan):
            return resume.disposition(self.root)

    def test_budget_timeout_retained_not_success(self):
        value = self.evaluate()
        self.assertEqual(value['state'], 'reviewed_predetermined_timeout')
        self.assertEqual(json.loads((self.root / 'result.json').read_text()), self.result)
        self.assertFalse(self.result['native_identity_verified'])
        self.assertEqual(self.evaluate(), value)

    def test_early_reset_not_budget_cancellation(self):
        self.transport[-1]['mono_ns'] = 9000000000
        with self.assertRaisesRegex(AssertionError, 'Non-boundary'):
            self.evaluate()

    def test_chunk_truncation_only_at_verified_budget(self):
        self.transport[-1]['type'] = 'IncompleteRead'
        self.transport[-1]['mono_ns'] = 9000000000
        with self.assertRaisesRegex(AssertionError, 'Non-boundary'):
            self.evaluate()
        self.transport[-1]['mono_ns'] = 10100000000
        self.assertEqual(self.evaluate()['state'], 'reviewed_predetermined_timeout')

    def test_http_failure_not_waived(self):
        self.transport.append({'event': 'response', 'status': 503})
        with self.assertRaisesRegex(AssertionError, 'HTTP failure'):
            self.evaluate()

    def test_generic_oserror_and_unanswered_request_refused(self):
        self.transport[-1]['type'] = 'OSError'
        with self.assertRaisesRegex(AssertionError, 'Non-boundary'):
            self.evaluate()
        self.transport[-1]['type'] = 'ConnectionResetError'
        self.transport.pop(1)
        with self.assertRaisesRegex(AssertionError, 'Non-boundary'):
            self.evaluate()

    def test_wrong_model_or_session_refused(self):
        self.transport[0]['model'] = 'wrong'
        with self.assertRaisesRegex(AssertionError, 'Wrong request'):
            self.evaluate()
        self.transport[0]['model'] = 'q'
        self.telemetry[0]['native_initialization'][0]['session_id'] = 'wrong'
        with self.assertRaisesRegex(AssertionError, 'Wrong native'):
            self.evaluate()

    def test_other_signal_refused(self):
        self.result['workers'][0]['exit_code'] = -11
        with self.assertRaisesRegex(AssertionError, 'termination'):
            self.evaluate()

    def test_reader_failure_and_incomplete_cleanup_are_fenced(self):
        for field in ('stream_complete', 'stream_eof', 'relay_complete'):
            self.result['workers'][0][field] = False
            with self.assertRaisesRegex(AssertionError, 'Incomplete native recording'):
                self.evaluate()
            self.result['workers'][0][field] = True
        self.result['workers'][0]['stream_error_type'] = 'OSError'
        with self.assertRaisesRegex(AssertionError, 'Incomplete native recording'):
            self.evaluate()

    def test_correlated_native_cancellation_does_not_waive_other_error(self):
        self.transport[-1].update(mono_ns=9000000000, at='early', type='BrokenPipeError')
        correlated = {'matches': [{'request': 1, 'transport_error_at': 'early',
            'transport_error_type': 'BrokenPipeError'}], 'profile_sha256': 'a' * 64}
        with patch.object(resume.cancellation, 'inspect', return_value=correlated):
            value = self.evaluate()
            self.assertEqual(value['state'], 'reviewed_native_stream_cancellation')
            self.assertEqual(json.loads((self.root / 'result.json').read_text()), self.result)
            self.transport.append({'event': 'transport_error', 'request': 1, 'at': 'other',
                'mono_ns': 9000000000, 'type': 'OSError'})
            with self.assertRaisesRegex(AssertionError, 'Non-boundary'):
                self.evaluate()


if __name__ == '__main__':
    unittest.main()
