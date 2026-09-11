import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments import qwen_profiles as profiles
from experiments import qwen_seven_seams as original
from experiments import qwen_code_adapter as native

SOURCE = Path(__file__).resolve().parents[1]


class QwenProfilesTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.runtime = self.root / 'runtime'
        (self.runtime / 'bin').mkdir(parents=True)
        (self.runtime / 'bin/qwen').write_text('console.log("0.23.2");\n')

    def prepare(self, **overrides):
        engine = profiles.runner({**profiles.DEFAULT, **overrides})
        root = engine.prepare(self.root / 'trial', 'C' if overrides.get('pi', True) else 'B',
            SOURCE, self.runtime, 'http://127.0.0.1:8078/v1', timeout=5)
        return engine, root

    def test_bad_controls_and_high_rejected(self):
        for values in ({'effort':'high'}, {'effort':'xhigh'}, {'thinking':0},
                       {'runs':True}, {'runs':0}, {'context':262144},
                       {'thinking':False, 'confidence':True}, {'unknown':True}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                profiles.validate({**profiles.DEFAULT, **values})

    def test_settings_no_leftover_high_and_toggles(self):
        for thinking in (True, False):
            p = {**profiles.DEFAULT, 'thinking':thinking, 'confidence':False}
            s = profiles.settings(p, original.MODEL, 'http://localhost:8078/v1')
            self.assertEqual(s['model']['reasoningEffort'], 'medium' if thinking else 'none')
            wire = s['modelProviders']['openai'][0]['generationConfig']['extra_body']
            self.assertEqual(wire['reasoning_effort'], 'medium')
            self.assertIs(wire['chat_template_kwargs']['enable_thinking'], thinking)

    def test_historical_modules_not_mutated_and_profiles_isolated(self):
        settings, prepare, order = native.settings, original.prepare, original.ORDER
        on = profiles.runner(profiles.DEFAULT)
        off = profiles.runner({**profiles.DEFAULT, 'thinking':False,'confidence':False})
        self.assertIs(native.settings, settings)
        self.assertIs(original.prepare, prepare)
        self.assertEqual(original.ORDER, order)
        self.assertEqual(on.ORDER, ('C1',))
        self.assertIsNot(on.adapter, off.adapter)
        self.assertNotEqual(on.adapter.settings(original.MODEL,'http://localhost/v1'),
                            off.adapter.settings(original.MODEL,'http://localhost/v1'))

    def test_fixture_checker_and_pi_unchanged_only_prompt_suffix(self):
        engine, root = self.prepare()
        plan = engine.verify(root, before=True)
        self.assertEqual(plan['qwen_profile'], profiles.DEFAULT)
        for name,value in plan['fixture_manifest'].items():
            self.assertEqual(engine.manifest(root/'work')[name], value)
        self.assertEqual(engine.sha(root/'check_contract.py'), engine.sha(SOURCE/'experiments/seven_seams_check.py'))
        for role in engine.ROLES:
            expected=(original.common.original.ASSETS/(role+'.txt')).read_text().rstrip()+'\n\n'+profiles.CONFIDENCE+'\n'
            self.assertEqual((root/(role+'.txt')).read_text(),expected)
        self.assertEqual(engine.manifest(root/'pi-source/project_intent'), engine.manifest(SOURCE/'project_intent',ignore_cache=True))

    def test_original_prompt_when_disabled_and_real_no_model_preflight(self):
        engine, root = self.prepare(thinking=False, confidence=False)
        for role in engine.ROLES:
            self.assertEqual((root/(role+'.txt')).read_bytes(), (original.common.original.ASSETS/(role+'.txt')).read_bytes())
        engine.preflight(root)

    def test_changed_profile_or_inputs_refused(self):
        engine, root = self.prepare()
        plan=json.loads((root/'plan.json').read_text())
        plan['qwen_profile']['confidence']=False
        (root/'plan.json').write_text(json.dumps(plan))
        with self.assertRaises(ValueError):engine.verify(root)

    def test_one_project_only_and_replay_refused(self):
        engine=profiles.runner(profiles.DEFAULT)
        batch=self.root/'batch'
        with patch.object(engine,'preflight'):
            engine.freeze(batch,SOURCE,self.runtime,'http://127.0.0.1:8078/v1',timeout=5)
        with patch.object(engine,'run',return_value=dict(result={'score':0},accepted=False,
                project_seconds=1,workers=[],infrastructure_ok=True)) as launch:
            engine.run_all(batch)
            self.assertEqual(launch.call_count,1)
            with self.assertRaises(FileExistsError):engine.run_all(batch)

    def test_actual_off_wire_and_reasoning_leak_fenced(self):
        engine,root=self.prepare(thinking=False,confidence=False)
        plan=engine.verify(root); session=plan['sessions']['producer']
        folder=root/'producer';folder.mkdir()
        (folder/'stdout.jsonl').write_text(json.dumps(dict(type='system',subtype='init',model=engine.MODEL,session_id=session))+'\n')
        request=dict(event='request',request=1,model=engine.MODEL,reasoning_effort='medium',
            chat_template_kwargs={'enable_thinking':False},max_tokens=32768)
        path=folder/'transport.jsonl';path.write_text(json.dumps(request)+'\n')
        row=dict(role='producer',session=session,start_monotonic_ns=0)
        self.assertTrue(engine.telemetry(root,row,plan)['controls_verified'])
        path.write_text(path.read_text()+json.dumps(dict(event='reasoning_observed',request=1,characters=2))+'\n')
        self.assertFalse(engine.telemetry(root,row,plan)['controls_verified'])


if __name__ == '__main__':
    unittest.main()
