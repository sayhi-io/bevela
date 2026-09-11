import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from experiments import qwen_single_worker as single
from experiments import qwen_seven_seams as original

SOURCE = Path(__file__).resolve().parents[1]


class SingleWorkerTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.parent = Path(temp.name)
        self.runtime = self.parent / 'runtime'
        (self.runtime / 'bin').mkdir(parents=True)
        (self.runtime / 'bin/qwen').write_text('console.log("0.23.2");\n')
        self.engine = single.runner()

    def prepare(self):
        return self.engine.prepare(self.parent / 'A1', 'A', SOURCE, self.runtime,
                                   'http://127.0.0.1:8078/v1', timeout=5)

    def test_complete_task_original_fixture_and_isolation(self):
        root = self.prepare()
        plan = self.engine.verify(root, before=True)
        self.assertEqual(plan['roles'], ['solo'])
        self.assertEqual(len(plan['sessions']), 1)
        self.assertFalse((root / 'work/.pi').exists())
        self.assertFalse((root / 'work/AGENTS.md').exists())
        self.assertFalse((root / 'work/tasks').exists())
        for role in original.ROLES:
            self.assertIn((original.common.original.ASSETS / (role + '.txt')).read_text(),
                          (root / 'solo.txt').read_text())
        for name, value in plan['fixture_manifest'].items():
            self.assertEqual(self.engine.manifest(root / 'work')[name], value)
        self.assertEqual(self.engine.sha(root / 'check_contract.py'),
                         self.engine.sha(SOURCE / 'experiments/seven_seams_check.py'))
        self.engine.preflight(root)
        self.assertEqual(original.ROLES, ('producer', 'consumer'))

    def test_tampered_worker_count_refused(self):
        root = self.prepare()
        plan = self.engine.verify(root)
        plan['worker_count'] = 2
        self.engine.write_json(root / 'plan.json', plan)
        with self.assertRaises(ValueError):
            self.engine.verify(root)

    def test_three_fresh_projects_sequential_and_no_replay(self):
        batch = self.parent / 'batch'
        with patch.object(self.engine, 'preflight'):
            self.engine.freeze(batch, SOURCE, self.runtime, 'http://127.0.0.1:8078/v1', 5)
        frozen = json.loads((batch / 'frozen.json').read_text())
        sessions = [self.engine.verify(batch / p['root'])['sessions']['solo'] for p in frozen['plans'].values()]
        self.assertEqual(len(set(sessions)), 3)
        calls = []
        def fake(root):
            calls.append(root.parent.name)
            return dict(result={'score': 0}, accepted=False, project_seconds=1,
                        workers=[], infrastructure_ok=True)
        with patch.object(self.engine, 'run', side_effect=fake):
            self.engine.run_all(batch)
            self.assertEqual(calls, ['A1', 'A2', 'A3'])
            with self.assertRaises(FileExistsError):
                self.engine.run_all(batch)

    def test_real_recorder_launches_exactly_one_worker(self):
        root = self.prepare()
        def fake(root, role, plan, observer):
            folder = root / role
            folder.mkdir()
            session = plan['sessions'][role]
            events = [dict(type='system', subtype='init', model=self.engine.MODEL, session_id=session),
                      dict(type='result', subtype='success', session_id=session)]
            (folder / 'stdout.jsonl').write_text('\n'.join(map(json.dumps, events)) + '\n')
            request = dict(event='request', request=1, model=self.engine.MODEL,
                           reasoning_effort='medium', chat_template_kwargs={'enable_thinking': False}, max_tokens=32768)
            (folder / 'transport.jsonl').write_text(json.dumps(request) + '\n')
            now = time.monotonic_ns()
            return dict(role=role, session=session, start_monotonic_ns=now - 1000000,
                        end_monotonic_ns=now, elapsed_seconds=.001, exit_code=0,
                        stream_complete=True, relay_complete=True)
        with patch.object(self.engine.adapter, 'record', side_effect=fake) as record:
            result = self.engine.run(root)
        self.assertEqual(record.call_count, 1)
        self.assertEqual(result['concurrency']['max_simultaneous'], 1)
        self.assertEqual(result['concurrency']['factor'], 1)
        self.assertEqual(result['result']['score'], 0)
        self.assertTrue(result['infrastructure_ok'])
        self.assertTrue(result['telemetry'][0]['thinking_disabled_verified'])


if __name__ == '__main__':
    unittest.main()
