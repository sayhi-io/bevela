from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.qwen_native_cancellation import inspect, match


class NativeCancellationTests(unittest.TestCase):
    def setUp(self):
        def at(seconds):
            return datetime.fromtimestamp(seconds, timezone.utc).isoformat()
        self.error = {'event': 'transport_error', 'request': 1,
            'type': 'BrokenPipeError', 'at': at(902.2)}
        self.transport = [{'event': 'request', 'request': 1, 'at': at(0)},
            {'event': 'response', 'request': 1, 'status': 200, 'at': at(1)},
            {'event': 'reasoning_observed', 'request': 1, 'at': at(901.9)},
            self.error, {'event': 'request', 'request': 2, 'at': at(902.7)},
            {'event': 'response', 'request': 2, 'status': 200, 'at': at(903)}]
        self.telemetry = [{'sessionId': 'session', 'type': 'system', 'subtype': 'ui_telemetry', 'systemPayload': {'uiEvent': {
            'event.name': 'qwen-code.api_error', 'error_type': 'StreamLifetimeExceededError',
            'model': 'qwen', 'prompt_id': 'session########0', 'event.timestamp': at(902),
            'duration_ms': 902000,
            'error_message': 'Stream exceeded its 900000ms upstream-wait cap after 8303 chunks without completing'}}}]
        self.events = [{'at': at(902.05), 'event': {
            'type': 'system', 'subtype': 'retry', 'session_id': 'session'}}]

    def classify(self, **updates):
        values = dict(error=self.error, transport=self.transport, telemetry=self.telemetry,
            events=self.events, session='session', model='qwen')
        values.update(updates)
        return match(**values)

    def test_requires_same_native_session_model_and_corroborated_retry(self):
        self.assertEqual(self.classify()['request'], 1)
        self.assertIsNone(self.classify(session='other'))
        self.assertIsNone(self.classify(model='other'))
        self.assertIsNone(self.classify(events=[]))

    def test_unrelated_error_or_incomplete_recovery_is_not_waived(self):
        self.assertIsNone(self.classify(error={**self.error, 'type': 'OSError'}))
        self.assertIsNone(self.classify(transport=self.transport[:-1]))
        self.assertIsNone(self.classify(transport=[r for r in self.transport if r['event'] != 'reasoning_observed']))

    def test_other_native_error_or_cap_is_not_waived(self):
        for key, value in [('error_type', 'StreamInactivityTimeoutError'),
                ('error_message', 'Stream exceeded its 1000ms upstream-wait cap after 1 chunks'),
                ('duration_ms', 300000), ('event.timestamp', '1970-01-01T00:00:01+00:00')]:
            changed = deepcopy(self.telemetry)
            changed[0]['systemPayload']['uiEvent'][key] = value
            self.assertIsNone(self.classify(telemetry=changed))

    def test_ambiguous_duplicate_native_records_are_not_waived(self):
        self.assertIsNone(self.classify(telemetry=self.telemetry * 2))

    def test_overlapping_streams_or_multiple_retries_are_ambiguous(self):
        other = {'event': 'request', 'request': 0, 'at': '1969-12-31T23:59:59+00:00'}
        self.assertIsNone(self.classify(transport=[other] + self.transport))
        self.assertIsNone(self.classify(events=self.events * 2))
        self.assertIsNone(self.classify(transport=self.transport + [self.transport[-2]]))

    def test_outer_native_envelope_must_match(self):
        for key in ('sessionId', 'type', 'subtype'):
            changed = deepcopy(self.telemetry)
            changed[0][key] = 'wrong'
            self.assertIsNone(self.classify(telemetry=changed))

    def test_complete_classification_cannot_reuse_one_native_error(self):
        with tempfile.TemporaryDirectory(prefix='qwen-cancellation-uniqueness-') as temporary:
            root = Path(temporary)
            profile = root / 'qwen-home/catalog/projects/work/chats/session.jsonl'
            profile.parent.mkdir(parents=True)
            profile.write_text('')
            (root / 'catalog').mkdir()
            (root / 'catalog/events.jsonl').write_text('')
            matches = [{'request': i, 'native_error_at': 'same', 'native_retry_at': 'same',
                'followup_request': i + 1} for i in (1, 2)]
            with patch('experiments.qwen_native_cancellation.match', side_effect=matches):
                observed = inspect(root, 'catalog', 'session', 'qwen', [self.error, self.error])
            self.assertEqual(observed['matches'], [])


if __name__ == '__main__':
    unittest.main()
