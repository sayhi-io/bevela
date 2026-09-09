import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from experiments import distributed_study as study

ROOT = Path(__file__).resolve().parents[1]


class DistributedRecorderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='distributed-unit-')
        self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name)
        self.fixture = self.parent / 'fixture'
        (self.fixture / 'tasks').mkdir(parents=True)
        (self.fixture / 'OBJECTIVE.md').write_text('Migrate the complete product.\n')
        (self.fixture / 'README.md').write_text('All requirements in OBJECTIVE.md.\n')
        for role in study.ROLES:
            (self.fixture / role).mkdir()
            (self.fixture / role / '__init__.py').write_text('VALUE = 1\n')
            (self.fixture / 'tasks' / (role + '.txt')).write_text('Implement ' + role + '.\n')
        study.write_json(self.fixture / 'architecture.json', {'boundaries': {
            role: ['product/shared-contract'] for role in study.ROLES}})
        self.checker = self.parent / 'checker.py'
        self.checker.write_text('import json\nprint(json.dumps({"accepted": True, "failed_contracts": []}))\n')
        (self.fixture / 'acceptance.py').write_bytes(self.checker.read_bytes())

    def prepare(self, condition):
        return study.prepare(self.parent / condition, condition, ROOT, self.fixture, self.checker)

    def test_matched_roles_task_information_and_no_prior_evidence(self):
        ordinary, pi = self.prepare('B'), self.prepare('C')
        for role in study.ROLES:
            self.assertEqual((ordinary / (role + '.txt')).read_bytes(), (pi / (role + '.txt')).read_bytes())
        for name, digest in study.manifest(self.fixture).items():
            self.assertEqual(study.sha(ordinary / 'work' / name), digest['sha256'])
            self.assertEqual(study.sha(pi / 'work' / name), digest['sha256'])
        self.assertFalse((ordinary / 'pi-source').exists())
        self.assertFalse((pi / 'pi-source/README.md').exists())
        self.assertFalse((pi / 'pi-source/experiments').exists())
        self.assertFalse((pi / 'pi-source/docs/results').exists())
        self.assertFalse((pi / 'work/.pi/presence').exists())
        records = json.loads((pi / 'work/.pi/snapshot.json').read_text())['records']
        self.assertEqual(len(records), 4)
        for row, role in zip(records, study.ROLES):
            self.assertEqual(row['scope'], (self.fixture / 'tasks' / (role + '.txt')).read_text())
            self.assertEqual(row['acceptance'], [(self.fixture / 'OBJECTIVE.md').read_text()])
        study.verify(ordinary, before=True)
        study.verify(pi, before=True)

    def test_solo_complete_objective_and_native_profile(self):
        root = self.prepare('A')
        plan = study.verify(root, before=True)
        self.assertEqual(plan['roles'], ['solo'])
        self.assertEqual((plan['model'], plan['effort']), ('gpt-5.6-sol', 'medium'))
        self.assertEqual(plan['timeout_seconds'], 900)
        self.assertIn('own all four components', (root / 'solo.txt').read_text())
        self.assertEqual(list((root / 'native/solo').iterdir()), [root / 'native/solo/config.toml'])

    def test_changed_profile_rejected_before_launch(self):
        root = self.prepare('A')
        (root / 'native/solo/config.toml').write_text('model = "wrong"\n')
        with patch.object(study.native, 'record') as record:
            with self.assertRaises(AssertionError):
                study.run(root, '/unused')
            record.assert_not_called()
        self.assertFalse((root / 'started.json').exists())

    def test_extra_profile_file_rejected_before_launch(self):
        root = self.prepare('A')
        (root / 'native/solo/prior-memory.md').write_text('Prior answer')
        with self.assertRaisesRegex(AssertionError, 'not fresh'):
            study.verify(root, before=True)

    def test_prompt_and_product_input_mutations_rejected(self):
        root = self.prepare('B')
        prompt = root / 'catalog.txt'
        original = prompt.read_bytes()
        prompt.write_text('Replacement hints')
        with self.assertRaises(AssertionError):
            study.verify(root, before=True)
        prompt.write_bytes(original)
        (root / 'work/orders/__init__.py').write_text('VALUE = 2\n')
        with self.assertRaises(AssertionError):
            study.verify(root, before=True)

    def test_pi_source_mutation_rejected(self):
        root = self.prepare('C')
        (root / 'pi-source/project_intent/__init__.py').write_text('changed')
        with self.assertRaises(AssertionError):
            study.verify(root)

    def test_regenerated_baseline_is_rejected_by_frozen_plan(self):
        root = self.prepare('A')
        (root / 'work/OBJECTIVE.md').write_text('Different task')
        study.write_json(root / 'before.json', study.manifest(root / 'work', ignore_cache=True))
        with self.assertRaisesRegex(AssertionError, 'Prepared baseline changed'):
            study.verify(root, before=True)

    def test_score_uses_frozen_checker_without_mutating_source(self):
        root = self.prepare('A')
        (root / 'work/acceptance.py').write_text('raise RuntimeError("worker checker")')
        # Unit test the copy/checker boundary without requiring host Codex/bwrap.
        # Actual namespace behavior is checked by frozen preflight before models.
        with patch.object(study.native, 'sandbox', side_effect=lambda root, role, argv: argv):
            self.assertTrue(study.score(root / 'work', self.checker)['accepted'])
        self.assertIn('worker checker', (root / 'work/acceptance.py').read_text())

    def test_version_preflight_cannot_contaminate_worker_profiles(self):
        root = self.prepare('B')
        calls = []
        def sandbox(root, role, argv):
            return [role, *argv]
        def execute(argv, **kwargs):
            calls.append(argv)
            if argv[-1] == '--version':
                # Reproduce the real CLI's no-inference helper-file side effect.
                (root / 'native' / argv[0] / 'tmp').mkdir()
            return subprocess.CompletedProcess(argv, 0, 'codex-cli 0.153.4', '')
        with patch.object(study.native, 'sandbox', side_effect=sandbox), \
                patch.object(study.subprocess, 'run', side_effect=execute):
            study.preflight(root, '/fake/codex')
        self.assertEqual(calls[0][0], 'preflight-version')
        self.assertEqual([c[0] for c in calls[1:]], list(study.ROLES))
        study.verify(root, before=True)

    def test_symlink_candidate_not_executed(self):
        root = self.prepare('A')
        (root / 'work/outside.py').symlink_to(self.checker)
        result = study.score(root / 'work', self.checker)
        self.assertFalse(result['accepted'])
        self.assertIn('symbolic links', result['evaluation_error'])

    def test_stage_conditions_cannot_silently_expand_or_mix(self):
        with self.assertRaisesRegex(ValueError, 'preregistered'):
            study.freeze(self.parent / 'batch', ROOT, self.fixture, list('BCB'), 'calibration', '/unused')
        self.assertFalse((self.parent / 'batch').exists())

    def test_replay_rejects_changed_objective_even_if_code_passes(self):
        root = self.prepare('A')
        study.write_json(root / 'result.json', {'concurrency': {'start_ns': 1}, 'accepted': False})
        observer = study.SourceObserver(root)
        observer.capture('initial')
        (root / 'work/OBJECTIVE.md').write_text('Weakened requirement')
        observer.capture('changed')
        observer.close()
        with patch.object(study, 'score', return_value={'accepted': True}):
            result = study.replay(root)
        self.assertTrue(result['sampled_states'][0]['accepted'])
        self.assertFalse(result['sampled_states'][1]['accepted'])
        self.assertIsNone(result['durable_accepted_sample_seconds'])

    def test_replay_observes_symlink_and_reconciles_final_rejection(self):
        root = self.prepare('A')
        study.write_json(root / 'result.json', {'concurrency': {'start_ns': 1}, 'accepted': False})
        observer = study.SourceObserver(root)
        observer.capture('initial')
        (root / 'work/link.py').symlink_to(self.checker)
        observer.capture('symlink')
        observer.close()
        with patch.object(study, 'score', return_value={'accepted': True}):
            result = study.replay(root)
        self.assertFalse(result['sampled_states'][-1]['accepted'])
        self.assertIsNone(result['durable_accepted_sample_seconds'])
        self.assertTrue(result['final_sample_matches_final_score'])

    def test_replay_checks_object_hashes(self):
        root = self.prepare('A')
        study.write_json(root / 'result.json', {'concurrency': {'start_ns': 1}, 'accepted': True})
        observer = study.SourceObserver(root)
        observer.capture('initial')
        observer.close()
        next((root / 'objects').iterdir()).write_text('tampered bytes')
        with self.assertRaisesRegex(AssertionError, 'digest mismatch'):
            study.replay(root)

    def batch(self, root):
        batch = self.parent / 'batch'
        (batch / 'code').mkdir(parents=True)
        (batch / 'fixture').mkdir()
        (batch / 'tests').mkdir()
        (batch / 'protocol.md').write_text('Frozen protocol')
        binary = batch / 'binary'
        binary.write_text('native executable fingerprint')
        registry = self.parent / 'study'
        registry.mkdir()
        study.write_json(batch / 'freeze.json', dict(code_manifest={}, fixture_manifest={}, tests_manifest={},
            study_root=str(registry),
            protocol_sha256=study.sha(batch / 'protocol.md'), codex_entry_sha256=study.sha(binary),
            codex_version='fake-test-only', stage='calibration',
            trials=[dict(label='B1', root=str(root), plan_sha256=study.sha(root / 'plan.json'))]))
        study.write_json(registry / 'study.json', {'codex_version': 'fake-test-only',
                         'codex_entry_sha256': study.sha(binary), 'batches': [dict(path=str(batch),
                         freeze_sha256=study.sha(batch / 'freeze.json'))]})
        return batch, str(binary)

    def test_interrupted_project_is_not_retried(self):
        root = self.prepare('B')
        (root / 'started.json').write_text('{}')
        batch, binary = self.batch(root)
        with patch.object(study.subprocess, 'check_output', return_value='fake-test-only'), \
                patch.object(study, 'run') as run:
            with self.assertRaisesRegex(RuntimeError, 'infrastructure interruption'):
                study.run_next(batch, binary)
            run.assert_not_called()

    def registry(self, candidates):
        registry = self.parent / 'study'
        (registry / 'pi-source').mkdir(parents=True)
        study.write_json(registry / 'study.json', dict(version=study.VERSION, pi_manifest={},
            codex_version='fake-test-only', codex_entry_sha256=study.sha(self.checker),
            candidates=candidates, ceiling=None, evaluation=None))
        (self.parent / 'experiments').mkdir()
        (self.parent / 'experiments/distributed_check.py').write_bytes(self.checker.read_bytes())
        return registry

    def test_cross_batch_candidate_limit_is_enforced(self):
        registry = self.registry([{}, {}])
        with patch.object(study.subprocess, 'check_output', return_value='fake-test-only'), \
                self.assertRaisesRegex(RuntimeError, 'budget exhausted'):
            study.freeze(self.parent / 'third-batch', self.parent, self.fixture,
                         list('BBB'), 'calibration', str(self.checker), registry)
        self.assertFalse((self.parent / 'third-batch').exists())

    def test_ceiling_cannot_skip_ordinary_calibration(self):
        registry = self.registry([])
        with patch.object(study.subprocess, 'check_output', return_value='fake-test-only'), \
                self.assertRaisesRegex(RuntimeError, 'Ordinary calibration required'):
            study.freeze(self.parent / 'ceiling', self.parent, self.fixture,
                         list('AA'), 'ceiling', str(self.checker), registry)

    def test_changed_native_binary_cannot_start_new_stage(self):
        registry = self.registry([])
        changed = self.parent / 'changed-binary'
        changed.write_text('changed executable')
        with self.assertRaisesRegex(AssertionError, 'Native executable changed within study'):
            study.freeze(self.parent / 'ceiling', self.parent, self.fixture,
                         list('AA'), 'ceiling', str(changed), registry)
        with patch.object(study.subprocess, 'check_output', return_value='changed-version'), \
                self.assertRaises(AssertionError):
            study.freeze(self.parent / 'ceiling', self.parent, self.fixture,
                         list('AA'), 'ceiling', str(self.checker), registry)

    def test_study_execution_lock_rejects_second_project(self):
        registry = self.registry([])
        with study.study_lock(registry):
            with self.assertRaises(BlockingIOError):
                with study.study_lock(registry):
                    self.fail('Second project acquired active study lock')

    def test_completed_project_requires_review(self):
        root = self.prepare('B')
        (root / 'started.json').write_text('{}')
        (root / 'result.json').write_text('{}')
        batch, binary = self.batch(root)
        with patch.object(study.subprocess, 'check_output', return_value='fake-test-only'), \
                patch.object(study, 'run') as run:
            with self.assertRaisesRegex(RuntimeError, 'Review completed'):
                study.run_next(batch, binary)
            run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
