import copy
from datetime import timedelta
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest

from project_intent.enrollment import registration
from project_intent.model import utcnow
from project_intent.worker_context import checkout_identity, integration_context, nearby_workers


ROOT = Path(__file__).resolve().parents[1]


class IntegrationContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.checkout = self.root / 'work'
        self.checkout.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.checkout)], check=True)
        self.identity = checkout_identity(self.checkout)
        self.scope = 'test/contracts'
        self.records = [dict(kind='workstream', id=key, revision='1', state='active',
                             statement=statement, scope=statement, acceptance=[statement],
                             boundaries=['contract/contact'], readiness={})
                        for key, statement in [('PRODUCER', 'Move display names into contact records'),
                                               ('CONSUMER', 'Render contact labels from current data')]]
        self.snapshot = dict(version=1, scope_id=self.scope, mission='Shared contracts',
                             source={'authoritative': False, 'captured_at': utcnow().isoformat()},
                             records=self.records)
        self.state = dict(id=self.scope, snapshot=self.snapshot, presence=[], execution={'status': 'observed'})
        self.snapshot_path = self.root / 'snapshot.json'
        self.snapshot_path.write_text(json.dumps(self.snapshot))
        self.leases = self.root / 'leases'
        self.config = self.root / 'worker config.json'
        self.config.write_text(json.dumps({'scopes': {self.scope: {
            'snapshot': str(self.snapshot_path), 'enrollment_directory': str(self.leases)},
            'other/scope': {'snapshot': str(self.root / 'unreadable.json'),
                            'enrollment_directory': str(self.root / 'other-leases')}}}))

    def cli(self, *args):
        result = subprocess.run([sys.executable, '-I', str(ROOT / 'project_intent/_worker_cli.py'), *args],
                                cwd=self.checkout, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def common(self):
        return ['--worker-config', str(self.config), '--scope', self.scope, '--checkout', str(self.checkout)]

    def worker(self, **overrides):
        record = registration(self.snapshot, 'PRODUCER', 'producer-session',
                              'Names now live in contact.display_name; label import still needs checking', [], [])
        record.update(checkout=self.identity, access='edit', touching_paths=['contacts.py'],
                      touching_seams=['contract/contact'], avoid_paths=[])
        record.update(overrides)
        self.state['presence'].append(record)
        return record

    def context(self):
        return integration_context(self.state, self.records[1], self.identity, ['labels.py'], session='consumer-session')

    def test_peer_intent_visible_without_any_enrollment(self):
        out = self.context()
        self.assertEqual([r['id'] for r in out['related_work']], ['PRODUCER'])
        self.assertEqual(out['related_work'][0]['acceptance'], self.records[0]['acceptance'])
        self.assertEqual(out['last_known_workers'], [])
        self.assertIn('not detected changes', out['meaning'])

    def test_unrelated_tasks_and_wrong_scope_workers_are_not_included(self):
        unrelated = copy.deepcopy(self.records[0])
        unrelated.update(id='UNRELATED', boundaries=['different/seam'])
        self.records.append(unrelated)
        self.worker(scope='other/scope')
        self.assertEqual([r['id'] for r in self.context()['related_work']], ['PRODUCER'])
        self.assertEqual(self.context()['last_known_workers'], [])

    def test_working_summary_survives_release_and_expiry_without_claiming_live_work(self):
        worker = self.worker()
        self.assertEqual(nearby_workers([self.state], self.identity, [], ['contract/contact'], self.scope)[0]['working'], worker['working'])
        for status, expiry, expected in [('inactive', utcnow()+timedelta(hours=1), 'released'),
                                         ('active', utcnow()-timedelta(seconds=1), 'expired')]:
            worker.update(status=status, expires_at=expiry.isoformat())
            observed, = self.context()['last_known_workers']
            self.assertEqual(observed['working'], worker['working'])
            self.assertEqual(observed['observation'], expected)
            self.assertEqual(nearby_workers([self.state], self.identity, [], ['contract/contact'], self.scope), [])

    def test_own_session_excluded_other_checkout_not_presented_as_local(self):
        self.worker(session='consumer-session')
        other = self.worker(session='other-session', checkout=dict(self.identity, root='/different/worktree'))
        observed, = self.context()['last_known_workers']
        self.assertEqual(observed['session'], other['session'])
        self.assertFalse(observed['same_checkout'])

    def test_future_observation_and_missing_coverage_stay_explicit(self):
        self.worker(heartbeat_at=(utcnow()+timedelta(minutes=1)).isoformat())
        self.state.pop('execution')
        out = self.context()
        self.assertEqual(out['presence_coverage'], 'unavailable')
        self.assertEqual(out['last_known_workers'][0]['observation'], 'future-timestamp')

    def test_onboard_refresh_is_read_only_scoped_and_bound_to_same_checkout(self):
        out = self.cli('onboard', *self.common(), '--workstream', 'CONSUMER')
        context = out['orientation']['integration_context']
        argv = context['refresh']['argv']
        self.assertEqual(shlex.split(context['refresh']['command']), argv)
        for flag, value in [('--worker-config', str(self.config)), ('--scope', self.scope),
                            ('--checkout', str(self.checkout)), ('--workstream', 'CONSUMER')]:
            self.assertEqual(argv[argv.index(flag)+1], value)
        result = subprocess.run(argv, cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['integration_context']['related_work'][0]['id'], 'PRODUCER')
        self.assertFalse(self.leases.exists())
        self.assertFalse((self.root / 'other-leases').exists())

    def test_refresh_keeps_direct_snapshot_mode(self):
        self.cli('enroll', '--snapshot', str(self.snapshot_path), '--directory', str(self.leases),
                 '--workstream', 'PRODUCER', '--session', 'producer-session',
                 '--access', 'edit', '--touching-path', 'contacts.py', '--working', 'Migrate names')
        self.cli('enroll', '--snapshot', str(self.snapshot_path), '--directory', str(self.leases),
                 '--workstream', 'PRODUCER', '--session', 'producer-session',
                 '--inactive', '--working', 'Names now in contact records')
        out = self.cli('start', '--snapshot', str(self.snapshot_path), '--directory', str(self.leases),
                       '--workstream', 'CONSUMER', '--checkout', str(self.checkout))
        argv = out['integration_context']['refresh']['argv']
        self.assertEqual(argv[argv.index('--snapshot')+1], str(self.snapshot_path))
        self.assertEqual(argv[argv.index('--directory')+1], str(self.leases))
        result = subprocess.run(argv, cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        observed, = json.loads(result.stdout)['integration_context']['last_known_workers']
        self.assertEqual(observed['working'], 'Names now in contact records')
        self.assertEqual(observed['observation'], 'released')

    def test_refresh_pins_implicit_checkout_and_relative_config(self):
        out = self.cli('onboard', '--worker-config', '../worker config.json',
                       '--scope', self.scope, '--workstream', 'CONSUMER')
        argv = out['orientation']['integration_context']['refresh']['argv']
        self.assertEqual(argv[argv.index('--checkout')+1], str(self.checkout))
        self.assertEqual(argv[argv.index('--worker-config')+1], str(self.config))
        result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['checkout']['root'], str(self.checkout))

    def test_refresh_after_peer_release_returns_actual_summary(self):
        consumer = self.cli('enroll', *self.common(), '--workstream', 'CONSUMER', '--session', 'consumer-session',
                            '--access', 'edit', '--touching-path', 'labels.py', '--working', 'Render labels')
        self.assertEqual(consumer['integration_context']['related_work'][0]['id'], 'PRODUCER')
        self.cli('enroll', *self.common(), '--workstream', 'PRODUCER', '--session', 'producer-session',
                 '--access', 'edit', '--touching-path', 'contacts.py', '--working', 'Migrate contact names')
        self.cli('enroll', *self.common(), '--workstream', 'PRODUCER', '--session', 'producer-session',
                 '--inactive', '--working', 'Names moved into records; consumer import not verified')
        result = subprocess.run(consumer['integration_context']['refresh']['argv'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        observed, = json.loads(result.stdout)['integration_context']['last_known_workers']
        self.assertEqual(observed['observation'], 'released')
        self.assertEqual(observed['working'], 'Names moved into records; consumer import not verified')
        self.assertEqual(observed['touching_paths'], ['contacts.py'])
