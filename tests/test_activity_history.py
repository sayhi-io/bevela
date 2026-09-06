from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from project_intent.activity import TAIL_BYTES
from project_intent.activity_history import ActivityHistory, MAX_SERIES
from project_intent.enrollment import registration
from project_intent.model import project
from project_intent.runtime import Store, write_json

ROOT = Path(__file__).resolve().parents[1]


class HistoryTests(unittest.TestCase):
    def metric(self, points, status='recent'):
        return {'session': 'worker', 'status': status, 'points': points,
                'last_report_at': points[-1]['at'] if points else None}

    def test_tail_predecessor_loss_does_not_erase_numeric_observation(self):
        history = ActivityHistory()
        history.observe('one', self.metric([{'at': 900, 'value': 7}]), 950, 'epoch')
        result = history.observe('one', self.metric([{'at': 900, 'value': None}, {'at': 950, 'value': 4}]), 950, 'epoch')
        self.assertEqual([p['value'] for p in result['points']], [7, 4])
        unavailable = history.observe('one', self.metric([], 'unavailable'), 960, 'epoch')
        self.assertEqual(unavailable['status'], 'unavailable')
        self.assertEqual(unavailable['points'], result['points'])

    def test_bounds_epochs_and_concurrent_updates(self):
        history = ActivityHistory()
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(lambda at: history.observe('one', self.metric([{'at': at, 'value': 1}]), 1000, 'first'), range(701, 1001)))
        result = history.observe('one', self.metric([{'at': 1001, 'value': 2}]), 1001, 'second')
        self.assertEqual(len(result['points']), 180)
        self.assertTrue(result['points'][-1]['break_before'])
        self.assertNotIn('_epoch', json.dumps(result))
        self.assertEqual(history.observe('one', self.metric([], 'inactive'), 1902)['points'], [])
        for index in range(MAX_SERIES + 3):
            history.observe(index, self.metric([{'at': 2000, 'value': 1}]), 2000)
        self.assertEqual(len(history._series), MAX_SERIES)
        history.prune(2901)
        self.assertEqual(history._series, {})

    def test_older_read_cannot_destroy_newer_cached_points(self):
        history = ActivityHistory()
        history.observe('one', self.metric([{'at': 1000, 'value': 1}]), 1000)
        old = history.observe('one', self.metric([{'at': 990, 'value': 2}]), 990)
        self.assertEqual([p['at'] for p in old['points']], [990])
        self.assertEqual([p['at'] for p in history.observe('one', self.metric([]), 1001)['points']], [990, 1000])


class StoreHistoryTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.logs = self.root / 'logs'; self.logs.mkdir()
        self.enrolled = self.root / 'enrolled'; self.enrolled.mkdir()
        self.log = self.logs / 'worker.jsonl'
        self.log.write_text(json.dumps({'type': 'session_meta', 'payload': {'id': 'worker'}}) + '\n')
        self.snapshot = json.loads((ROOT / '.project-intent/snapshot.json').read_text())
        self.scope = self.snapshot['scope_id']
        self.now = datetime(2026, 9, 5, tzinfo=timezone.utc)
        self.record = registration(self.snapshot, 'PI-MISSION-01', 'worker', 'history fix', [], [], str(self.log), now=self.now)
        self.record['checkout'] = {'host': 'test', 'root': '/checkout', 'repository_common_dir': '/repo/.git', 'branch': 'agent/history', 'head': None, 'observed_at': self.now.isoformat()}
        self.save()
        write_json(self.root / 'snapshot.json', self.snapshot)
        self.source = {'directory': str(self.enrolled), 'telemetry_roots': [str(self.logs)]}
        self.config = {'scopes': [{'id': self.scope, 'label': 'test', 'cache': str(self.root / 'snapshot.json'), 'enrollment_sources': [self.source]}]}
        self.store = Store(self.config)

    def save(self):
        write_json(self.enrolled / 'worker.json', self.record)

    def event(self, seconds, count):
        event = {'timestamp': (self.now + timedelta(seconds=seconds)).isoformat(),
                 'payload': {'type': 'token_count', 'info': {'total_token_usage': {'output_tokens': count}}}}
        with self.log.open('a') as stream:
            stream.write(json.dumps(event) + '\n')

    def activity(self, seconds):
        return self.store.view(self.now + timedelta(seconds=seconds))[0]['activity']['PI-MISSION-01']

    def seed(self):
        self.event(1, 0); self.event(11, 100)
        return self.activity(12)

    def test_tail_rollover_stale_resume_and_unavailable(self):
        initial = self.seed()
        self.assertEqual(initial['points'][-1]['value'], 10)
        self.assertEqual(self.activity(150)['status'], 'stale')
        # Log text, not additional usage, pushes prior reports outside the parser tail.
        with self.log.open('a') as stream:
            stream.write(json.dumps({'padding': 'x' * TAIL_BYTES}) + '\n')
        self.assertEqual(self.activity(160)['points'], initial['points'])
        self.event(170, 200); self.event(180, 300)
        resumed = self.activity(181)
        self.assertEqual([p['value'] for p in resumed['points']], [None, 10, None, 10])
        self.assertEqual(resumed['status'], 'recent')
        self.log.unlink()
        unavailable = self.activity(182)
        self.assertEqual(unavailable['status'], 'unavailable')
        self.assertEqual(unavailable['points'], resumed['points'])
        self.assertEqual(self.activity(1100)['points'], [])

    def test_release_resume_keeps_history_without_gap_attribution(self):
        self.seed()
        checkout = self.record['checkout']
        self.record = registration(self.snapshot, 'PI-MISSION-01', 'worker', '', [], [], old=self.record, inactive=True, now=self.now + timedelta(seconds=12))
        self.record['checkout'] = checkout
        self.save()
        with patch('project_intent.activity.Path.open', side_effect=AssertionError('inactive log read')):
            self.assertEqual(self.activity(13)['status'], 'inactive')
        self.event(15, 1000)  # Not assigned: never enters resumed history.
        self.record = registration(self.snapshot, 'PI-MISSION-01', 'worker', '', [], [], old=self.record, now=self.now + timedelta(seconds=20))
        self.record['checkout'] = checkout
        self.save(); self.event(21, 1100); self.event(31, 1200)
        resumed = self.activity(32)
        self.assertEqual([p['value'] for p in resumed['points']], [None, 10, None, 10])
        self.assertTrue(resumed['points'][2]['break_before'])
        self.assertNotIn((self.now + timedelta(seconds=15)).timestamp(), [p['at'] for p in resumed['points']])

    def test_expiry_preserves_only_observed_history_and_new_checkout_is_separate(self):
        self.seed()
        self.record['expires_at'] = (self.now + timedelta(seconds=20)).isoformat(); self.save()
        with patch('project_intent.activity.Path.open', side_effect=AssertionError('expired log read')):
            self.assertEqual(self.activity(21)['status'], 'expired')
        self.record['checkout']['root'] = '/different'; self.save()
        self.assertEqual(self.activity(22)['points'], [])

    def test_malformed_telemetry_never_crashes_or_recovers_history(self):
        self.seed()
        for telemetry in (['bad'], {'path': [], 'kind': 'codex-local-usage', 'since': self.record['claimed_at']}):
            self.record['telemetry'] = telemetry; self.save()
            result = self.activity(13)
            self.assertEqual(result['status'], 'unavailable')
            self.assertEqual(result['points'], [])

    def test_duplicate_scope_and_session_boundaries(self):
        self.seed()
        self.config['scopes'][0]['enrollment_sources'].append(self.source)
        duplicate = self.activity(13)
        self.assertEqual(duplicate, {'status': 'ambiguous-binding', 'points': []})
        self.config['scopes'][0]['enrollment_sources'].pop()
        state = self.store.view(self.now + timedelta(seconds=14))[0]
        self.assertEqual(project([state], ['unrelated'])['workstreams'], [])
        other = copy.deepcopy(self.record); other['session'] = 'second'
        second = self.logs / 'second.jsonl'; second.write_text(json.dumps({'type': 'session_meta', 'payload': {'id': 'second'}}) + '\n')
        other['telemetry']['path'] = str(second); write_json(self.enrolled / 'second.json', other)
        metrics = self.activity(15)['sessions']
        self.assertEqual(metrics[0]['session'], 'second')
        self.assertEqual(metrics[0]['points'], [])
        self.assertEqual(metrics[1]['points'][-1]['value'], 10)
