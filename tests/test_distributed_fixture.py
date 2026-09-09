import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from experiments.distributed_check import ASSETS, check


class DistributedFixtureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='depot-fixture-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'work'
        shutil.copytree(ASSETS / 'fixture', self.root)

    def reference(self):
        for role in ('catalog', 'orders', 'settlement', 'reporting'):
            shutil.copytree(ASSETS / 'reference' / role, self.root / role, dirs_exist_ok=True)

    def test_working_legacy_product_is_not_a_migrated_solution(self):
        result = check(self.root)
        self.assertFalse(result['accepted'])
        self.assertEqual(len(result['groups']), 12)
        self.assertTrue(result['groups']['legacy_workflow']['passed'])
        self.assertTrue(all(c['passed'] for c in result['component_checks'].values()))
        self.assertIn('order_recovery', result['failed_contracts'])

    def test_reference_passes_all_contracts_and_original_local_checks(self):
        self.reference()
        result = check(self.root)
        self.assertTrue(result['accepted'], result)
        self.assertEqual(result['failed_contracts'], [])
        self.assertTrue(all(c['passed'] for c in result['component_checks'].values()))

    def test_public_checker_is_same_bytes_and_returns_json_on_contract_failure(self):
        frozen = Path(self.temp.name) / 'frozen-acceptance.py'
        shutil.copy2(ASSETS / 'fixture/acceptance.py', frozen)
        process = subprocess.run([sys.executable, '-B', '-I', str(frozen), str(self.root)],
                                 capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout), check(self.root, frozen))
        self.assertEqual((self.root / 'acceptance.py').read_bytes(), frozen.read_bytes())

    def test_missing_source_is_infrastructure_not_zero_score(self):
        process = subprocess.run([sys.executable, '-B', '-I', str(self.root / 'acceptance.py'),
                                  str(self.root / 'absent')], capture_output=True, text=True)
        self.assertNotEqual(process.returncode, 0)
        self.assertIn('infrastructure_error', json.loads(process.stdout))

    def test_checker_outside_candidate_is_not_replaced_by_candidate_edits(self):
        self.reference()
        (self.root / 'acceptance.py').write_text('raise RuntimeError("modified candidate checker")\n')
        self.assertTrue(check(self.root)['accepted'])

    def test_real_legacy_files_migrate_without_losing_holds_or_seen_events(self):
        state = Path(self.temp.name) / 'state'
        code = '''import json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from catalog import Catalog
from orders import Orders
from settlement import Settlement
from reporting import Reporting
p=Path(sys.argv[2]); p.mkdir(exist_ok=True)
c=Catalog(p/'catalog.json'); o=Orders(p/'orders.json',c)
s=Settlement(p/'settlement.json'); r=Reporting(p/'reporting.json')
if sys.argv[3]=='legacy':
    c.put('tea','Tea',2.5,5); o.place('old',[{'sku':'tea','quantity':2}])
    for event in o.events():
        s.handle(event); r.handle(event); o.ack(event['event_id'])
    s.drain()
    for event in s.events():
        r.handle(event); s.ack(event['event_id'])
    assert r.legacy_receipt('old')=='old: $5.00 (paid)'
else:
    assert c.get('tea')['stock']==3 and o.get('old')['total_minor']==500
    assert s.events()==[] and s.drain()==0
    for event in json.loads((p/'settlement.json').read_text())['seen'].values():
        assert s.handle(event) is False
    for event in json.loads((p/'reporting.json').read_text())['seen'].values():
        assert r.handle(event) is False
    o.cancel('old'); assert c.get('tea')['stock']==5
    for event in o.events(): s.handle(event); r.handle(event)
    for event in s.events(): r.handle(event)
    assert s.balance()==0 and r.revenue()==0
    assert r.legacy_receipt('old')=='old: $5.00 (refunded)'
'''
        for phase in ('legacy', 'migrated'):
            if phase == 'migrated':
                self.reference()
            process = subprocess.run([sys.executable, '-B', '-I', '-c', code,
                                      str(self.root), str(state), phase], capture_output=True, text=True)
            self.assertEqual(process.returncode, 0, process.stderr)

    def test_component_failure_does_not_skip_other_groups(self):
        self.reference()
        (self.root / 'catalog/__init__.py').write_text('raise RuntimeError("broken catalog")\n')
        result = check(self.root)
        self.assertFalse(result['accepted'])
        self.assertFalse(result['groups']['money_and_quotes']['passed'])
        self.assertTrue(result['groups']['reporting_late_join']['passed'])
        self.assertTrue(result['groups']['deferred_settlement']['passed'])
        self.assertEqual(len(result['component_checks']), 4)

    def test_shared_architecture_and_tasks_have_no_reference_payload(self):
        objective = (self.root / 'OBJECTIVE.md').read_text()
        architecture = json.loads((self.root / 'architecture.json').read_text())['boundaries']
        self.assertEqual(set(architecture), {'catalog', 'orders', 'settlement', 'reporting'})
        for role, boundaries in architecture.items():
            self.assertTrue((self.root / 'tasks' / (role + '.txt')).is_file())
            for boundary in boundaries:
                self.assertIn(boundary, objective)
        self.assertFalse((self.root / 'reference').exists())

    def test_hanging_local_test_fails_component_and_preserves_later_results(self):
        self.reference()
        (self.root / 'catalog/test_hanging.py').write_text(
            'import threading, unittest\n'
            'class HangingTest(unittest.TestCase):\n'
            '    def test_hangs(self):\n'
            '        threading.Event().wait()\n')
        result = check(self.root)
        self.assertFalse(result['accepted'])
        self.assertNotIn('infrastructure_error', result)
        self.assertEqual(result['failed_contracts'], [])
        self.assertEqual(len(result['groups']), 12)
        self.assertEqual(result['component_checks']['catalog'], {
            'passed': False, 'detail': 'Local tests exceeded 5 seconds'})
        for role in ('orders', 'settlement', 'reporting'):
            self.assertTrue(result['component_checks'][role]['passed'], result)

    def test_purposeful_mutations_are_discriminated(self):
        cases = [
            ('catalog', 'rounding=ROUND_HALF_UP', 'rounding="ROUND_DOWN"', 'money_and_quotes'),
            ('catalog', 'return copy.deepcopy(prior["receipt"])',
             'return {**copy.deepcopy(prior["receipt"]), "total_minor": 0}', 'reservation_atomicity'),
            ('catalog', 'self.state.update(version=2, reservations=reservations)',
             'self.state.update(version=2, reservations={})', 'migration_and_restart'),
            ('orders', 'if fail_after_reserve:', 'if False and fail_after_reserve:', 'order_recovery'),
            ('orders', '"schema": 2, "event_id": key + ":" + kind',
             '"schema": 1, "event_id": key + ":" + kind', 'durable_order_outbox'),
            ('settlement', 'record["placed"] = True',
             'record["placed"] = True\n            record["captured"] = True', 'deferred_settlement'),
            ('settlement', ' and not record["cancelled"]', '', 'cancellation_reordering'),
            ('reporting', 'max(record["payment_revision"], event["revision"])',
             'event["revision"]', 'reporting_late_join'),
            ('reporting', 'captured = old["status"] == "paid" or paid > 0',
             'captured = paid > 0', 'migration_and_restart'),
            ('reporting', 'return None\n        total = receipt["total_minor"]',
             'return None\n        total = receipt["total_minor"] * 100', 'legacy_workflow'),
            ('settlement', 'schema not in (1, 2)', 'schema != 2', 'mixed_wire_versions'),
            ('catalog', 'type(value) is not int', 'not isinstance(value, int)', 'validation_is_atomic'),
        ]
        for role, old, new, group in cases:
            with self.subTest(role=role, group=group):
                self.reference()
                source = self.root / role / '__init__.py'
                text = source.read_text()
                self.assertEqual(text.count(old), 1)
                source.write_text(text.replace(old, new, 1))
                result = check(self.root)
                self.assertFalse(result['accepted'])
                self.assertFalse(result['groups'][group]['passed'], result)

    def test_local_success_does_not_establish_integrated_success(self):
        self.reference()
        source = self.root / 'settlement/__init__.py'
        text = source.read_text()
        source.write_text(text.replace(' and not record["cancelled"]', ''))
        result = check(self.root)
        self.assertTrue(all(c['passed'] for c in result['component_checks'].values()), result)
        self.assertFalse(result['groups']['integrated_replay']['passed'])
        self.assertFalse(result['accepted'])



