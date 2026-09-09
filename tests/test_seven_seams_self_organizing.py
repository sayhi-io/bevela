import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from experiments import seven_seams_self_organizing as study

ROOT = Path(__file__).resolve().parents[1]


class SelfOrganizingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name)

    def prepare(self, condition):
        return study.prepare(condition, ROOT, self.parent)

    def test_exact_same_prompt_no_allocation_and_original_bytes(self):
        hashes = set()
        for condition, count in study.CONDITIONS.items():
            root = self.prepare(condition)
            plan = json.loads((root / 'plan.json').read_text())
            self.assertEqual(len(plan['roles']), count)
            for role in plan['roles']:
                hashes.add(study.sha(root / (role + '.txt')))
                self.assertEqual((root / (role + '.txt')).read_text(), study.PROMPT)
            for name, entry in plan['fixture_manifest'].items():
                self.assertEqual(study.manifest(root / 'work')[name], entry)
            self.assertEqual(study.sha(root / 'work/acceptance.py'),
                             study.sha(ROOT / 'experiments/seven_seams_check.py'))
            expected = '\n'.join((study.base.original.ASSETS / (r + '.txt')).read_text()
                                  for r in study.base.original.ROLES)
            self.assertEqual((root / 'work/OBJECTIVE.md').read_text(), expected)
            self.assertFalse((root / 'work/tasks').exists())
            self.assertEqual(subprocess.check_output(['git', '-C', str(root / 'work'), 'status', '--porcelain']), b'')
        self.assertEqual(len(hashes), 1)

    def test_pi_has_one_whole_project_not_worker_assignments(self):
        for condition in ('C', 'D'):
            root = self.prepare(condition)
            data = json.loads((root / 'work/.pi/snapshot.json').read_text())
            self.assertEqual(len(data['records']), 1)
            record = data['records'][0]
            self.assertEqual(record['id'], 'PROJECT')
            self.assertEqual(record['scope'], (root / 'work/OBJECTIVE.md').read_text())
            self.assertEqual(len(record['boundaries']), 7)
            self.assertFalse((root / 'work/.pi/presence').exists())
            self.assertFalse((root / 'pi-source/experiments').exists())
            self.assertEqual({p.name for p in (root / 'pi-source/docs').iterdir()}, set(study.base.OPERATIONAL_DOCS))

    def test_isolation_has_one_shared_work_and_private_native_profile(self):
        root = self.prepare('B')
        first = study.sandbox(root, 'worker1', ['true'])
        second = study.sandbox(root, 'worker2', ['true'])
        for args in (first, second):
            self.assertEqual(args.count(str(root / 'work')), 3)  # source, target, cwd
            self.assertNotIn(str(root / 'before'), args)
            self.assertNotIn(str(Path.home() / 'sayhi'), args)
            self.assertIn('--unshare-pid', args)
        self.assertIn(str(root / 'native/worker1'), first)
        self.assertNotIn(str(root / 'native/worker2'), first)
        self.assertIn(str(root / 'native/worker2'), second)

    def test_mutation_refused(self):
        root = self.prepare('A')
        plan = json.loads((root / 'plan.json').read_text())
        plan['self_recorder_sha256'] = 'changed'
        with self.assertRaises(ValueError):
            study.verify(root, plan)
        plan = json.loads((root / 'plan.json').read_text())
        (root / 'worker1.txt').write_text('own prices')
        with self.assertRaises(ValueError):
            study.verify(root, plan)

    def test_exact_launch_counts_and_preserve_failures_without_retry(self):
        for condition, count in study.CONDITIONS.items():
            root = self.prepare(condition)
            def fake(root, role, binary, plan, observer):
                return {'role': role, 'exit_code': 1, 'start_monotonic_ns': 1,
                        'end_monotonic_ns': 2, 'elapsed_seconds': 1e-9}
            with patch.object(study.shutil, 'which', return_value='/fake'), \
                    patch.object(study.subprocess, 'check_output', return_value='fake'), \
                    patch.object(study, 'record', side_effect=fake) as record:
                result = study.run(root)
                self.assertEqual(record.call_count, count)
                self.assertEqual(result['result']['score'], 0)
                self.assertFalse(result['accepted'])
                self.assertEqual(result['human_interventions'], 0)
                with self.assertRaises(FileExistsError):
                    study.run(root)
                self.assertEqual(record.call_count, count)
