import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from experiments import qwen_compact_pi as compact
from experiments import qwen_profiles as profiles

SOURCE = Path(__file__).resolve().parents[1]


class CompactPITests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.parent = Path(temp.name)
        self.runtime = self.parent / 'runtime'
        (self.runtime / 'bin').mkdir(parents=True)
        (self.runtime / 'bin/qwen').write_text('console.log("0.23.2");\n')
        self.engine = compact.runner()

    def prepare(self):
        return self.engine.prepare(self.parent / 'trial', 'C', SOURCE, self.runtime,
                                   'http://127.0.0.1:8078/v1', 5)

    def test_compact_generic_text_and_unchanged_task_backend_checker(self):
        root = self.prepare()
        plan = self.engine.verify(root, before=True)
        text = (root / 'work/AGENTS.md').read_text()
        self.assertLess(len(text.split()), 310)
        for word in ('sayhi', 'sparkops', 'sparkpyro', 'tea', 'NAMES', 'REFUNDED'):
            self.assertNotIn(word, text)
        self.assertEqual(plan['roles'], ['producer', 'consumer'])
        for name, value in plan['fixture_manifest'].items():
            self.assertEqual(self.engine.manifest(root / 'work')[name], value)
        self.assertEqual(self.engine.sha(root / 'check_contract.py'),
                         self.engine.sha(SOURCE / 'experiments/seven_seams_check.py'))
        self.assertEqual(self.engine.manifest(root / 'pi-source/project_intent'),
                         self.engine.manifest(SOURCE / 'project_intent', ignore_cache=True))
        self.assertEqual(self.engine.manifest(root / 'pi-source/skills/project-intent'),
                         self.engine.manifest(SOURCE / 'skills/project-intent', ignore_cache=True))
        for role in self.engine.ROLES:
            self.assertEqual((root / (role + '.txt')).read_bytes(),
                (self.engine.common.original.ASSETS / (role + '.txt')).read_bytes())
        self.assertEqual(subprocess.check_output(['git', '-C', str(root / 'work'), 'rev-list', '--count', 'HEAD'], text=True).strip(), '1')
        self.engine.preflight(root)

    def test_relative_cli_helper_works_in_worker_namespace(self):
        root = self.prepare()
        plan = self.engine.verify(root)
        helper = (root / 'work/AGENTS.md').read_text().split('```sh\n')[1].split('```')[0]
        command = self.engine.adapter.sandbox(root, 'producer',
            ['/bin/sh', '-c', helper + '\npi start --workstream PRODUCER'],
            plan['sessions']['producer'], pi=True)
        result = subprocess.run(command, text=True, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('integration_context', result.stdout)

    def test_template_tamper_refused(self):
        root = self.prepare()
        fake = self.parent / 'different.md'
        fake.write_text('different')
        with patch.object(compact, 'TEMPLATE', fake), self.assertRaises(ValueError):
            self.engine.verify(root)

    def test_three_trials_no_replay_and_historical_profile_untouched(self):
        batch = self.parent / 'batch'
        with patch.object(self.engine, 'preflight'):
            self.engine.freeze(batch, SOURCE, self.runtime, 'http://127.0.0.1:8078/v1', 5)
        calls = []
        def fake(root):
            calls.append(root.parent.name)
            return dict(result={'score': 0}, accepted=False, workers=[], project_seconds=1, infrastructure_ok=True)
        with patch.object(self.engine, 'run', side_effect=fake):
            self.engine.run_all(batch)
            self.assertEqual(calls, ['C1', 'C2', 'C3'])
            with self.assertRaises(FileExistsError):
                self.engine.run_all(batch)
        old = profiles.runner(compact.PROFILE)
        self.assertEqual(old.VERSION, profiles.VERSION)


if __name__ == '__main__':
    unittest.main()
