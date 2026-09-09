import copy
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest

from project_intent.worker_context import discovery, resolve_assignment
from project_intent.onboarding import documentation


ROOT = Path(__file__).resolve().parents[1]
FAILED_QUERY = 'receipt label product dollar price formatting tests'


class OnboardingRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pi-onboarding-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        snapshot = json.loads((ROOT / '.project-intent/snapshot.json').read_text())
        prototype = next(r for r in snapshot['records'] if r['kind'] == 'workstream')
        self.records = []
        for key, statement in (
            ('PRICES', 'Change catalog.PRICES to store integer cents instead of dollar floats. Keep checkout.total(items) returning the same dollar totals.'),
            ('RECEIPT', 'Include the product\'s dollar price in receipt.label(name), to two decimal places: label("tea") should return "tea: $12.50" and label("cake") should return "cake: $7.25".'),
        ):
            row = copy.deepcopy(prototype)
            row.update(id=key, statement=statement, scope=statement,
                       source_checkout=str(self.root / 'reference'), acceptance=[statement])
            row.pop('provider_identifier', None)
            self.records.append(row)
        snapshot.update(scope_id='experiment/seam-micro', records=self.records)
        self.state = {'id': snapshot['scope_id'], 'label': 'test', 'snapshot': snapshot, 'provider_status': 'offline'}
        self.scope = self.state['id']
        self.snapshot_path = self.root / 'snapshot.json'
        self.snapshot_path.write_text(json.dumps(snapshot))
        self.leases = self.root / 'leases'
        self.config = self.root / 'worker config.json'
        self.config.write_text(json.dumps({'scopes': {self.scope: {
            'snapshot': str(self.snapshot_path), 'enrollment_directory': str(self.leases),
        }, 'other/scope': {'snapshot': str(self.root / 'absent.json'),
                           'enrollment_directory': str(self.root / 'other-leases')}}}))
        self.checkout = self.root / 'task checkout'
        self.checkout.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.checkout)], check=True)

    def run_cli(self, *args):
        # CI runs from source without an editable install. Exercise the exact
        # release launcher from the unrelated task checkout in both environments.
        result = subprocess.run([sys.executable, '-I', str(ROOT / 'project_intent/_worker_cli.py'), *args],
                                cwd=self.checkout, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def common(self):
        return ['--worker-config', str(self.config), '--scope', self.scope,
                '--checkout', str(self.checkout)]

    def test_exact_failed_query_keeps_and_ranks_receipt(self):
        # The less relevant price record has a checkout advantage; relevance wins.
        self.records[0]['source_checkout'] = str(self.checkout)
        result = discovery([self.state], {'root': str(self.checkout)}, FAILED_QUERY)
        self.assertEqual([r['id'] for r in result['candidates']], ['RECEIPT', 'PRICES'])
        match = result['candidates'][0]['query_match']
        self.assertEqual(match['matched_terms'], ['receipt', 'label', 'product', 'dollar', 'price'])
        self.assertEqual(match['unmatched_terms'], ['formatting', 'tests'])
        self.assertEqual(match['matched_count'], 5)
        self.assertEqual(match['query_term_count'], 7)

    def test_deduplicated_case_and_code_punctuation(self):
        rows = discovery([self.state], query='RECEIPT.label(name) receipt')['candidates']
        self.assertEqual(rows[0]['id'], 'RECEIPT')
        self.assertEqual(rows[0]['query_match']['query_term_count'], 3)
        self.assertEqual(rows[0]['query_match']['matched_count'], 3)

    def test_unfiltered_inventory_and_unknown_query(self):
        self.assertEqual(discovery([self.state], query='unfindablexyz')['candidates'], [])
        rows = discovery([self.state])['candidates']
        self.assertEqual({r['id'] for r in rows}, {'PRICES', 'RECEIPT'})
        self.assertTrue(all(r['query_match']['query_term_count'] == 0 for r in rows))

    def test_equal_scores_are_stable_and_checkout_breaks_ties(self):
        self.records[0]['statement'] = self.records[1]['statement']
        self.records[0]['scope'] = self.records[1]['scope']
        self.records[1]['source_checkout'] = str(self.checkout)
        rows = discovery([self.state], {'root': str(self.checkout)}, 'dollar')['candidates']
        self.assertEqual([r['id'] for r in rows], ['RECEIPT', 'PRICES'])
        self.records[0]['source_checkout'] = str(self.checkout)
        rows = discovery([self.state], {'root': str(self.checkout)}, 'dollar')['candidates']
        self.assertEqual([r['id'] for r in rows], ['PRICES', 'RECEIPT'])

    def test_partial_match_never_resolves_or_enrolls_automatically(self):
        out = self.run_cli('onboard', *self.common(), '--query', FAILED_QUERY)
        self.assertEqual(out['discovery']['candidates'][0]['id'], 'RECEIPT')
        self.assertNotIn('orientation', out)
        self.assertNotIn('enrollment_template', out)
        self.assertFalse(self.leases.exists())
        with self.assertRaises(ValueError):
            resolve_assignment([self.state], 'receip', self.scope)

    def test_scoped_fallback_then_exact_enrollment_is_executable(self):
        out = self.run_cli('onboard', *self.common(), '--query', 'unfindablexyz')
        recovery, = out['inventory_recovery']
        self.assertEqual(recovery['scope'], self.scope)
        self.assertEqual(shlex.split(recovery['command']), recovery['argv'])
        self.assertNotIn('--query', recovery['argv'])
        self.assertEqual(out['discovery']['source_errors'], [])  # Other scope not read.
        inventory = subprocess.run(recovery['argv'], cwd=self.checkout, capture_output=True, text=True)
        self.assertEqual(inventory.returncode, 0, inventory.stderr)
        self.assertEqual({r['id'] for r in json.loads(inventory.stdout)['candidates']}, {'PRICES', 'RECEIPT'})
        self.assertFalse(self.leases.exists())
        selected = self.run_cli('onboard', *self.common(), '--workstream', 'RECEIPT')
        argv = shlex.split(selected['enrollment_template'])
        self.assertEqual(argv[argv.index('--worker-config') + 1], str(self.config))
        self.assertEqual(argv[argv.index('--checkout') + 1], str(self.checkout))
        self.assertFalse(self.leases.exists())
        # Explicitly choose a unique presence-only identity; never inspect host logs.
        codex = argv.index('--codex')
        argv[codex:codex + 1] = ['--session', 'receipt-regression']
        result = subprocess.run(argv, cwd=self.checkout, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['workstream'], 'RECEIPT')
        self.assertTrue((self.leases / 'receipt-regression.json').is_file())
        self.assertFalse((self.root / 'other-leases').exists())

    def test_docs_uses_installed_paths_without_loading_config_or_git(self):
        out = self.run_cli('docs', '--worker-config', str(self.root / 'missing-config.json'),
                           '--checkout', str(self.root / 'missing-checkout'))
        expected = documentation()
        self.assertEqual(out, expected)
        for record in out['documents'].values():
            self.assertTrue(record['available'])
            self.assertTrue(Path(record['path']).is_relative_to(ROOT))
        # A fake docs directory in cwd cannot redirect the installed paths.
        (self.checkout / 'docs').mkdir()
        self.assertEqual(self.run_cli('docs'), expected)

    def test_printed_commands_cannot_load_checkout_or_pythonpath_package(self):
        out = self.run_cli('onboard', *self.common(), '--query', 'unfindablexyz')
        selected = self.run_cli('onboard', *self.common(), '--workstream', 'RECEIPT')
        shadow = self.checkout / 'project_intent'
        shadow.mkdir()
        (shadow / '__init__.py').write_text('raise RuntimeError("checkout package imported")\n')
        env = dict(os.environ, PYTHONPATH=str(self.checkout))
        inventory = subprocess.run(out['inventory_recovery'][0]['argv'], cwd=self.checkout,
                                   env=env, capture_output=True, text=True)
        self.assertEqual(inventory.returncode, 0, inventory.stderr)
        self.assertEqual({r['id'] for r in json.loads(inventory.stdout)['candidates']}, {'PRICES', 'RECEIPT'})
        argv = shlex.split(selected['enrollment_template'])
        i = argv.index('--codex')
        argv[i:i + 1] = ['--session', 'exact-release-regression']
        result = subprocess.run(argv, cwd=self.checkout, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        enrolled = json.loads(result.stdout)
        self.assertEqual(enrolled['workstream'], 'RECEIPT')
        self.assertEqual(enrolled['checkout']['root'], str(self.checkout))

    def test_missing_packaged_docs_are_explicit_not_searched(self):
        from unittest.mock import patch
        with patch('project_intent.onboarding.__file__', str(self.root / 'package/onboarding.py')):
            out = documentation()
        self.assertTrue(all(not d['available'] for d in out['documents'].values()))
        self.assertFalse(self.leases.exists())
