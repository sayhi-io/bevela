import ast
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from experiments import torture_refunds as study

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'experiments/torture_refunds'
CHECKER = ROOT / 'experiments/torture_refunds_check.py'


class TortureContracts(unittest.TestCase):
    def probe(self, source, mutation=None):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            shutil.copytree(source, target, dirs_exist_ok=True)
            if mutation:
                path = target / 'shop.py'
                original = path.read_text()
                self.assertIn(mutation[0], original)
                path.write_text(original.replace(*mutation))
            result = subprocess.run([sys.executable, '-B', '-I', str(CHECKER), str(target)], capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)

    def test_original_fixture_passes_existing_contracts(self):
        result = subprocess.run([sys.executable, '-B', '-m', 'unittest', '-v'], cwd=ASSETS / 'fixture', capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_joint_requirements_are_satisfiable(self):
        self.assertEqual(self.probe(ASSETS / 'reference')['score'], 7)

    def test_unchanged_fixture_does_not_pass(self):
        self.assertEqual(self.probe(ASSETS / 'fixture')['score'], 0)

    def test_each_deliberate_defect_is_detected(self):
        mutations = {
            'units': ('return cents / 100', 'return cents / 1'),
            'both_features': ('def refund(order_id, request_id, quantity=None):', 'def refund(order_id, request_id, quantity=None):\n    raise NotImplementedError("Lost refund implementation")'),
            'rounding': ("cumulative = cents_round(Decimal(order['charged']) * returned / order['quantity'])", "cumulative = int(Decimal(order['charged']) * returned / order['quantity'])"),
            'inventory': ("STOCK[order['sku']]['on_hand'] += count", "STOCK[order['sku']]['on_hand'] += count * 2"),
            'retry_safety': ("'requests': REQUESTS", "'requests': {}"),
            'persistence': ("'orders': ORDERS", "'orders': {key: {field: value for field, value in order.items() if field != 'note'} for key, order in ORDERS.items()}"),
            'receipts': ('RECEIPTS.pop(order_id, None)', 'None  # lost invalidation'),
        }
        for name, mutation in mutations.items():
            with self.subTest(problem=name):
                result = self.probe(ASSETS / 'reference', mutation)
                self.assertFalse(result['problems'][name]['passed'], result)

    def test_preparation_excludes_reference_checker_and_pi_from_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            trial = study.prepare('gpt-5.6-luna', 'high', directory)
            self.assertEqual(set(study.manifest(trial / 'work')), {'shop.py', 'README.md', 'test_existing.py'})
            plan = json.loads((trial / 'plan.json').read_text())
            self.assertEqual((plan['model'], plan['effort'], plan['control_runs']), ('gpt-5.6-luna', 'high', 1))
            self.assertFalse(plan['pi_enabled'])
            study.verify_inputs(trial, plan)
            self.assertFalse((trial / 'started.json').exists())
            self.assertEqual((trial / 'producer.txt').read_bytes(), (ASSETS / 'producer.txt').read_bytes())
            self.assertEqual((trial / 'consumer.txt').read_bytes(), (ASSETS / 'consumer.txt').read_bytes())

    def test_native_recording_functions_unchanged(self):
        previous = ast.parse((ROOT / 'experiments/seven_seams.py').read_text())
        current = ast.parse((ROOT / 'experiments/torture_refunds.py').read_text())
        for name in ('command', 'record', 'manifest'):
            node = lambda tree: next(item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == name)
            self.assertEqual(ast.dump(node(previous)), ast.dump(node(current)))


if __name__ == '__main__':
    unittest.main()
