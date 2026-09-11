import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch

from experiments import qwen_independent_tasks as study


class IndependentTaskTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.runtime = self.root / 'runtime'
        (self.runtime / 'bin').mkdir(parents=True)
        (self.runtime / 'bin/qwen').write_text('console.log("0.23.2");\n')

    def prepare(self, pi=False, name='trial'):
        engine = study.runner(pi)
        root = engine.prepare(self.root / name, study.SOURCE, self.runtime, 'http://localhost:8078/v1')
        return engine, root, engine.verify(root, before=True)

    def test_identical_task_inputs_across_arms_distinct_between_workers(self):
        original_roles = study.original.base.ROLES
        a, ra, pa = self.prepare(False, 'a')
        b, rb, pb = self.prepare(True, 'b')
        self.assertEqual(study.original.base.ROLES, original_roles)
        for key in ('fixture_manifest', 'input_hashes', 'runtime_manifest', 'settings_sha256', 'historical_fixture_manifest'):
            self.assertEqual(pa[key], pb[key], key)
        self.assertEqual(pa['roles'], ['money', 'recovery', 'returns'])
        self.assertEqual(len({(ra / (r + '.txt')).read_text() for r in study.ROLES}), 3)
        for role in study.ROLES:
            self.assertEqual((ra / (role + '.txt')).read_text(), study.TASKS[role])
            self.assertEqual((rb / 'work/tasks' / (role + '.txt')).read_text(), study.TASKS[role])
        self.assertTrue(set(pa['sessions'].values()).isdisjoint(pb['sessions'].values()))
        self.assertFalse((ra / 'pi-source').exists())
        self.assertFalse((ra / 'work/.pi').exists())
        self.assertEqual((ra / 'work/AGENTS.md').read_text(), study.COMMON)
        self.assertEqual((rb / 'work/AGENTS.md').read_text(), study.COMMON + '\n' + study.steering.compact.instructions(study.SCOPE))
        settings = study.read(ra / 'settings-template.json')
        self.assertEqual(settings['model']['maxSessionTurns'], 500)
        self.assertEqual(settings['model']['maxToolCallsPerTurn'], 500)
        self.assertEqual(settings['model']['reasoningEffort'], 'none')
        self.assertNotIn('hooks', settings)
        self.assertEqual(pa['timeout_seconds'], 1800)

    def test_unchanged_source_checker_and_lossless_contract_replacements(self):
        engine, root, plan = self.prepare()
        for name, info in plan['historical_fixture_manifest'].items():
            if name not in ('README.md', 'OBJECTIVE.md') and not name.startswith('tasks/'):
                self.assertEqual(info, plan['fixture_manifest'][name], name)
        objective = (root / 'work/OBJECTIVE.md').read_text()
        for old, new in reversed(study.REPLACEMENTS):
            self.assertEqual(objective.count(new), 1)
            objective = objective.replace(new, old)
        self.assertEqual(objective, (study.FIXTURE / 'OBJECTIVE.md').read_text())
        self.assertNotIn('Implement only your assigned component', (root / 'work/OBJECTIVE.md').read_text())
        self.assertEqual(set(p.name for p in (root / 'work/tasks').iterdir()), {r + '.txt' for r in study.ROLES})
        self.assertEqual(engine.sha(root / 'check_contract.py'), engine.sha(study.FIXTURE / 'acceptance.py'))
        # Reference is used only in this disposable unit test; never model inputs.
        for component in study.original.base.ROLES:
            shutil.copytree(study.FIXTURE.parent / 'reference' / component, root / 'work' / component, dirs_exist_ok=True)
        # Preserve the historical sandbox without requiring an operator's npm
        # installation for this Python-only reference check.
        (self.root / '.npm-global').mkdir()
        with patch.object(Path, 'home', return_value=self.root):
            result = engine.base.score(root / 'work', root / 'check_contract.py')
        self.assertTrue(result['accepted'])
        self.assertEqual(sum(g['passed'] for g in result['groups'].values()), 15)

    def test_snapshot_has_only_actual_task_facts_and_broad_public_architecture(self):
        engine, root, plan = self.prepare(True)
        snapshot = study.read(root / 'work/.pi/snapshot.json')
        public = study.read(root / 'work/architecture.json')['boundaries']
        boundaries = sorted({b for entries in public.values() for b in entries})
        self.assertEqual(len(snapshot['records']), 3)
        for record, role in zip(snapshot['records'], study.ROLES):
            self.assertEqual(record['id'], role.upper())
            self.assertEqual(record['scope'], study.TASKS[role])
            self.assertEqual(record['acceptance'], [study.TASKS[role]])
            self.assertEqual(record['boundaries'], boundaries)
            self.assertNotIn('touching_paths', record)
        binding = study.read(root / 'pi-source/steering.json')
        self.assertEqual(len(binding['baseline']), 12)
        self.assertNotIn('acceptance.py', binding['baseline'])
        self.assertEqual(set(binding['sessions'].values()), {'MONEY', 'RECOVERY', 'RETURNS'})

    def test_real_isolation_and_native_hook_for_non_component_tasks(self):
        for pi in (False, True):
            engine, root, plan = self.prepare(pi, str(pi))
            engine.preflight(root)
            if not pi:
                continue
            for role in study.ROLES:
                event = dict(session_id=plan['sessions'][role], cwd=str(root / 'work'), hook_event_name='UserPromptSubmit')
                env = {**os.environ, 'HOME': str(root / 'qwen-home' / role), 'QWEN_SESSION_ID': event['session_id']}
                result = subprocess.run(['/usr/bin/python3', '-B', '-I', str(root / 'pi-source/qwen_nested_steering_hook.py')],
                    input=json.dumps(event), capture_output=True, text=True, env=env, check=True)
                self.assertEqual(result.stderr, '')
                self.assertIn('PI update:', result.stdout)

    def test_hash_fences_and_no_replay(self):
        engine, root, plan = self.prepare()
        (root / 'started.json').write_text('{}')
        with self.assertRaises(FileExistsError):
            engine.run(root)
        (root / 'money.txt').write_text('different task')
        with self.assertRaises(AssertionError):
            engine.verify(root)

    def test_three_native_workers_are_actually_launched_concurrently(self):
        engine, root, plan = self.prepare()
        barrier = threading.Barrier(3, timeout=5)
        seen = []
        def fake_record(root, role, plan, observer):
            seen.append(role)
            barrier.wait()
            raise RuntimeError('intentional test boundary after three concurrent entries')
        engine.adapter.record = fake_record
        with self.assertRaisesRegex(RuntimeError, 'intentional test boundary'):
            engine.run(root)
        self.assertEqual(set(seen), set(study.ROLES))

    def test_six_projects_sequential_and_failed_correctness_not_replaced(self):
        batch = self.root / 'batch'
        study.freeze(batch, self.runtime, 'http://localhost:8078/v1')
        actual_runner, calls = study.runner, []
        def fake_runner(pi):
            engine = actual_runner(pi)
            def run(root):
                self.assertEqual(len(calls), study.ORDER.index(root.name))
                calls.append(root.name)
                return dict(accepted=False, result={'groups': {'x': {'passed': False}}}, project_seconds=1,
                    infrastructure_errors=[], protected_inputs_changed=[],
                    workers=[{'relay_complete': True, 'stream_complete': True}])
            engine.run = run
            return engine
        with patch.object(study, 'runner', side_effect=fake_runner):
            study.run_all(batch)
            with self.assertRaises(FileExistsError):
                study.run_all(batch)
        self.assertEqual(calls, list(study.ORDER))
        self.assertTrue((batch / 'completed.json').exists())


if __name__ == '__main__':
    unittest.main()
