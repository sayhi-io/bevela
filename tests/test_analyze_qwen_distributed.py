import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments import analyze_qwen_distributed as analysis
from experiments import qwen_code_adapter as adapter
from experiments.export_qwen_results import public_project


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='qwen-analysis-unit-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def analyze_usage(self, transport):
        directory = self.root / 'catalog'
        directory.mkdir(exist_ok=True)
        (directory / 'events.jsonl').write_text('')
        path = directory / 'transport.jsonl'
        path.write_text('\n'.join(map(json.dumps, transport)))
        usage = adapter.usage(path)
        worker = {'role': 'catalog', 'session': 'fixture', 'started_at': '2026-01-01T00:00:00Z',
            'finished_at': '2026-01-01T00:00:01Z', 'start_monotonic_ns': 0,
            'end_monotonic_ns': 1000000000, 'elapsed_seconds': 1, 'exit_code': 0}
        plan = {'sessions': {'catalog': 'fixture'}, 'condition': 'B', 'pi_enabled': False}
        final = {name: 0 for name in ('setup_seconds', 'archive_seconds', 'verification_seconds',
            'project_seconds', 'human_interventions', 'external_repair_seconds')}
        final.update(workers=[worker], concurrency={'start_ns': 0}, accepted=False,
            autonomous_complete=False, usage=usage, protected_inputs_changed=[],
            result={'groups': {}, 'failed_contracts': [], 'component_checks': {}})
        telemetry = [{'role': 'catalog', 'session': 'fixture', 'usage': usage,
            'native_identity_verified': True, 'native_success': True}]
        for name, value in [('plan.json', plan), ('result.json', final),
                            ('worker-analysis.json', telemetry), ('before.json', {})]:
            (self.root / name).write_text(json.dumps(value))
        (self.root / 'source-history.jsonl').write_text('')
        with patch.object(analysis.study, 'verify', return_value=plan):
            result = analysis.project(self.root)
        # Synthetic replay metadata exercises only the exporter projection, not
        # a checker or historical study artifact.
        result['replay'] = {'first_accepted_sample_seconds': None,
            'durable_accepted_sample_seconds': None, 'final_sample_matches_final_score': True,
            'sampled_states': []}
        return result['workers'][0], public_project(result)

    def test_invalid_usage_never_crashes_or_exports_provider_text(self):
        for invalid in (None, [], 'PRIVATE_RAW_CONTENT', {},
                        {'prompt_tokens': 'PRIVATE_RAW_CONTENT', 'completion_tokens': '32768'},
                        {'prompt_tokens': True, 'completion_tokens': True},
                        {'prompt_tokens': -1, 'completion_tokens': -1},
                        {'prompt_tokens': 2.5, 'completion_tokens': 32768.0}):
            with self.subTest(usage=invalid):
                worker, public = self.analyze_usage([
                    {'event': 'request', 'request': 1},
                    {'event': 'usage', 'request': 1, 'usage': invalid}])
                self.assertIsNone(worker['max_observed_request_input_tokens'])
                self.assertEqual(worker['response_limit_sized_completions'], 0)
                self.assertFalse(worker['usage']['complete_usage'])
                self.assertNotIn('PRIVATE_RAW_CONTENT', json.dumps(public))

    def test_partial_and_duplicate_usage_matches_observed_request_coverage(self):
        transport = [{'event': 'request', 'request': 1}, {'event': 'request', 'request': 2},
            {'event': 'request', 'request': 3},
            {'event': 'usage', 'request': 1, 'usage': {'prompt_tokens': 50, 'completion_tokens': 32768}},
            {'event': 'usage', 'request': 1, 'usage': {'prompt_tokens': 100, 'completion_tokens': 32768}},
            {'event': 'usage', 'request': 2, 'usage': {'prompt_tokens': 'PRIVATE_RAW_CONTENT'}},
            {'event': 'usage', 'request': 3, 'usage': None},
            {'event': 'usage', 'request': 999, 'usage': {'prompt_tokens': 999999, 'completion_tokens': 32768}}]
        worker, public = self.analyze_usage(transport)
        self.assertEqual(worker['max_observed_request_input_tokens'], 100)
        self.assertEqual(worker['response_limit_sized_completions'], 1)
        self.assertEqual(worker['usage']['input_tokens'], 100)
        self.assertFalse(worker['usage']['complete_usage'])
        self.assertNotIn('PRIVATE_RAW_CONTENT', json.dumps(public))

    def test_zero_usage_is_observed_not_missing(self):
        worker, _ = self.analyze_usage([{'event': 'request', 'request': 1},
            {'event': 'usage', 'request': 1, 'usage': {'prompt_tokens': 0, 'completion_tokens': 0}}])
        self.assertEqual(worker['max_observed_request_input_tokens'], 0)
        self.assertTrue(worker['usage']['complete_usage'])

    def test_missing_event_log_is_not_zero_activity(self):
        with self.assertRaisesRegex(ValueError, 'unavailable'):
            analysis.tool_events(self.root, 'catalog', 0)

    def test_pi_alias_repair_and_event_span_preserved(self):
        directory = self.root / 'catalog'
        directory.mkdir()
        events = [dict(mono_ns=1000000000, event={'message': {'content': [
            {'type': 'tool_use', 'id': 'a', 'name': 'run_shell_command',
             'input': {'command': '$PI repair-claim --workstream CATALOG'}}]}}),
            dict(mono_ns=3000000000, event={'message': {'content': [
                {'type': 'tool_result', 'tool_use_id': 'a', 'is_error': False, 'content': 'ok'}]}})]
        (directory / 'events.jsonl').write_text('\n'.join(map(json.dumps, events)))
        calls = analysis.tool_events(self.root, 'catalog', 0)
        self.assertTrue(calls[0]['pi_tagged'])
        self.assertEqual(calls[0]['finished_seconds'] - calls[0]['seconds'], 2)

    def test_incomplete_worker_coverage_refused(self):
        (self.root / 'result.json').write_text(json.dumps({'workers': [{'role': 'a', 'session': '1'}]}))
        (self.root / 'worker-analysis.json').write_text('[]')
        with patch.object(analysis.study, 'verify', return_value={'sessions': {'a': '1'}}):
            with self.assertRaisesRegex(ValueError, 'coverage'):
                analysis.project(self.root)

    def test_replay_preserves_non_contract_rejections_and_provenance(self):
        for name in ['before.json', 'plan.json']:
            (self.root / name).write_text('{}')
        (self.root / 'check_contract.py').write_text('# frozen')
        (self.root / 'result.json').write_text(json.dumps({'concurrency': {'start_ns': 0}, 'accepted': False}))
        (self.root / 'source-history.jsonl').write_text(json.dumps({
            'mono_ns': 1, 'files': {}, 'errors': ['incomplete observed state']}) + '\n')
        with patch.object(analysis.study, 'verify'), patch.object(analysis.study.base, 'score',
            return_value={'accepted': False, 'failed_contracts': [], 'component_checks': {'catalog': {'passed': False}}}):
            value = analysis.replay(self.root)
        state = value['sampled_states'][0]
        self.assertTrue(state['observer_errors'])
        self.assertEqual(state['component_checks']['catalog']['passed'], False)
        self.assertEqual(value['provenance'], analysis.replay_provenance(self.root))
        (self.root / 'check_contract.py').write_text('# changed')
        self.assertNotEqual(value['provenance'], analysis.replay_provenance(self.root))


if __name__ == '__main__':
    unittest.main()
