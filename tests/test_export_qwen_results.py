import json
from pathlib import Path
import tempfile
import unittest

from experiments.export_qwen_results import operational_hashes, public_disposition, public_path, public_project, runtime_identity, summarize
from experiments import qwen_distributed_study as study


class PublicQwenResultsTests(unittest.TestCase):
    def test_native_version_is_read_from_frozen_package_not_hardcoded(self):
        with tempfile.TemporaryDirectory(prefix='qwen-runtime-identity-') as temporary:
            root = Path(temporary)
            package = root / 'runtime/lib/node_modules/@qwen-code/qwen-code/package.json'
            package.parent.mkdir(parents=True)
            package.write_text(json.dumps({'name': '@qwen-code/qwen-code', 'version': '0.24.1'}))
            self.assertEqual(runtime_identity(root), 'Qwen Code 0.24.1')
            package.write_text(json.dumps({'name': '@qwen-code/qwen-code', 'version': 'PRIVATE_RAW_CONTENT'}))
            with self.assertRaisesRegex(ValueError, 'runtime identity'):
                runtime_identity(root)

    def test_operational_artifact_allowlist_hashes_only_available_files(self):
        with tempfile.TemporaryDirectory(prefix='qwen-public-operational-') as temporary:
            batch = Path(temporary)
            permitted = batch / 'operational-receipt.json'
            permitted.write_text('{"private":"PRIVATE_RAW_CONTENT"}')
            (batch / 'credentials.json').write_text('DO_NOT_PUBLISH')
            result = operational_hashes(batch)
            self.assertEqual(result, {'operational-receipt.json': study.sha(permitted)})
            self.assertNotIn('PRIVATE_RAW_CONTENT', json.dumps(result))
            self.assertNotIn('DO_NOT_PUBLISH', json.dumps(result))
            self.assertNotIn(str(batch), json.dumps(result))

    def test_summary_keeps_failed_cost_and_cache_separate(self):
        row = {'condition': 'B', 'accepted': False, 'project_seconds': 1800,
            'concurrency': {'worker_seconds': 7000}, 'usage': {
                'input_tokens': 100, 'cached_input_tokens': 90, 'output_tokens': 20,
                'reasoning_tokens': 15, 'complete_usage': False},
            'workers': [{'timed_out': True, 'native_success': False}],
            'human_interventions': 0}
        summary = summarize([row])['B']
        self.assertEqual(summary['accepted'], 0)
        self.assertEqual(summary['median_observed_aggregate_tokens'], 120)
        self.assertFalse(summary['all_usage_complete'])
        self.assertEqual(summary['worker_timeouts'], 1)
        self.assertNotIn('time_to_accepted', summary)

    def test_public_projection_does_not_copy_raw_native_records(self):
        final = {name: 0 for name in ('setup_seconds', 'archive_seconds',
            'verification_seconds', 'project_seconds', 'human_interventions', 'external_repair_seconds')}
        final.update(accepted=False, autonomous_complete=False, concurrency={}, usage={},
            protected_inputs_changed=[], result={'groups': {'x': {'passed': False,
                'detail': 'PRIVATE_RAW_CONTENT'}}, 'failed_contracts': ['x'], 'component_checks': {
                    'orders': {'passed': False, 'tests_run': 2, 'detail': 'PRIVATE_RAW_CONTENT'}}},
            infrastructure_errors=[{'role': 'orders', 'errors': [{'event': 'transport_error',
                'type': 'IncompleteRead', 'message': 'PRIVATE_RAW_CONTENT', 'request': 1}]}])
        value = {'label': 'B1', 'condition': 'B', 'pi_behavior': None, 'result': final,
            'workers': [], 'source_changes': [], 'evidence_sha256': {},
            'native_event_hashes': {}, 'replay_sha256': 'x', 'analyzer_sha256': 'y',
            'native_profile': 'PRIVATE_RAW_CONTENT', 'replay': {
                'first_accepted_sample_seconds': None, 'durable_accepted_sample_seconds': None,
                'final_sample_matches_final_score': True, 'sampled_states': []}}
        result = public_project(value)
        self.assertNotIn('PRIVATE_RAW_CONTENT', json.dumps(result))
        self.assertEqual(result['integration_passed'], 0)
        self.assertEqual(result['failed_contracts'], ['x'])
        self.assertEqual(result['transport_observations'][0]['errors'][0]['type'], 'IncompleteRead')
        final['result'] = {'accepted': False, 'evaluation_error': 'PRIVATE_RAW_CONTENT'}
        unscored = public_project(value)
        self.assertEqual(unscored['evaluation_status'], 'unscored')
        self.assertIsNone(unscored['integration_passed'])
        self.assertIsNone(unscored['integration_total'])
        self.assertIsNone(unscored['failed_contracts'])
        self.assertTrue(unscored['evaluation_error_present'])
        self.assertFalse(unscored['final_sample_matches_final_contracts_and_local_checks'])
        self.assertNotIn('PRIVATE_RAW_CONTENT', json.dumps(unscored))
        final['accepted'] = True
        with self.assertRaisesRegex(ValueError, 'Unscored'):
            public_project(value)
        final['accepted'] = False
        value['replay'] = None
        with self.assertRaises(ValueError):
            public_project(value)

    def test_public_paths_reject_absolute_traversal_and_control_text(self):
        self.assertEqual(public_path('orders/test_orders.py'), 'orders/test_orders.py')
        for value in ('/private/file', '../private/file', 'orders/../../secret', 'orders/line\nsecret'):
            with self.assertRaises(ValueError):
                public_path(value)

    def test_disposition_versions_and_evidence_bindings(self):
        with tempfile.TemporaryDirectory(prefix='qwen-public-disposition-') as temporary:
            batch = Path(temporary)
            root = batch / 'C3'
            (root / 'catalog').mkdir(parents=True)
            profile = root / 'qwen-home/catalog/projects/work/chats/session.jsonl'
            profile.parent.mkdir(parents=True)
            for path in (root / 'result.json', root / 'plan.json', root / 'catalog/transport.jsonl',
                         root / 'catalog/events.jsonl', profile):
                path.write_text('{}\n')
            plan = {'roles': ['catalog'], 'sessions': {'catalog': 'session'}}
            workers = [{'role': 'catalog', 'timed_out': True}]
            record = {'state': 'reviewed_predetermined_timeout', 'timed_out_roles': ['catalog'],
                'controller_sha256': 'a' * 64, 'result_sha256': study.sha(root / 'result.json'),
                'plan_sha256': study.sha(root / 'plan.json'),
                'transport_sha256': {'catalog': study.sha(root / 'catalog/transport.jsonl')}}
            (batch / 'sequencing-amendment-v2.json').write_text(json.dumps({'controller_sha256': 'a' * 64}))
            (root / 'timeout-disposition-v2.json').write_text(json.dumps(record))
            self.assertEqual(public_disposition(root, plan, workers)['version'], 2)
            record.update(state='reviewed_native_stream_cancellation', classifier_sha256='b' * 64,
                native_cancellations={'catalog': {'classifier_sha256': 'b' * 64,
                    'profile_sha256': study.sha(profile), 'native_events_sha256': study.sha(root / 'catalog/events.jsonl'),
                    'matches': [{'request': 1, 'native_error_at': '1970-01-01T00:15:02Z',
                        'native_error_type': 'StreamLifetimeExceededError', 'duration_ms': 902000,
                        'transport_error_at': '1970-01-01T00:15:02.2Z', 'transport_error_type': 'BrokenPipeError',
                        'native_retry_at': '1970-01-01T00:15:02.1Z', 'followup_request': 2,
                        'private_detail': 'PRIVATE_RAW_CONTENT'}], 'private_detail': 'PRIVATE_RAW_CONTENT'}})
            (batch / 'sequencing-amendment-v3.json').write_text(json.dumps({
                'controller_sha256': 'a' * 64, 'classifier_sha256': 'b' * 64}))
            (root / 'timeout-disposition-v3.json').write_text(json.dumps(record))
            public = public_disposition(root, plan, workers)
            self.assertEqual(public['version'], 3)
            self.assertNotIn('PRIVATE_RAW_CONTENT', json.dumps(public))
            profile.write_text('changed')
            with self.assertRaisesRegex(ValueError, 'profile evidence'):
                public_disposition(root, plan, workers)
            record['transport_sha256'] = {}
            (root / 'timeout-disposition-v3.json').write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, 'coverage'):
                public_disposition(root, plan, workers)

    def test_v4_disposition_binds_prelaunch_policy_not_historical_amendment(self):
        with tempfile.TemporaryDirectory(prefix='qwen-v4-disposition-') as temporary:
            batch = Path(temporary)
            root = batch / 'B1'
            (root / 'catalog').mkdir(parents=True)
            for path in (root / 'result.json', root / 'plan.json', root / 'catalog/transport.jsonl'):
                path.write_text('{}')
            policy = {'version': 'qwen-native-boundary/v4', 'controller_sha256': 'a' * 64,
                'classifier_sha256': 'b' * 64}
            (batch / 'frozen.json').write_text(json.dumps({'sequencing_policy': policy}))
            record = {'state': 'reviewed_predetermined_timeout', 'timed_out_roles': ['catalog'],
                'policy_version': policy['version'], 'controller_sha256': policy['controller_sha256'],
                'classifier_sha256': policy['classifier_sha256'], 'native_cancellations': {},
                'result_sha256': study.sha(root / 'result.json'), 'plan_sha256': study.sha(root / 'plan.json'),
                'transport_sha256': {'catalog': study.sha(root / 'catalog/transport.jsonl')}}
            (root / 'timeout-disposition-v4.json').write_text(json.dumps(record))
            result = public_disposition(root, {'roles': ['catalog']}, [{'role': 'catalog', 'timed_out': True}])
            self.assertEqual(result['version'], 4)
            self.assertEqual(result['policy_source'], 'frozen.json')
            self.assertNotIn('amendment_sha256', result)
            policy['version'] = 'unknown'
            (batch / 'frozen.json').write_text(json.dumps({'sequencing_policy': policy}))
            with self.assertRaisesRegex(ValueError, 'frozen policy'):
                public_disposition(root, {'roles': ['catalog']}, [{'role': 'catalog', 'timed_out': True}])


if __name__ == '__main__':
    unittest.main()
