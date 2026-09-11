import copy
import json
import unittest
from unittest.mock import patch

from experiments import qwen_independent_timeout_resume as route
from tests import test_qwen_independent_resume as earlier


class TimeoutTests(unittest.TestCase):
    setUp = earlier.ResumeTests.setUp
    put = earlier.ResumeTests.put

    def timeout(self):
        self.plan['timeout_seconds'] = 1800
        self.put('plan.json', self.plan)
        start, cutoff = 1000000000, 1801000000000
        worker = self.result['workers'][0]
        worker.update(timed_out=True, exit_code=-15, start_monotonic_ns=start,
            end_monotonic_ns=cutoff + 200000000, elapsed_seconds=1800.2)
        request = {**self.request, 'mono_ns': cutoff - 2000000000}
        response = dict(event='response', request=1, mono_ns=cutoff - 1000000000, status=200)
        error = dict(event='transport_error', request=1, mono_ns=cutoff + 100000000,
            at='deadline', type='IncompleteRead')
        self.transport = [request, response, error]
        (self.root / 'money/transport.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in self.transport))
        self.native.update(transport_errors=[error], native_success=False, final_identity_verified=False)
        self.put('worker-analysis.json', [self.native])
        self.result.update(accepted=False, result={'accepted': False})
        self.result['infrastructure_errors'].insert(0, dict(role='money', errors=[error]))
        self.put('result.json', self.result)
        return worker, error

    def test_timeout_failure_preserved_without_modifying_raw_evidence(self):
        self.timeout()
        before = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        reviewed = route.audit(self.root, self.plan)
        self.assertFalse(reviewed['accepted'])
        self.assertFalse(reviewed['audited_autonomous_complete'])
        self.assertEqual(list(reviewed['timeout_cleanup']), ['money'])
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_normal_success_passes_same_audit(self):
        self.assertTrue(route.audit(self.root, self.plan)['audited_autonomous_complete'])

    def test_errors_before_deadline_after_cleanup_or_without_response_refused(self):
        worker, error = self.timeout()
        for change in ({'mono_ns': 1}, {'mono_ns': worker['end_monotonic_ns'] + 16000000000},
                       {'type': 'TimeoutError'}, {'event': 'handler_error'}, {'request': 999}):
            with self.subTest(change=change):
                with self.assertRaises(ValueError):
                    route.timeout_errors(worker, self.plan, [*self.transport[:2], {**error, **change}])
        bad = copy.deepcopy(self.transport)
        bad[1]['status'] = 500
        with self.assertRaises(ValueError):
            route.timeout_errors(worker, self.plan, bad)
        with self.assertRaises(ValueError):
            route.timeout_errors(worker, self.plan, [self.transport[0], error])

    def test_not_a_timeout_or_unfinished_cleanup_refused(self):
        worker, error = self.timeout()
        for change in ({'timed_out': False}, {'exit_code': 0}, {'elapsed_seconds': 1700},
                       {'end_monotonic_ns': worker['start_monotonic_ns'] + 1000000000}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                route.timeout_errors({**worker, **change}, self.plan, self.transport)
        self.result['workers'][0]['relay_complete'] = False
        self.put('result.json', self.result)
        with self.assertRaises(ValueError):
            route.audit(self.root, self.plan)

    def test_only_four_untouched_projects_run_and_replay_refused(self):
        batch = self.root / 'batch'
        batch.mkdir()
        for name in ('frozen.json', 'continuation-v1/stopped.json', 'B1/plan.json'):
            self.put('batch/' + name, {})
        for label in route.REMAINING:
            (batch / label).mkdir()
        calls = []
        reviewed = dict(accepted=False, audited_autonomous_complete=False, timeout_cleanup={'money': {}})
        class FakeEngine:
            def run(self, root):
                calls.append(root.name)
                route.study.original.write_json(root / 'plan.json', {})
                return dict(accepted=False, result={'groups': {}}, project_seconds=1801)
        with patch.object(route, 'verify'), patch.object(route, 'audit', return_value=reviewed), \
             patch.object(route.study, 'runner', return_value=FakeEngine()):
            route.freeze(batch)
            route.run(batch)
            with self.assertRaises(FileExistsError):
                route.run(batch)
        self.assertEqual(calls, ['B2', 'A2', 'A3', 'B3'])


if __name__ == '__main__':
    unittest.main()
