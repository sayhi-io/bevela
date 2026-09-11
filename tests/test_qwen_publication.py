"""Public study ledgers retain outcomes without private evaluation locations."""
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'docs/results'
SANITIZED = ('qwen-confidence', 'qwen-ordinary-thinking-off',
             'qwen-compact-pi', 'qwen-compact-pi-v2')


class QwenPublicationTests(unittest.TestCase):
    def test_all_public_qwen_ledgers_are_valid_and_omit_private_roots(self):
        ledgers = list(RESULTS.glob('qwen-*-measurements.json'))
        self.assertGreaterEqual(len(ledgers), 9)
        for path in ledgers:
            with self.subTest(ledger=path.name):
                text = path.read_text()
                self.assertIsInstance(json.loads(text), dict)
                self.assertNotRegex(text, r'/(?:home|Users|tmp|private)/')

    def test_sanitized_copies_disclose_original_hash_and_retained_errors(self):
        for name in SANITIZED:
            with self.subTest(ledger=name):
                text = (RESULTS / (name + '-measurements.json')).read_text()
                note = json.loads(text)['publication']
                self.assertEqual(note['kind'], 'sanitized-public-copy')
                self.assertRegex(note['source_ledger_sha256'], r'^[a-f0-9]{64}$')
                self.assertTrue(note['redactions'])
                self.assertIn('<private-evaluation>/source/', text)
                self.assertIn('ImportError', text)

    def test_qwen_result_pages_have_resolvable_local_links(self):
        pages = list(RESULTS.glob('qwen-*.md'))
        for path in pages:
            for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
                if '://' in target or target.startswith('#'):
                    continue
                with self.subTest(page=path.name, target=target):
                    self.assertTrue((path.parent / target.split('#')[0]).is_file())


if __name__ == '__main__':
    unittest.main()