class DistributedV2FixtureTests(unittest.TestCase):
    """Candidate2 assets are bound by the recorder's existing fixture-test copy."""

    def setUp(self):
        self.assets = ASSETS.parent / 'distributed_v2'
        self.temp = tempfile.TemporaryDirectory(prefix='depot-v2-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'work'
        shutil.copytree(self.assets / 'fixture', self.root)

    def reference(self):
        for role in ('catalog', 'orders', 'settlement', 'reporting'):
            shutil.copytree(self.assets / 'reference' / role, self.root / role, dirs_exist_ok=True)

    def evaluate(self):
        return check(self.root, checker=self.assets / 'fixture/acceptance.py')

    def replace(self, role, old, new):
        path = self.root / role / '__init__.py'
        text = path.read_text()
        self.assertEqual(text.count(old), 1, (role, old))
        path.write_text(text.replace(old, new))

    def test_legacy_starting_modules_and_original_groups_are_unchanged(self):
        import ast
        for role in ('catalog', 'orders', 'settlement', 'reporting'):
            for name in ('__init__.py', 'test_' + role + '.py'):
                self.assertEqual((self.root / role / name).read_bytes(),
                                 (ASSETS / 'fixture' / role / name).read_bytes())
        # Compare every original checker function, allowing only the candidate
        # identifier to change in the evaluator envelope.
        original = ast.parse((ASSETS / 'fixture/acceptance.py').read_text())
        current = ast.parse((self.root / 'acceptance.py').read_text().replace(
            '"distributed/v2"', '"distributed/v1"'))
        funcs = {node.name: ast.dump(node) for node in current.body if isinstance(node, ast.FunctionDef)}
        for node in original.body:
            if isinstance(node, ast.FunctionDef):
                self.assertEqual(funcs[node.name], ast.dump(node), node.name)
        result = self.evaluate()
        self.assertFalse(result['accepted'])
        self.assertEqual(len(result['groups']), 15)
        self.assertTrue(result['groups']['legacy_workflow']['passed'])
        self.assertTrue(all(c['passed'] for c in result['component_checks'].values()))

    def test_reference_passes_all_fifteen_and_original_locals(self):
        self.reference()
        result = self.evaluate()
        self.assertTrue(result['accepted'], result)
        self.assertEqual(result['fixture'], 'distributed/v2')
        self.assertEqual(len(result['groups']), 15)
        self.assertEqual(sum(c['tests_run'] for c in result['component_checks'].values()), 8)

    def test_business_contract_is_in_protected_objective(self):
        objective = (self.root / 'OBJECTIVE.md').read_text()
        for token in ('return_items', 'restore(reservation_id', 'return_summary',
                      'Cancellation', 'fail_after_restore', 'producer'):
            self.assertIn(token, objective)
        self.assertFalse((self.root / 'RETURNS.md').exists())
        architecture = json.loads((self.root / 'architecture.json').read_text())['boundaries']
        for role in architecture:
            self.assertIn('contracts/partial-returns', architecture[role])
            self.assertIn('partial-return', (self.root / 'tasks' / (role + '.txt')).read_text())
            self.assertTrue((self.root / role / 'CONTRACT.md').is_file())

    def test_v1_reference_is_not_a_return_solution(self):
        for role in ('catalog', 'orders', 'settlement', 'reporting'):
            shutil.copytree(ASSETS / 'reference' / role, self.root / role, dirs_exist_ok=True)
        result = self.evaluate()
        self.assertEqual(set(result['failed_contracts']), {
            'partial_return_recovery', 'partial_return_pipeline', 'partial_return_cancellation'})
        self.assertTrue(all(c['passed'] for c in result['component_checks'].values()))

    def test_actual_old_v1_and_v2_states_upgrade_with_seen_history_and_holds(self):
        code = '''import json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from catalog import Catalog
from orders import Orders
from settlement import Settlement
from reporting import Reporting
p=Path(sys.argv[2]); p.mkdir(exist_ok=True)
c=Catalog(p/'catalog.json'); o=Orders(p/'orders.json',c)
s=Settlement(p/'settlement.json'); r=Reporting(p/'reporting.json')
if sys.argv[3]=='create':
    c.put('tea','Tea',2.5,5); o.place('old',[{'sku':'tea','quantity':2}])
    for e in o.events(): s.handle(e); r.handle(e); o.ack(e['event_id'])
    s.drain()
    for e in s.events(): r.handle(e); s.ack(e['event_id'])
    assert r.legacy_receipt('old')=='old: $5.00 (paid)'
else:
    assert c.get('tea')['stock']==3 and o.events()==s.events()==[]
    assert s.drain()==0
    o.return_items('old','part',[{'sku':'tea','quantity':1}])
    for e in o.events(): s.handle(e); r.handle(e); o.ack(e['event_id'])
    for e in s.events(): r.handle(e); s.ack(e['event_id'])
    assert c.get('tea')['stock']==4 and s.balance()==r.revenue()==250
    assert r.return_summary('old')=={'returned_items':[{'sku':'tea','quantity':1}],
        'refund_due_minor':250,'refunded_minor':250}
    c=Catalog(p/'catalog.json'); o=Orders(p/'orders.json',c)
    s=Settlement(p/'settlement.json'); r=Reporting(p/'reporting.json')
    assert o.events()==s.events()==[] and s.drain()==0
    o.cancel('old')
    for e in o.events(): s.handle(e); r.handle(e)
    for e in s.events(): r.handle(e)
    assert c.get('tea')['stock']==5 and s.balance()==r.revenue()==0
    assert r.legacy_receipt('old')=='old: $5.00 (refunded)'
'''
        for version in (1, 2):
            with self.subTest(version=version):
                shutil.copytree(self.assets / 'fixture', self.root, dirs_exist_ok=True)
                if version == 2:
                    for role in ('catalog', 'orders', 'settlement', 'reporting'):
                        shutil.copytree(ASSETS / 'reference' / role, self.root / role, dirs_exist_ok=True)
                state = Path(self.temp.name) / ('old-v' + str(version))
                for phase in ('create', 'upgrade'):
                    if phase == 'upgrade':
                        self.reference()
                    process = subprocess.run([sys.executable, '-B', '-I', '-c', code,
                                              str(self.root), str(state), phase],
                                             capture_output=True, text=True, timeout=20)
                    self.assertEqual(process.returncode, 0, process.stderr)

    def test_new_wire_layout_is_not_an_oracle_requirement(self):
        self.reference()
        # Nested Catalog receipt; Orders adapts without sharing Catalog's parser.
        cat = self.root / 'catalog/__init__.py'
        text = cat.read_text()
        start = text.index('    def restore(')
        text = text[:start] + text[start:].replace('return copy.deepcopy(known)',
            'return {"restore": copy.deepcopy(known)}').replace('return copy.deepcopy(receipt)',
            'return {"restore": copy.deepcopy(receipt)}')
        cat.write_text(text)
        self.replace('orders', 'return_id=return_id, items=basket)))',
                     'return_id=return_id, items=basket)))["restore"]')
        # Array-wrapped Orders payload; both actual consumers adapt locally.
        self.replace('orders', '"return_note": {"ticket": return_id, "units": returned["items"],',
                     '"return_note": [{"ticket": return_id, "units": returned["items"],')
        self.replace('orders', '"original": order["record"]["total_minor"]}})',
                     '"original": order["record"]["total_minor"]}]})')
        for role in ('settlement', 'reporting'):
            self.replace(role, 'note = event["return_note"]', 'note = event["return_note"][0]')
        # Reversed Settlement positional payload; only its consumer knows the layout.
        self.replace('settlement',
            '"refund_position": [record["total_minor"], record["partial_refund"]]',
            '"refund_position": [record["partial_refund"], record["total_minor"]]')
        self.replace('reporting', 'total, refunded = map(_integer, event["refund_position"])',
                     'refunded, total = map(_integer, event["refund_position"])')
        self.assertTrue(self.evaluate()['accepted'])

    def test_consistently_wrong_pipeline_still_fails_input_derived_oracle(self):
        self.reference()
        # All downstream consumers accept and consistently propagate this false
        # Catalog credit; agreeing projections cannot establish correctness.
        self.replace('catalog', '"credit": cumulative - refunded_before',
                     '"credit": 0')
        result = self.evaluate()
        self.assertFalse(result['accepted'])
        self.assertFalse(result['groups']['partial_return_pipeline']['passed'], result)
        self.assertFalse(result['groups']['partial_return_recovery']['passed'], result)
        self.assertTrue(result['groups']['integrated_replay']['passed'])
        self.assertTrue(all(c['passed'] for c in result['component_checks'].values()))

    def test_return_mutations_are_detected(self):
        cases = [
            ('orders',
             'return copy.deepcopy(sorted(events, key=lambda e: (e["order_id"], e["revision"], e["event_id"])))',
             'return sorted(events, key=lambda e: (e["order_id"], e["revision"], e["event_id"]))',
             'partial_return_pipeline'),
            ('catalog', 'item["quantity"] - returned.get(item["sku"], 0)',
             'item["quantity"]', 'partial_return_cancellation'),
            ('orders', 'if fail_after_restore:', 'if False and fail_after_restore:',
             'partial_return_recovery'),
            ('settlement', 'record.get("partial_refund", 0) + returned["refund_minor"]',
             'returned["refund_minor"]', 'partial_return_pipeline'),
            ('reporting', 'max(record.get("partial_refund", 0), event["refunded_minor"])',
             'event["refunded_minor"]', 'partial_return_pipeline'),
        ]
        for role, old, new, group in cases:
            with self.subTest(role=role, group=group):
                self.reference()
                self.replace(role, old, new)
                result = self.evaluate()
                self.assertFalse(result['groups'][group]['passed'], result)

    def test_consistently_wrong_fixed_envelopes_fail(self):
        for defect in ('kind', 'revision'):
            with self.subTest(defect=defect):
                self.reference()
                for role in ('orders', 'settlement', 'reporting'):
                    path = self.root / role / '__init__.py'
                    text = path.read_text()
                    if defect == 'kind':
                        text = text.replace('"order.returned"', '"order.credit"')
                    else:
                        text = text.replace('"revision": 3', '"revision": 9').replace(
                            'event["revision"] != 3', 'event["revision"] != 9')
                    path.write_text(text)
                result = self.evaluate()
                self.assertFalse(result['groups']['partial_return_pipeline']['passed'], result)

    def test_checker_copy_runs_without_asset_path_dependency(self):
        self.reference()
        frozen = Path(self.temp.name) / 'acceptance-frozen.py'
        shutil.copy2(self.assets / 'fixture/acceptance.py', frozen)
        (self.root / 'acceptance.py').write_text('raise RuntimeError("candidate edited checker")\n')
        process = subprocess.run([sys.executable, '-B', '-I', str(frozen), str(self.root)],
                                 capture_output=True, text=True, timeout=30)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertTrue(json.loads(process.stdout)['accepted'])

    def test_unadapted_producer_payload_breaks_only_new_integration(self):
        self.reference()
        self.replace('orders', '"return_note": {"ticket": return_id,',
                     '"different_return_note": {"ticket": return_id,')
        result = self.evaluate()
        self.assertFalse(result['groups']['partial_return_pipeline']['passed'], result)
        self.assertTrue(result['groups']['partial_return_recovery']['passed'], result)
        self.assertTrue(result['groups']['integrated_replay']['passed'])
        self.assertTrue(all(c['passed'] for c in result['component_checks'].values()), result)

    def test_reference_components_import_without_peer_packages(self):
        # Smoke check only: this does not certify absence of lazy imports or
        # cross-component state-file access; those remain source-review rules.
        for role in ('catalog', 'orders', 'settlement', 'reporting'):
            with self.subTest(role=role):
                isolated = Path(self.temp.name) / ('isolated-' + role)
                shutil.copytree(self.assets / 'reference' / role, isolated / role)
                code = ('import importlib,sys; sys.path.insert(0,sys.argv[1]); '
                        'm=importlib.import_module(sys.argv[2]); '
                        'assert callable(getattr(m,sys.argv[2].title()))')
                process = subprocess.run([sys.executable, '-B', '-I', '-c', code,
                                          str(isolated), role], cwd=isolated,
                                         capture_output=True, text=True, timeout=5)
                self.assertEqual(process.returncode, 0, process.stderr)


if __name__ == '__main__':
    unittest.main()
