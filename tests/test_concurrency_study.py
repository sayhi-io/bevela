import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments import concurrency_study as study
from experiments import concurrency_analysis as analysis

ROOT = Path(__file__).resolve().parents[1]


class ConcurrencyStudyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name)

    def prepare(self, condition):
        return study.prepare(condition, ROOT, self.parent)

    def test_four_arms_same_original_fixture_tasks_and_checker(self):
        roots = {c: self.prepare(c) for c in study.CONDITIONS}
        baseline = study.manifest(study.original.ASSETS / 'fixture', ignore_cache=True)
        for condition, root in roots.items():
            actual = study.manifest(root / 'work', ignore_cache=True)
            self.assertEqual({p: v for p, v in actual.items()
                              if p != 'AGENTS.md' and not p.startswith(('.pi/', 'tasks/'))}, baseline)
            self.assertEqual(study.sha(root / 'check_contract.py'),
                             study.sha(ROOT / 'experiments/seven_seams_check.py'))
            for role in study.original.ROLES:
                self.assertEqual(study.sha(root / (role + '.txt')),
                                 study.sha(study.original.ASSETS / (role + '.txt')))
                self.assertEqual(study.sha(root / 'work/tasks' / (role + '.txt')),
                                 study.sha(root / (role + '.txt')))
            self.assertFalse((root / 'started.json').exists())
            self.assertEqual((root / 'pi-source').exists(), condition in ('C', 'D'))
            self.assertEqual((root / 'work/AGENTS.md').read_text().startswith(study.COMMON), True)
        self.assertEqual(study.sha(roots['A'] / 'solo.txt'), study.sha(roots['D'] / 'solo.txt'))

    def test_pi_has_only_tasks_and_no_checker_or_previous_evidence(self):
        for condition in ('C', 'D'):
            root = self.prepare(condition)
            snapshot = json.loads((root / 'work/.pi/snapshot.json').read_text())
            self.assertEqual({r['id'] for r in snapshot['records']},
                             {r.upper() for r in study.CONDITIONS[condition]})
            for row in snapshot['records']:
                self.assertEqual(row['statement'], (root / (row['id'].lower() + '.txt')).read_text().strip())
                self.assertEqual(row['acceptance'], [row['statement']])
                self.assertEqual(len(row['boundaries']), 7)
            self.assertFalse((root / 'work/check_contract.py').exists())
            self.assertFalse((root / 'work/.pi/presence').exists())
            self.assertFalse((root / 'pi-source/experiments').exists())
            self.assertFalse((root / 'pi-source/tests').exists())
            self.assertEqual({p.name for p in (root / 'pi-source/docs').iterdir()}, set(study.OPERATIONAL_DOCS))
            self.assertFalse((root / 'pi-source/docs/CLI_AB_PILOT_01.md').exists())

    def test_recorder_mutation_is_rejected(self):
        root = self.prepare('A')
        plan = json.loads((root / 'plan.json').read_text())
        plan['recorder_hashes']['concurrency_study.py'] = 'not-the-recorder'
        with self.assertRaisesRegex(ValueError, 'Recorder source changed'):
            study.verify(root, plan)

    def test_refuses_mutated_input_before_launch(self):
        root = self.prepare('A')
        (root / 'consumer.txt').write_text('changed')
        with patch.object(study, 'record', side_effect=AssertionError('must not launch')):
            with self.assertRaises(ValueError):
                study.run(root)

    def test_concurrency_uses_project_window_not_sum(self):
        result = study.concurrency([
            {'start_monotonic_ns': 1_000_000_000, 'end_monotonic_ns': 5_000_000_000},
            {'start_monotonic_ns': 2_000_000_000, 'end_monotonic_ns': 7_000_000_000}])
        self.assertEqual(result['worker_interval_seconds'], 6)
        self.assertEqual(result['worker_seconds'], 9)
        self.assertEqual(result['factor'], 1.5)
        self.assertEqual(result['max_simultaneous'], 2)

    def test_tokens_use_last_cumulative_sample_not_sum(self):
        native = [{'type': 'event_msg', 'payload': {'type': 'token_count', 'info': {
            'total_token_usage': {'input_tokens': n, 'cached_input_tokens': n // 2,
                                  'output_tokens': 20, 'reasoning_output_tokens': 5}}}}
            for n in (100, 300, 500)]
        self.assertEqual(analysis.last_usage(native)['input_tokens'], 500)
        self.assertEqual(analysis.last_usage(native)['output_tokens'], 20)
        self.assertIsNone(analysis.last_usage([]))

    def test_tool_duration_uses_native_call_pair(self):
        native = [
            {'type': 'response_item', 'timestamp': '2026-09-09T00:00:01.000Z',
             'payload': {'type': 'custom_tool_call', 'call_id': 'a', 'name': 'exec',
                         'input': 'project-intent onboard'}},
            {'type': 'response_item', 'timestamp': '2026-09-09T00:00:01.250Z',
             'payload': {'type': 'custom_tool_call_output', 'call_id': 'a',
                         'output': [{'text': 'result'}]}}]
        calls = analysis.native_calls(native, '2026-09-09T00:00:00+00:00')
        self.assertEqual(calls[0]['seconds'], .25)
        self.assertTrue(calls[0]['pi_related'])
        self.assertEqual(calls[0]['output_bytes'], 6)

    def test_source_observer_preserves_versions_without_touching_work(self):
        root = self.prepare('A')
        observer = study.SourceObserver(root)
        before = study.manifest(root / 'work')
        observer.capture('initial')
        self.assertEqual(study.manifest(root / 'work'), before)
        target = root / 'work/presentation.py'
        original = target.read_bytes()
        target.write_bytes(original + b'\n# changed\n')
        observer.capture('change')
        observer.close()
        rows = [json.loads(line) for line in (root / 'source-history.jsonl').read_text().splitlines()]
        self.assertEqual(len(rows), 2)
        self.assertEqual((root / 'objects' / rows[0]['files']['presentation.py']).read_bytes(), original)
        self.assertNotEqual(rows[0]['files']['presentation.py'], rows[1]['files']['presentation.py'])

    def test_each_arm_exact_process_count_and_no_retries(self):
        for condition in study.CONDITIONS:
            root = self.prepare(condition)
            def fake(root, role, binary, plan, observer):
                return {'role': role, 'exit_code': 0, 'start_monotonic_ns': 1,
                        'end_monotonic_ns': 2, 'elapsed_seconds': 1e-9}
            with patch.object(study.shutil, 'which', return_value='/fake'), \
                    patch.object(study.subprocess, 'check_output', return_value='fake'), \
                    patch.object(study, 'record', side_effect=fake) as record:
                result = study.run(root)
                self.assertEqual(record.call_count, len(study.CONDITIONS[condition]))
                self.assertEqual(result['result']['score'], 0)
                self.assertFalse(result['accepted'])
                self.assertIsNone(result['accepted_project_seconds'])
                with self.assertRaises(FileExistsError):
                    study.run(root)
                self.assertEqual(record.call_count, len(study.CONDITIONS[condition]))
