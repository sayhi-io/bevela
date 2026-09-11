"""Synthetic JSON only: no study runner, candidate execution or native processes."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments import distributed_analysis as export


class DistributedAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='distributed-export-unit-')
        self.addCleanup(self.temp.cleanup)
        self.study = Path(self.temp.name)
        self.batch = self.study / 'batch'
        self.batch.mkdir()
        self.root = self.study / 'completed'
        self.root.mkdir()
        self.running = self.study / 'running'
        self.running.mkdir()
        self.future = self.study / 'future'
        self.future.mkdir()
        self.roles = ['catalog', 'orders']
        self.secret = '/home/private/SECRET/00000000-0000-4000-8000-000000000001'
        self.plan = {'condition': 'B', 'roles': self.roles, 'model': 'gpt-5.6-sol',
                     'effort': 'medium', 'pi_enabled': False, 'pi_commit': 'a' * 40,
                     'before_sha256': 'b' * 64, 'own_recorder_sha256': 'c' * 64,
                     'input_hashes': {'catalog.txt': 'd' * 64}}
        self.plan_sha = self.write(self.root / 'plan.json', self.plan)
        self.processes = [{'role': r, 'started_at': '2026-09-09T08:00:00+00:00',
                           'finished_at': '2026-09-09T08:00:10+00:00',
                           'elapsed_seconds': 10, 'exit_code': 0, 'stream_complete': True}
                          for r in self.roles]
        self.result = {'condition': 'B', 'accepted': True, 'autonomous_complete': True,
            'native_identity_verified': True, 'workers': self.processes,
            'setup_seconds': 0.2, 'archive_seconds': 0.3, 'verification_seconds': 0.4,
            'project_seconds': 10.7,
            'result': {'groups': {'money_and_quotes': {'passed': True}},
                       'component_checks': {'catalog': {'passed': True, 'tests_run': 2,
                                                        'errors': 0, 'failures': 0}},
                       'failed_contracts': []},
            'concurrency': {'worker_interval_seconds': 10, 'worker_seconds': 20,
                            'factor': 2, 'max_simultaneous': 2,
                            'active_timeline': [{'seconds': 0, 'active': 2},
                                                {'seconds': 10, 'active': 0}]}}
        self.telemetry = [{'role': r, 'native_contexts': [['gpt-5.6-sol', 'medium']],
            'native_sha256': 'e' * 64, 'native_tool_call_count': 4,
            'tokens': {'input_tokens': 100, 'cached_input_tokens': 80, 'cache_write_input_tokens': 0,
                       'output_tokens': 20, 'reasoning_output_tokens': 5, 'total_tokens': 120},
            'start_seconds': 0, 'end_seconds': 10,
            'pi_native_calls': [{'output_bytes': 3, 'input': self.secret, 'output': self.secret}],
            'pi_command_candidates': 2, 'pi_native_tool_seconds': 0.15, 'pi_output_bytes': 5,
            'pi_failed_commands': 1, 'pi_operation_candidate_counts': {'enroll': 1},
            'enrollment_completed_seconds': 2, 'onboarding_observed_span_seconds': 1.5,
            'patch_calls': [{'input': self.secret, 'output': self.secret, 'call_id': self.secret}],
            'edits': [{'status': 'completed', 'changes': [
                {'path': str(self.root / 'work' / r / '__init__.py'), 'kind': 'update'}]}]}
            for r in self.roles]
        self.write(self.running / 'started.json', {'secret': self.secret})
        self.write(self.running / 'plan.json', {'secret': self.secret})
        self.write(self.future / 'plan.json', {'secret': self.secret})
        self.manifest = {'acceptance.py': {'sha256': '1' * 64}}
        self.freeze = {'stage': 'calibration', 'at': '2026-09-09T07:00:00Z',
            'code_manifest': {'experiments/distributed_study.py': {'sha256': '2' * 64}},
            'fixture_manifest': self.manifest, 'tests_manifest': {},
            'trials': [{'label': 'B1', 'root': str(self.root), 'plan_sha256': self.plan_sha},
                       {'label': 'B2', 'root': str(self.running), 'plan_sha256': '3' * 64},
                       {'label': 'B3', 'root': str(self.future), 'plan_sha256': '4' * 64}]}
        self.save_freeze()
        self.write(self.root / 'replay.json', {'first_accepted_sample_seconds': 5,
            'durable_accepted_sample_seconds': 6, 'final_sample_matches_final_score': True,
            'sampled_states': [{'accepted': False, 'evaluation_error': self.secret},
                               {'accepted': True}]})
        self.save_completed()

    @staticmethod
    def write(path, value):
        raw = json.dumps(value).encode()
        path.write_bytes(raw)
        return hashlib.sha256(raw).hexdigest()

    def save_freeze(self):
        freeze_sha = self.write(self.batch / 'freeze.json', self.freeze)
        record = {'path': str(self.batch), 'freeze_sha256': freeze_sha,
                  'fixture_manifest': self.manifest, 'checker_sha256': '1' * 64}
        self.registry = {'batches': [record], 'candidates': [record], 'ceiling': None,
                         'evaluation': None, 'pi_manifest': {}, 'codex_entry_sha256': '5' * 64}
        self.write(self.study / 'study.json', self.registry)

    def save_completed(self, review=True):
        result_sha = self.write(self.root / 'result.json', self.result)
        analysis_sha = self.write(self.root / 'worker-analysis.json', self.telemetry)
        if review:
            self.write(self.batch / 'B1-review.json', {'result_sha256': result_sha,
                'analysis_sha256': analysis_sha, 'history_sha256': '6' * 64,
                'native_sha256': {r: 'e' * 64 for r in self.roles},
                'infrastructure_failure': False, 'integrity_failure': False,
                'rationale': self.secret})

    def row(self):
        return export.collect(self.study)['batches'][0]['projects'][0]

    def test_metrics_outcomes_and_token_subsets(self):
        row = self.row()
        self.assertEqual(row['status'], 'completed_reviewed')
        self.assertTrue(row['accepted'])
        self.assertTrue(row['autonomous_complete'])
        self.assertEqual(row['tokens_last_observed_sum'], {
            'input_tokens': 200, 'cached_input_tokens': 160, 'cache_write_input_tokens': 0,
            'output_tokens': 40, 'reasoning_output_tokens': 10, 'total_tokens': 240})
        self.assertEqual(row['timing']['project_seconds'], 10.7)
        self.assertEqual(row['replay']['durable_accepted_sample_seconds'], 6)
        self.assertEqual(row['replay']['evaluation_error_state_count'], 1)
        self.assertEqual(row['concurrency']['active_intervals'], [
            {'start_seconds': 0, 'end_seconds': 10, 'active': 2}])
        self.assertEqual(row['outcomes']['components'][0]['tests_run'], 2)
        tool = row['workers'][0]['tools']
        self.assertEqual(tool['pi_tagged_native_output_bytes'], 3)
        self.assertEqual(tool['pi_tagged_command_output_bytes'], 5)
        self.assertEqual(tool['onboarding_observed_span_seconds'], 1.5)

    def test_never_reads_unfinished_or_native_or_candidate_files(self):
        original = Path.read_bytes
        allowed = {self.study / 'study.json', self.batch / 'freeze.json', self.batch / 'B1-review.json'}
        allowed.update(self.root / n for n in ['plan.json', 'result.json', 'worker-analysis.json', 'replay.json'])
        reads = []
        def guarded(path):
            self.assertIn(path, allowed)
            reads.append(path)
            return original(path)
        with patch.object(Path, 'read_bytes', guarded):
            data = export.collect(self.study)
        self.assertTrue(reads)
        self.assertEqual([r['status'] for r in data['batches'][0]['projects']],
                         ['completed_reviewed', 'unfinished', 'not_run'])
        self.assertEqual(data['stages_allocated'], {'calibration': True, 'ceiling': False, 'evaluation': False})

    def test_private_text_and_unknown_fields_cannot_escape(self):
        self.result['result']['groups'][self.secret] = {'passed': False, 'details': self.secret}
        self.result['result']['component_checks']['catalog']['stderr'] = self.secret
        self.result['result']['evaluation_error'] = self.secret
        self.result['result']['failed_contracts'] = [self.secret]
        self.telemetry[0].update(sessions=[self.secret], native_log=self.secret,
                                 commands=[self.secret], agent_messages=[self.secret])
        self.telemetry[0]['pi_operation_candidate_counts'][self.secret] = 100
        self.telemetry[0]['edits'][0]['changes'] += [{'path': self.secret},
            {'path': str(self.root / 'work/.pi/auth.json')}, {'path': '../outside.py'}]
        self.save_completed()
        data = export.collect(self.study)
        text = json.dumps(data)
        self.assertNotIn('SECRET', text)
        self.assertNotIn(str(self.study), text)
        self.assertNotIn('01a0855d', text)
        edits = data['batches'][0]['projects'][0]['workers'][0]['edits']
        self.assertEqual(edits['reported_relative_paths'], ['catalog/__init__.py'])
        self.assertEqual(edits['omitted_path_entries'], 3)

    def test_missing_token_fields_remain_unknown_in_totals(self):
        self.telemetry[1]['tokens'] = {'input_tokens': 90}
        self.save_completed()
        row = self.row()
        self.assertEqual(row['tokens_last_observed_sum']['input_tokens'], 190)
        self.assertIsNone(row['tokens_last_observed_sum']['cached_input_tokens'])
        self.assertIsNone(row['tokens_last_observed_sum']['total_tokens'])

    def test_missing_worker_analysis_not_zero_filled(self):
        self.telemetry.pop()
        self.save_completed()
        row = self.row()
        self.assertIsNone(row['tokens_last_observed_sum']['input_tokens'])
        self.assertIsNone(row['workers'][1]['tools']['native_paired_call_count'])
        self.assertIsNone(row['workers'][1]['edits']['patch_call_candidates'])

    def test_timeout_keeps_source_acceptance_separate(self):
        self.result['workers'][0].update(timed_out=True, exit_code=-15)
        self.result['autonomous_complete'] = False
        self.save_completed()
        row = self.row()
        self.assertTrue(row['accepted'])
        self.assertFalse(row['autonomous_complete'])
        self.assertTrue(row['token_totals_include_partial_timeout'])
        self.assertEqual(row['workers'][0]['token_usage_status'], 'partial_timeout')

    def test_unreviewed_completed_case_not_silently_dropped(self):
        (self.batch / 'B1-review.json').unlink()
        self.assertEqual(self.row()['status'], 'completed_unreviewed')

    def test_partial_json_preserves_incomplete_status(self):
        (self.root / 'result.json').write_text('{')
        row = self.row()
        self.assertEqual(row['status'], 'recording_incomplete')
        self.assertIsNone(row['accepted'])

    def test_mismatched_review_rejected(self):
        self.result['accepted'] = False
        self.save_completed(review=False)
        with self.assertRaisesRegex(export.ExportError, 'review binding'):
            self.row()

    def test_native_digest_declarations_must_agree_without_log_reads(self):
        self.telemetry[0]['native_sha256'] = 'f' * 64
        self.save_completed()
        with self.assertRaisesRegex(export.ExportError, 'Native digest'):
            self.row()

    def test_non_object_review_is_not_treated_as_reviewed(self):
        self.write(self.batch / 'B1-review.json', [self.secret])
        self.assertEqual(self.row()['status'], 'completed_unreviewed')

    def test_manifest_paths_are_allowlisted(self):
        self.freeze['code_manifest'].update({self.secret: {'sha256': 'f' * 64},
            '../outside.py': {'sha256': 'f' * 64}, 'auth.json': {'sha256': 'f' * 64}})
        self.save_freeze()
        hashes = export.collect(self.study)['batches'][0]['provenance']['code_sha256_declared']
        self.assertEqual(list(hashes), ['experiments/distributed_study.py'])

    def test_mismatched_plan_and_freeze_rejected(self):
        self.write(self.root / 'plan.json', {'different': True})
        with self.assertRaisesRegex(export.ExportError, 'plan digest'):
            self.row()
        self.write(self.batch / 'freeze.json', {'different': True})
        with self.assertRaisesRegex(export.ExportError, 'freeze digest'):
            self.row()

    def test_candidate_is_from_registry_not_directory_suffix(self):
        self.registry['candidates'].insert(0, {'path': 'other', 'fixture_manifest': {}})
        self.write(self.study / 'study.json', self.registry)
        self.assertEqual(export.collect(self.study)['batches'][0]['candidate'], 2)

    def test_numeric_strings_booleans_and_nonfinite_are_not_metrics(self):
        self.telemetry[0]['tokens'].update(input_tokens=True, output_tokens='private', total_tokens=float('inf'))
        self.result['project_seconds'] = float('nan')
        self.save_completed()
        row = self.row()
        self.assertIsNone(row['tokens_last_observed_sum']['input_tokens'])
        self.assertIsNone(row['tokens_last_observed_sum']['output_tokens'])
        self.assertIsNone(row['timing']['project_seconds'])
        json.dumps(row, allow_nan=False)

    def test_stdout_only_json_and_no_artifact_mutations(self):
        before = {p: p.read_bytes() for p in self.study.rglob('*') if p.is_file()}
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            export.main(['--study', str(self.study)])
        json.loads(out.getvalue())
        after = {p: p.read_bytes() for p in self.study.rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_cli_errors_do_not_disclose_private_root(self):
        error = io.StringIO()
        with contextlib.redirect_stderr(error), self.assertRaises(SystemExit):
            export.main(['--study', str(self.study / 'PRIVATE-MISSING')])
        self.assertNotIn('PRIVATE-MISSING', error.getvalue())
        self.assertNotIn(str(self.study), error.getvalue())


class DistributedPublicationTests(unittest.TestCase):
    def test_published_candidate1_keeps_every_project_and_worker(self):
        root = Path(__file__).resolve().parents[1]
        data = json.loads((root / 'docs/results/sol-distributed-measurements.json').read_text())
        batch, = [b for b in data['batches'] if b['stage'] == 'calibration' and b['candidate'] == 1]
        rows = batch['projects']
        self.assertEqual([r['label'] for r in rows], ['B1', 'B2', 'B3'])
        self.assertEqual([r['tokens_last_observed_sum']['total_tokens'] for r in rows],
                         [1469382, 1893107, 1488668])
        for row in rows:
            self.assertTrue(row['accepted'])
            self.assertTrue(row['autonomous_complete'])
            self.assertEqual(row['model'], 'gpt-5.6-sol')
            self.assertEqual(row['effort'], 'medium')
            self.assertFalse(row['pi_enabled'])
            self.assertEqual({w['role'] for w in row['workers']},
                             {'catalog', 'orders', 'settlement', 'reporting'})
            self.assertEqual(len(row['outcomes']['groups']), 12)
            self.assertTrue(all(g['passed'] for g in row['outcomes']['groups']))
            self.assertAlmostEqual(sum(w['duration_seconds'] for w in row['workers']),
                                   row['concurrency']['worker_seconds'])
            for name in export.TOKEN_KEYS:
                self.assertEqual(sum(w['tokens'][name] for w in row['workers']),
                                 row['tokens_last_observed_sum'][name])

    def test_completed_calibration_stops_without_invented_evaluation(self):
        root = Path(__file__).resolve().parents[1]
        data = json.loads((root / 'docs/results/sol-distributed-measurements.json').read_text())
        self.assertEqual(len(data['batches']), 2)
        self.assertEqual({b['stage'] for b in data['batches']}, {'calibration'})
        batch, = [b for b in data['batches'] if b['candidate'] == 2]
        rows = batch['projects']
        self.assertEqual([r['label'] for r in rows], ['B1', 'B2', 'B3'])
        self.assertEqual([r['tokens_last_observed_sum']['total_tokens'] for r in rows],
                         [2629461, 3139955, 2965664])
        for row in rows:
            self.assertEqual(row['status'], 'completed_reviewed')
            self.assertTrue(row['accepted'])
            self.assertTrue(row['autonomous_complete'])
            self.assertFalse(row['pi_enabled'])
            self.assertEqual(row['model'], 'gpt-5.6-sol')
            self.assertEqual(row['effort'], 'medium')
            self.assertEqual(len(row['workers']), 4)
            self.assertEqual(len(row['outcomes']['groups']), 15)
            self.assertTrue(all(g['passed'] for g in row['outcomes']['groups']))
            self.assertAlmostEqual(sum(w['duration_seconds'] for w in row['workers']),
                                   row['concurrency']['worker_seconds'])
            for name in export.TOKEN_KEYS:
                self.assertEqual(sum(w['tokens'][name] for w in row['workers']),
                                 row['tokens_last_observed_sum'][name])

    def test_published_ledger_has_no_private_execution_material(self):
        root = Path(__file__).resolve().parents[1]
        text = (root / 'docs/results/sol-distributed-measurements.json').read_text()
        self.assertNotRegex(text, r'/home/|/tmp/|Bearer |-----BEGIN|"(?:root|pid|session|native_log|commands|agent_messages)"')
        self.assertNotRegex(text, r'[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}')


if __name__ == '__main__':
    unittest.main()
