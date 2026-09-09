import json
from pathlib import Path
import re
import unittest

from experiments.results_catalog import BATCHES, fingerprint, project, tokens


ROOT = Path(__file__).resolve().parents[1]


class ResultsPublicationTests(unittest.TestCase):
    def test_public_measurements_keep_all_runs_and_reverse_chronology(self):
        data = json.loads((ROOT / 'docs/results/measurements.json').read_text())
        groups = data['groups']
        self.assertEqual(set(BATCHES), {g['id'] for g in groups})
        self.assertEqual(57, sum(len(g['trials']) for g in groups))
        self.assertEqual(sorted((g['last_trial_started_at'] for g in groups), reverse=True),
                         [g['last_trial_started_at'] for g in groups])
        for group in groups:
            rows = group['trials']
            self.assertEqual(sorted((r['started_at'] for r in rows), reverse=True),
                             [r['started_at'] for r in rows])
            for row in rows:
                self.assertEqual(row['score'], 7 - len(row['failed_seams']))
                self.assertAlmostEqual(sum(w['duration_seconds'] for w in row['workers']),
                                       row['aggregate_worker_seconds'])
                self.assertRegex(row['plan_sha256'], r'^[a-f0-9]{64}$')

    def test_export_contains_no_private_execution_material(self):
        text = (ROOT / 'docs/results/measurements.json').read_text()
        self.assertNotRegex(text, r'/home/|/tmp/|Bearer |-----BEGIN|"(?:root|pid|session|native_log|commands|agent_messages)"')
        self.assertNotRegex(text, r'[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}')

    def test_tokens_are_subsets_not_added_again(self):
        self.assertIsNone(tokens(None))
        source = {'input_tokens': 100, 'cached_input_tokens': 80, 'output_tokens': 10,
                  'reasoning_output_tokens': 3, 'total_tokens': 110, 'secret': 'omit'}
        self.assertEqual(tokens(source)['total_tokens'], 110)
        self.assertNotIn('secret', tokens(source))

    def test_fingerprint_separates_backend_from_workflow_and_ui(self):
        original = {'project_intent/cli.py': {'sha256': 'a'},
                    'project_intent/web/app.js': {'sha256': 'b'},
                    'skills/project-intent/SKILL.md': {'sha256': 'c'}}
        changed = dict(original, **{'project_intent/web/app.js': {'sha256': 'd'}})
        self.assertEqual(fingerprint(original, 'project_intent/'), fingerprint(changed, 'project_intent/'))
        self.assertIsNone(fingerprint({}, 'project_intent/'))

    def test_luna_low_is_not_mislabeled_sol_low_pi(self):
        data = json.loads((ROOT / 'docs/results/measurements.json').read_text())
        rows = [r for g in data['groups'] for r in g['trials']]
        luna_pi = [r for r in rows if r['model'] == 'gpt-5.6-luna' and r['effort'] == 'low' and r['pi_enabled']]
        self.assertEqual([7, 7], [r['score'] for r in luna_pi])
        self.assertFalse(any(r['model'] == 'gpt-5.6-sol' and r['effort'] == 'low' and r['pi_enabled'] for r in rows))

    def test_readme_and_public_result_links_resolve(self):
        paths = [ROOT / 'README.md', ROOT / 'RESULTS.md',
                 ROOT / 'docs/CLI_AB_EVALUATION.md', ROOT / 'docs/README_ACCURACY_AUDIT.md',
                 *sorted((ROOT / 'docs/results').glob('*.md'))]
        for path in paths:
            self.assertTrue(path.is_file(), path)
            for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
                if target.startswith(('https://', 'http://', '#', 'mailto:')):
                    continue
                target = target.split('#')[0]
                self.assertTrue((path.parent / target).exists(), f'{path.name}: {target}')

    def test_withdrawn_controls_are_not_active_cases(self):
        for name in ('experiments/shared_contract_study.py',
                     'experiments/luna_release_study.py',
                     'experiments/luna_release_study_v2.py',
                     'docs/CLI_AB_PILOT_01.md', 'docs/CLI_AB_SHARED_CONTRACT.md',
                     'docs/CLI_AB_LUNA_RELEASE_03.md', 'docs/CLI_AB_STUDY03.md'):
            self.assertFalse((ROOT / name).exists(), name)
        catalog = (ROOT / 'RESULTS.md').read_text()
        self.assertIn('withdrawn-coached-controls', catalog)
        for line in catalog.splitlines():
            if line.startswith('|'):
                self.assertNotRegex(line, r'Status Pilot01|Status Study02|Release Study03')
        # Removing invalid controls must not remove unfavorable native outcomes.
        for name in ('seam_microstudy.py', 'seven_seams.py', 'torture_refunds.py',
                     'concurrency_study.py', 'seven_seams_self_organizing.py'):
            self.assertTrue((ROOT / 'experiments' / name).is_file(), name)

    def test_readme_breakthrough_bars_match_recorded_scores(self):
        readme = (ROOT / 'README.md').read_text()
        bars = re.findall(r'Run \d\s+\[([#.]{7})\]\s+(\d)/7', readme)
        self.assertEqual([0, 2, 3, 4, 3, 7, 7], [int(score) for _, score in bars])
        for bar, score in bars:
            self.assertEqual(int(score), bar.count('#'))
        self.assertFalse(any(line.startswith('|') for line in readme.splitlines()))


if __name__ == '__main__':
    unittest.main()
