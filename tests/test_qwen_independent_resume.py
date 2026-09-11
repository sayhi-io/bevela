import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments import qwen_independent_resume as resume


class ResumeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.plan = dict(model=resume.study.MODEL, pi_enabled=False,
            sessions={'money': 'session-money'})
        settings = resume.study.runner(False).adapter.settings(resume.study.MODEL, 'http://127.0.0.1:12345/v1')
        self.put('settings-template.json', settings)
        self.put('qwen-home/money/settings.json', settings)
        self.put('plan.json', self.plan)
        self.put('money/command.json', ['native-qwen'])
        self.native = dict(role='money', session='session-money', initialization_verified=True,
            final_identity_mismatch=False, final_identity_verified=True, transport_errors=[],
            thinking_disabled_verified=True, controls_verified=False, native_success=True)
        self.put('worker-analysis.json', [self.native])
        self.result = dict(accepted=True, autonomous_complete=False, result={'accepted': True},
            protected_inputs_changed=[], infrastructure_errors=[dict(role='money', errors=[resume.IDENTITY_ERROR])],
            workers=[dict(role='money', session='session-money', relay_complete=True, stream_complete=True,
                stream_eof=True, stream_error_type=None, exit_code=0)])
        self.put('result.json', self.result)
        self.request = dict(event='request', request=1, at='now', model=resume.study.MODEL,
            reasoning_effort='medium', chat_template_kwargs={'enable_thinking': False}, max_tokens=25106)
        self.put('money/transport.jsonl', self.request)

    def put(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value) + '\n')

    def test_lower_budget_is_observer_only_correction(self):
        before = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result = resume.audit(self.root, self.plan)
        self.assertTrue(result['audited_autonomous_complete'])
        self.assertFalse(result['original_autonomous_complete'])
        self.assertEqual(result['correction_roles'], ['money'])
        self.assertEqual(result['workers']['money']['reduced_output_budgets'][0]['max_tokens'], 25106)
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_bad_budget_model_or_reasoning_never_accepted(self):
        for change in ({'max_tokens': 32769}, {'max_tokens': 0}, {'max_tokens': True}, {'max_tokens': None},
                       {'max_tokens': 2.5}, {'model': 'different'}, {'reasoning_effort': 'high'},
                       {'chat_template_kwargs': {'enable_thinking': True}}):
            with self.subTest(change=change):
                self.put('money/transport.jsonl', {**self.request, **change})
                with self.assertRaises(ValueError):
                    resume.audit(self.root, self.plan)

    def test_unrelated_failure_or_changed_native_settings_refused(self):
        for field, value in (('initialization_verified', False), ('final_identity_mismatch', True),
                             ('thinking_disabled_verified', False), ('transport_errors', ['unexpected'])):
            self.put('worker-analysis.json', [{**self.native, field: value}])
            with self.assertRaises(ValueError):
                resume.audit(self.root, self.plan)
        self.put('worker-analysis.json', [self.native])
        settings = resume.study.read(self.root / 'qwen-home/money/settings.json')
        settings['model']['maxSessionTurns'] = 501
        self.put('qwen-home/money/settings.json', settings)
        with self.assertRaises(ValueError):
            resume.audit(self.root, self.plan)

    def test_native_failure_not_reclassified_as_success(self):
        self.put('worker-analysis.json', [{**self.native, 'native_success': False}])
        result = copy.deepcopy(self.result)
        result['workers'][0]['exit_code'] = 1
        self.put('result.json', result)
        self.assertFalse(resume.audit(self.root, self.plan)['audited_autonomous_complete'])

    def test_partial_recording_and_unrelated_infrastructure_refused(self):
        for field, value in (('relay_complete', False), ('stream_complete', False)):
            result = copy.deepcopy(self.result)
            result['workers'][0][field] = value
            self.put('result.json', result)
            with self.assertRaises(ValueError):
                resume.audit(self.root, self.plan)
        self.put('result.json', {**self.result, 'infrastructure_errors': [{'role': 'money', 'errors': ['other']}]})
        with self.assertRaises(ValueError):
            resume.audit(self.root, self.plan)

    def test_native_success_without_clamping_also_supported(self):
        self.put('money/transport.jsonl', {**self.request, 'max_tokens': 32768})
        self.put('worker-analysis.json', [{**self.native, 'controls_verified': True}])
        self.put('result.json', {**self.result, 'autonomous_complete': True, 'infrastructure_errors': []})
        result = resume.audit(self.root, self.plan)
        self.assertTrue(result['audited_autonomous_complete'])
        self.assertEqual(result['correction_roles'], [])

    def test_continuation_queues_only_five_in_original_order_and_refuses_replay(self):
        batch = self.root / 'batch'
        batch.mkdir()
        self.put('batch/frozen.json', {})
        self.put('batch/stopped.json', {'label': 'A1'})
        self.put('batch/A1/plan.json', {})
        audited = dict(accepted=True, audited_autonomous_complete=True)
        calls = []
        class FakeEngine:
            def run(self, root):
                calls.append(root.name)
                resume.study.original.write_json(root / 'plan.json', {})
                return dict(accepted=True, result={'groups': {}}, project_seconds=1)
        for label in resume.REMAINING:
            (batch / label).mkdir()
        with patch.object(resume, 'verify_cohort'), patch.object(resume, 'audit', return_value=audited), \
             patch.object(resume.study, 'runner', return_value=FakeEngine()):
            resume.freeze(batch)
            resume.run(batch)
            with self.assertRaises(FileExistsError):
                resume.run(batch)
        self.assertEqual(calls, ['B1', 'B2', 'A2', 'A3', 'B3'])
        self.assertFalse((batch / 'A1/started.json').exists())


if __name__ == '__main__':
    unittest.main()
