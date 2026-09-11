import json
from pathlib import Path
import tempfile
import shutil
import threading
import time
import unittest
from unittest.mock import patch

from experiments import qwen_seven_seams as study

SOURCE = Path(__file__).resolve().parents[1]


class QwenSevenTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name)
        self.runtime = self.parent / 'runtime'
        self.runtime.mkdir()
        (self.runtime / 'dummy').write_text('test-only native runtime')
        (self.runtime/'bin').mkdir()
        (self.runtime/'bin/qwen').write_text('console.log("0.23.2");\n')

    def prepare(self, condition='B'):
        return study.prepare(self.parent / condition, condition, SOURCE, self.runtime,
                             'http://127.0.0.1:8078/v1', timeout=5)

    def test_original_fixture_and_prompts_unchanged_in_both_arms(self):
        for condition in ('B', 'C'):
            root = self.prepare(condition)
            plan = study.verify(root, before=True)
            for name, value in plan['fixture_manifest'].items():
                self.assertEqual(study.manifest(root / 'work')[name], value)
            for role in study.ROLES:
                self.assertEqual((root / (role+'.txt')).read_bytes(),
                    (study.common.original.ASSETS / (role+'.txt')).read_bytes())
            self.assertEqual(study.sha(root/'check_contract.py'), study.sha(SOURCE/'experiments/seven_seams_check.py'))
            self.assertFalse((root/'work/tasks').exists())
            self.assertEqual(plan['server_effort'], 'medium')
            settings = json.loads((root/'settings-template.json').read_text())
            self.assertEqual(settings['modelProviders']['openai'][0]['generationConfig']['extra_body']['reasoning_effort'], 'medium')
            self.assertEqual(len(set(plan['sessions'].values())), 2)

    def test_control_no_pi_and_treatment_no_historical_results(self):
        ordinary, aware = self.prepare('B'), self.prepare('C')
        self.assertFalse((ordinary/'pi-source').exists())
        self.assertFalse((ordinary/'work/.pi').exists())
        self.assertFalse((ordinary/'work/AGENTS.md').exists())
        self.assertNotIn('SEVEN SEAMS', (aware/'pi-source/README.md').read_text())
        self.assertFalse((aware/'pi-source/docs/results').exists())
        agents = (aware/'work/AGENTS.md').read_text()
        self.assertIn('/usr/bin/python3', agents)
        self.assertIn('QWEN_SESSION_ID', agents)
        self.assertNotIn('CODEX_THREAD_ID', agents)
        self.assertNotIn(study.common.COMMON, agents)
        inventory = json.loads((aware/'work/.pi/snapshot.json').read_text())
        self.assertEqual({r['id'] for r in inventory['records']}, {'PRODUCER','CONSUMER'})

    def test_real_no_model_isolation_and_pi_cli_preflight(self):
        for condition in ('B', 'C'):
            study.preflight(self.prepare(condition))

    def test_same_checker_runs_inside_isolated_copy(self):
        root=self.prepare()
        shutil.copytree(root/'work',root/'after',ignore=shutil.ignore_patterns('.git'))
        before=study.manifest(root/'after')
        result=study.score(root)
        self.assertEqual(result['score'],0)
        self.assertEqual(result['out_of'],7)
        self.assertEqual(study.manifest(root/'after'),before)

    def test_wrong_native_version_refused_before_models(self):
        (self.runtime/'bin/qwen').write_text('console.log("wrong");\n')
        with self.assertRaises(RuntimeError):
            study.preflight(self.prepare())

    def test_frozen_input_and_nonfresh_home_refused(self):
        root = self.prepare()
        (root/'qwen-home/producer/settings.json').write_text('{}')
        with self.assertRaises(ValueError):
            study.verify(root,before=True)
        (root/'producer.txt').write_text('changed')
        with self.assertRaises(ValueError):
            study.verify(root)

    def row(self, root, effort='medium', timed_out=False):
        plan = study.verify(root)
        folder = root/'producer'
        folder.mkdir(exist_ok=True)
        session = plan['sessions']['producer']
        events = [dict(type='system', subtype='init', model=study.MODEL, session_id=session),
                  dict(type='result', subtype='success', session_id=session)]
        (folder/'stdout.jsonl').write_text('\n'.join(json.dumps(e) for e in events)+'\n')
        request = dict(event='request', request=1, model=study.MODEL, reasoning_effort=effort,
            chat_template_kwargs={'enable_thinking':True}, max_tokens=32768)
        (folder/'transport.jsonl').write_text(json.dumps(request)+'\n')
        return dict(role='producer',session=session,start_monotonic_ns=0,timed_out=timed_out), plan

    def test_actual_medium_controls_and_uuid_not_assumed(self):
        root=self.prepare()
        row,plan=self.row(root)
        self.assertTrue(study.telemetry(root,row,plan)['controls_verified'])
        row,plan=self.row(root,effort='xhigh')
        self.assertFalse(study.telemetry(root,row,plan)['controls_verified'])
        row['session']='wrong'
        self.assertFalse(study.telemetry(root,row,plan)['initialization_verified'])

    def test_timeout_cleanup_not_general_transport_amnesty(self):
        root=self.prepare()
        row,plan=self.row(root,timed_out=True)
        path=root/'producer/transport.jsonl'
        with path.open('a') as stream:
            for stamp in (1, 5_000_000_001):
                stream.write(json.dumps(dict(event='transport_error', mono_ns=stamp, type='ConnectionResetError'))+'\n')
        evidence=study.telemetry(root,row,plan)
        self.assertEqual(len(evidence['transport_errors']),2)
        self.assertEqual(len(evidence['unexpected_transport_errors']),1)

    def test_sequential_batch_no_retry(self):
        batch=self.parent/'batch'
        with patch.object(study,'preflight'):
            study.freeze(batch,SOURCE,self.runtime,'http://127.0.0.1:8078/v1',timeout=5)
        calls=[]
        def fake(root):
            calls.append(root.parent.name)
            return dict(result={'score':0},accepted=False,project_seconds=1,workers=[],infrastructure_ok=True)
        with patch.object(study,'run',side_effect=fake):
            study.run_all(batch)
            self.assertEqual(calls,list(study.ORDER))
            with self.assertRaises(FileExistsError):
                study.run_all(batch)
        self.assertEqual(len(calls),6)

    def test_infrastructure_error_stops_next_project(self):
        batch=self.parent/'batch'
        with patch.object(study,'preflight'):
            study.freeze(batch,SOURCE,self.runtime,'http://127.0.0.1:8078/v1',timeout=5)
        with patch.object(study,'run',return_value=dict(result={'score':0},accepted=False,
                project_seconds=1,workers=[],infrastructure_ok=False)) as launch:
            with self.assertRaises(RuntimeError):
                study.run_all(batch)
            self.assertEqual(launch.call_count,1)

    def concurrent_result(self,omit_final=False):
        root=self.prepare()
        barrier=threading.Barrier(2)
        completed=[]
        def record(root,role,plan,observer):
            folder=root/role
            folder.mkdir()
            session=plan['sessions'][role]
            events=[dict(type='system',subtype='init',model=study.MODEL,session_id=session),
                    dict(type='result',subtype='success',session_id=session)]
            if omit_final:
                events.pop()
            (folder/'stdout.jsonl').write_text('\n'.join(json.dumps(e) for e in events)+'\n')
            request=dict(event='request',request=1,model=study.MODEL,reasoning_effort='medium',
                chat_template_kwargs={'enable_thinking':True},max_tokens=32768)
            (folder/'transport.jsonl').write_text(json.dumps(request)+'\n')
            start=time.monotonic_ns()
            barrier.wait(timeout=5)  # Unit-test assertion only, not a worker barrier.
            completed.append(role)
            return dict(role=role,session=session,start_monotonic_ns=start,end_monotonic_ns=time.monotonic_ns(),
                exit_code=0,stream_complete=True,relay_complete=True)
        def score(root):
            self.assertEqual(set(completed),set(study.ROLES))
            return {'score':0,'out_of':7}
        with patch.object(study.adapter,'record',side_effect=record) as launch, patch.object(study,'score',side_effect=score):
            result=study.run(root)
            self.assertEqual(launch.call_count,2)
            self.assertEqual(result['concurrency']['max_simultaneous'],2)
            self.assertEqual(result['infrastructure_ok'],not omit_final)
            self.assertFalse(result['accepted'])
            with self.assertRaises(FileExistsError):
                study.run(root)
            self.assertEqual(launch.call_count,2)

    def test_two_workers_overlap_and_checker_waits_for_both(self):
        self.concurrent_result()

    def test_non_timeout_missing_terminal_evidence_is_infrastructure_failure(self):
        self.concurrent_result(omit_final=True)


if __name__ == '__main__':
    unittest.main()
