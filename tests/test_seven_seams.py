import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from experiments import seven_seams as study

ROOT = Path(__file__).resolve().parents[1]


class SevenSeamsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.work = self.root / 'fixture'
        shutil.copytree(study.ASSETS / 'fixture', self.work)

    def score(self):
        before = study.manifest(self.work)
        result = subprocess.run([sys.executable, '-B', '-I', str(ROOT / 'experiments/seven_seams_check.py'), str(self.work)],
                                cwd=self.work, capture_output=True, text=True, check=True)
        self.assertEqual(study.manifest(self.work), before)
        return json.loads(result.stdout)

    def solution(self):
        # Deterministic checker-validation fixture, never shown to model workers.
        files = {
            'catalog.py': 'PRICES = {"tea": 1250, "cake": 725}\n',
            'checkout.py': 'from catalog import PRICES\ndef total(items): return sum(PRICES[n] for n in items) / 100\n',
            'inventory.py': 'STOCK = {"tea": {"on_hand": 10, "reserved": 2}, "cake": {"on_hand": 5, "reserved": 1}}\ndef available(name): return STOCK[name]["on_hand"] - STOCK[name]["reserved"]\n',
            'shipping.py': 'WEIGHTS = {"tea": 250, "cake": 500}\ndef parcel_kg(items): return sum(WEIGHTS[n] for n in items) / 1000\n',
            'promotions.py': 'from checkout import total\nDISCOUNTS = {"tea": 1000, "cake": 2000}\ndef discounted_total(name, quantity=1): return round(total([name] * quantity) * (1 - DISCOUNTS[name] / 10000), 2)\n',
            'delivery.py': 'LEAD_TIME = {"tea": 48, "cake": 24}\ndef days(name): return LEAD_TIME[name] / 24\n',
            'customers.py': 'CONTACTS = {"ada": {"email": "ada@example.test", "display_name": "Ada"}, "lin": {"email": "lin@example.test", "display_name": "Lin"}}\ndef email(customer): return CONTACTS[customer]["email"]\n',
            'orders.py': 'STATUS = {"P-1": "paid", "P-2": "pending", "R-3": "refunded"}\ndef is_paid(order): return STATUS[order] == "paid"\n',
            'presentation.py': '''from checkout import total
from inventory import available
from shipping import parcel_kg
from promotions import DISCOUNTS, discounted_total
from delivery import days
from customers import CONTACTS, email
from orders import STATUS
def price_label(n): return f"${total([n]):.2f}"
def stock_label(n): return f"{available(n)} available"
def weight_label(n): return f"{parcel_kg([n]):.3f} kg"
def discount_label(n): return f"{DISCOUNTS[n] / 100:g}% off; ${discounted_total(n):.2f}"
def delivery_label(n): return f"{days(n):g} {'day' if days(n) == 1 else 'days'}"
def contact_label(n): return f"{CONTACTS[n]['display_name']} <{email(n)}>"
def status_label(n): return {"paid": "Paid", "pending": "Awaiting payment", "refunded": "Refunded"}[STATUS[n]]
''',
        }
        for name, content in files.items():
            (self.work / name).write_text(content)

    def test_starting_fixture_preserves_existing_behavior_but_has_seven_unfinished_problems(self):
        result = subprocess.run([sys.executable, '-B', '-m', 'unittest', '-q'], cwd=self.work, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.score()
        self.assertEqual(result['out_of'], 7)
        self.assertEqual(result['score'], 0)
        self.assertEqual(list(result['problems']), list(study.SEAMS))

    def test_reference_contract_satisfies_all_seven(self):
        self.solution()
        self.assertEqual(self.score()['score'], 7)

    def test_each_public_helper_must_keep_keyword_arguments(self):
        self.solution()
        helpers = (('checkout', 'total'), ('inventory', 'available'),
                   ('shipping', 'parcel_kg'), ('promotions', 'discounted_total'),
                   ('delivery', 'days'), ('customers', 'email'), ('orders', 'is_paid'))
        for problem, (name, function) in zip(study.SEAMS, helpers):
            with self.subTest(problem=problem):
                path = self.work / (name + '.py')
                original = path.read_text()
                path.write_text(original.replace(f'def {function}(', 'def _original(')
                                + f'\ndef {function}(*args): return _original(*args)\n')
                result = self.score()
                self.assertEqual(result['score'], 6)
                self.assertFalse(result['problems'][problem]['producer']['passed'])
                path.write_text(original)

    def test_each_broken_consumer_is_reported_as_its_own_problem(self):
        self.solution()
        original = (self.work / 'presentation.py').read_text()
        functions = ('price_label', 'stock_label', 'weight_label', 'discount_label', 'delivery_label', 'contact_label', 'status_label')
        for problem, function in zip(study.SEAMS, functions):
            with self.subTest(problem=problem):
                (self.work / 'presentation.py').write_text(original + f'\ndef {function}(n): return "wrong"\n')
                result = self.score()
                self.assertEqual(result['score'], 6)
                failed = [name for name, row in result['problems'].items() if not row['both_preserved']]
                self.assertEqual(failed, [problem])

    def test_discount_also_detects_broken_price_dependency(self):
        self.solution()
        (self.work / 'checkout.py').write_text('from catalog import PRICES\ndef total(items): return sum(PRICES[n] for n in items)\n')
        result = self.score()
        self.assertFalse(result['problems']['prices']['both_preserved'])
        self.assertFalse(result['problems']['discounts']['both_preserved'])
        self.assertEqual(result['score'], 5)

    def test_hard_coded_labels_do_not_pass_current_data_requirement(self):
        self.solution()
        with (self.work / 'presentation.py').open('a') as stream:
            stream.write('\ndef price_label(n): return {"tea": "$12.50", "cake": "$7.25"}[n]\n')
        result = self.score()
        self.assertFalse(result['problems']['prices']['consumer']['passed'])
        self.assertTrue(result['problems']['prices']['producer']['passed'])
        self.assertEqual(result['score'], 6)

    def test_native_command_matches_prior_microstudy_shape(self):
        self.assertEqual(study.command('/codex', self.work, 'task', 'gpt-5.6-luna', 'medium'),
                         ['/codex', 'exec', '--json', '--sandbox', 'workspace-write', '-m', 'gpt-5.6-luna',
                          '-c', 'model_reasoning_effort="medium"', '-C', str(self.work), 'task'])

    def test_prepare_freezes_pi_and_task_inputs_without_starting_any_worker(self):
        with patch.object(study, 'run', side_effect=AssertionError('prepare must not run workers')):
            root = study.prepare(ROOT, self.root)
        self.assertFalse((root / 'started.json').exists())
        self.assertFalse((root / 'control').exists())
        plan = json.loads((root / 'plan.json').read_text())
        self.assertEqual(plan['roles'], ['producer', 'consumer'])
        self.assertEqual(len(plan['problems']), 7)
        self.assertEqual(plan['control_runs'], 0)
        study.verify_inputs(root, plan)
        self.assertNotIn('tests', [p.name for p in (root / 'pi-source').iterdir()])
        for role in study.ROLES:
            self.assertEqual((root / (role + '.txt')).read_bytes(), (study.ASSETS / (role + '.txt')).read_bytes())
        context = json.loads((root / 'work/.pi/snapshot.json').read_text())
        self.assertEqual({r['id'] for r in context['records']}, {'PRODUCER', 'CONSUMER'})
        for record in context['records']:
            self.assertEqual(len(record['boundaries']), 7)
        onboard = subprocess.run([sys.executable, '-B', '-I', str(root / 'pi-source/project_intent/_worker_cli.py'),
            'onboard', '--worker-config', str(root / 'work/.pi/worker.json'), '--scope', study.SCOPE,
            '--query', 'migrate stored representations'], cwd=root / 'work', capture_output=True, text=True)
        self.assertEqual(onboard.returncode, 0, onboard.stderr)
        response = json.loads(onboard.stdout)
        self.assertEqual(response['discovery']['candidates'][0]['id'], 'PRODUCER')
        self.assertEqual(response['documentation']['source_root'], str(root / 'pi-source'))
        study.verify_inputs(root, plan)

    def test_frozen_input_changes_fail_before_any_launch(self):
        root = study.prepare(ROOT, self.root)
        (root / 'pi-source/project_intent/cli.py').write_text('# changed\n')
        with patch.object(study, 'record', side_effect=AssertionError('must not launch')), self.assertRaises(ValueError):
            study.run(root)

    def test_requested_model_and_effort_are_frozen_at_preparation(self):
        root = study.prepare(ROOT, self.root, model='gpt-5.3-codex-spark', effort='medium')
        plan = json.loads((root / 'plan.json').read_text())
        self.assertEqual(plan['model'], 'gpt-5.3-codex-spark')
        self.assertEqual(plan['effort'], 'medium')
        self.assertFalse((root / 'started.json').exists())

    def test_check_refuses_mid_run_or_unstarted_fixture(self):
        root = study.prepare(ROOT, self.root)
        with self.assertRaises(ValueError):
            study.check(root)

    def test_single_run_records_two_workers_and_never_starts_another_trial(self):
        root = study.prepare(ROOT, self.root)
        def fake_record(root, role, binary, plan):
            return {'role': role, 'exit_code': 0, 'start_monotonic_ns': 1, 'end_monotonic_ns': 2}
        with patch.object(study.shutil, 'which', return_value='/fake/codex'), \
                patch.object(study.subprocess, 'check_output', return_value='fake-version'), \
                patch.object(study, 'record', side_effect=fake_record) as record:
            summary = study.run(root)
            self.assertEqual(record.call_count, 2)
            self.assertEqual({c.args[1] for c in record.call_args_list}, {'producer', 'consumer'})
            self.assertEqual(len(summary['workers']), 2)
            with self.assertRaises(FileExistsError):
                study.run(root)
            self.assertEqual(record.call_count, 2)
        before = study.manifest(root / 'after')
        result = study.check(root)
        self.assertEqual(result['score'], 0)
        self.assertEqual(study.manifest(root / 'after'), before)
        with self.assertRaises(FileExistsError):
            study.check(root)
