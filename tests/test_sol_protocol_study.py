import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from experiments import sol_protocol_study as study

ROOT = Path(__file__).resolve().parents[1]


class ProtocolCalibrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name)

    def prepare(self, scenario):
        return study.prepare(self.parent / scenario, scenario, 1, ROOT)

    def enroll(self, root):
        return study.pi(root, 'enroll', '--workstream', 'CONSUMER', '--session', 'test-worker',
                        '--working', 'Consumer assessment', '--access', 'edit',
                        '--touching-path', 'consumer.py', '--touching-seam', 'commerce/money')

    def test_freeze_exact_pi_and_private_no_historical_evidence(self):
        for scenario in study.TASKS:
            root = self.prepare(scenario)
            plan = json.loads((root / 'plan.json').read_text())
            study.verify(root, plan)
            self.assertEqual(plan['model'], 'gpt-5.6-sol')
            self.assertEqual(plan['effort'], 'medium')
            self.assertFalse((root / 'pi-source/README.md').exists())
            self.assertFalse((root / 'pi-source/experiments').exists())
            self.assertFalse((root / 'pi-source/docs/results').exists())
            self.assertEqual(study.manifest(root / 'pi-source/project_intent', True),
                             study.manifest(ROOT / 'project_intent', True))
            self.assertEqual((root / 'worker.txt').read_text(), study.TASKS[scenario])
            people = list((root / 'work/.pi/presence').glob('*.json'))
            self.assertEqual(len(people), 1)  # no worker enrollment fabricated
            self.assertEqual(json.loads(people[0].read_text())['session'], study.PEER)

    def test_changes_rejected_before_launch(self):
        root = self.prepare('audit')
        plan = json.loads((root / 'plan.json').read_text())
        (root / 'worker.txt').write_text('changed')
        with self.assertRaises(AssertionError):
            study.verify(root, plan)

    def test_native_profile_mutation_stops_before_execution(self):
        root = self.prepare('audit')
        (root / 'native/worker/config.toml').write_text('model = "different"\n')
        with self.assertRaisesRegex(AssertionError, 'Native profile changed'):
            study.preflight(root, '/unused')
        with self.assertRaisesRegex(AssertionError, 'Native profile changed'):
            study.run(root, '/unused')

    def test_passing_probe_before_migration_is_not_post_change_validation(self):
        root = self.prepare('repair-owner')
        actor = study.PeerActor(root, 'repair-owner')
        actor.transitioned = True
        actor.events = [{'action': 'producer-transition', 'at': '2026-09-09T00:00:10+00:00'}]
        plan = json.loads((root / 'plan.json').read_text())
        row = dict(started_at='2026-09-09T00:00:00+00:00', exit_code=0, stream_complete=True)
        call = dict(id='probe', input='python3 -B contract_test.py',
                    output="INTEGRATED_PROBE '$12.50' expected '$12.50'", start_seconds=1, end_seconds=2,
                    pi_related=False, seconds=1, output_bytes=50)
        with patch.object(study, 'native_evidence', return_value=('test-worker', [], [])), \
                patch.object(study.analysis, 'native_calls', return_value=[call]):
            result = study.assess(root, plan, row, actor)
            self.assertFalse(result['checks']['probe_passed_after_change'])
            call.update(start_seconds=11, end_seconds=12)
            result = study.assess(root, plan, row, actor)
            self.assertTrue(result['checks']['probe_passed_after_change'])

    def test_completed_trial_requires_review_before_next_launch(self):
        root = self.prepare('audit')
        (root / 'started.json').write_text('{}')
        (root / 'result.json').write_text('{}')
        batch = self.parent / 'batch'
        batch.mkdir()
        (batch / 'code').mkdir()
        for name in ('protocol.md', 'test_protocol.py', 'binary'):
            (batch / name).write_text(name)
        study.write_json(batch / 'freeze.json', dict(code_manifest={},
            protocol_sha256=study.sha(batch / 'protocol.md'), test_sha256=study.sha(batch / 'test_protocol.py'),
            codex_entry_sha256=study.sha(batch / 'binary'),
            trials=[dict(root=str(root), label='audit-1', plan_sha256=study.sha(root / 'plan.json'))]))
        with patch.object(study, 'run') as launch:
            with self.assertRaisesRegex(RuntimeError, 'manual review required'):
                study.run_batch(batch, str(batch / 'binary'))
            launch.assert_not_called()

    def test_probe_detects_actual_stale_receipt_not_peer_summary(self):
        root = self.prepare('audit')
        result = subprocess.run(['python3', '-B', 'contract_test.py'], cwd=root / 'work', capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b'$1250.00', result.stdout)
        (root / 'work/consumer.py').write_text(study.CONSUMER_NEW)
        result = subprocess.run(['python3', '-B', 'contract_test.py'], cwd=root / 'work', capture_output=True)
        self.assertEqual(result.returncode, 0)

    def test_owner_actor_requires_real_enrollment_and_valid_claim(self):
        root = self.prepare('repair-owner')
        actor = study.PeerActor(root, 'repair-owner')
        actor.tick()
        self.assertFalse(actor.transitioned)
        self.enroll(root)
        actor.tick()
        self.assertTrue(actor.transitioned)
        self.assertFalse(actor.finished)
        claim = study.pi(root, 'repair-claim', '--workstream', 'CONSUMER', '--session', 'test-worker',
            '--seam', 'commerce/money', '--repair-path', 'consumer.py', '--peer-session', study.PEER,
            '--problem', 'Wrong receipt units', '--check-path', 'consumer.py', '--check-path', 'producer.py',
            '--check-path', 'contract_test.py')
        self.assertFalse(claim['ready_to_edit'])
        actor.tick()
        self.assertTrue(actor.finished)
        repair = study.pi(root, 'repair-status', '--workstream', 'CONSUMER')['repairs'][0]
        self.assertEqual(repair['state'], 'claimed')
        self.assertEqual((root / 'work/consumer.py').read_text(), study.CONSUMER_OLD)

    def test_peer_actor_never_repairs_before_worker_ack(self):
        root = self.prepare('repair-peer')
        self.enroll(root)
        actor = study.PeerActor(root, 'repair-peer')
        actor.tick()
        self.assertIsNotNone(actor.claim)
        self.assertFalse(actor.finished)
        self.assertEqual((root / 'work/consumer.py').read_text(), study.CONSUMER_OLD)
        study.pi(root, 'repair-ack', '--workstream', 'CONSUMER', '--session', 'test-worker',
                 '--repair-id', actor.claim['repair_id'], '--expected-revision', str(actor.claim['revision']))
        actor.tick()
        self.assertTrue(actor.finished)
        repair = study.pi(root, 'repair-status', '--workstream', 'CONSUMER')['repairs'][0]
        self.assertEqual(repair['state'], 'resolved')
        self.assertEqual(repair['verification'], 'owner-reported-checks-source-unchanged')
        self.assertEqual((root / 'work/consumer.py').read_text(), study.CONSUMER_NEW)

    def test_outer_isolation_does_not_mount_peer_actor_or_judge(self):
        root = self.prepare('audit')
        args = study.native.sandbox(root, 'worker', ['true'])
        self.assertNotIn(str(root / 'plan.json'), args)
        self.assertNotIn(str(ROOT), args)
        self.assertNotIn(str(root.parent), args)
        self.assertIn(str(root / 'work'), args)
        self.assertIn(str(root / 'pi-source'), args)
        self.assertIn('--unshare-pid', args)


if __name__ == '__main__':
    unittest.main()
