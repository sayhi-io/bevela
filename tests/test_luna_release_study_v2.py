import unittest
from pathlib import Path
from experiments import luna_release_study as old
from experiments import luna_release_study_v2 as new


class LunaReleaseV2Tests(unittest.TestCase):
    def test_separate_attempt_and_equal_conditions(self):
        self.assertNotEqual(old.ROOT, new.ROOT)
        self.assertEqual(new.ORDER, ('A2-control', 'A2-aware', 'B2-aware', 'B2-control'))
        self.assertEqual(old.MODEL, new.MODEL)
        self.assertEqual(old.LIMITS, new.LIMITS)
        self.assertEqual(old.BASE, new.BASE)
        self.assertEqual(old.ROLES, new.ROLES)

    def test_both_browser_sources_and_addendum_are_frozen(self):
        inputs = new.inputs()
        for name in ('luna_release_browser.py', 'luna_release_browser_v2.py',
                     'luna_release_study_v2.py', 'luna_release_evaluation_v2.py'):
            self.assertIn('experiments/' + name, inputs)
        self.assertIn('docs/CLI_AB_LUNA_RELEASE_03_V2.md', inputs)

    def test_actual_worker_and_evaluator_use_repaired_entrypoint(self):
        for arm in new.ORDER:
            self.assertIn('acceptance/luna_release_browser_v2.py', new.prompt(arm, 'browser', 'initial'))
        source = Path(new.SOURCE / 'experiments/luna_release_evaluation_v2.py').read_text()
        self.assertIn("acceptance/'luna_release_browser_v2.py'", source)
        self.assertNotIn("acceptance/'luna_release_browser.py'", source)

    def test_ids_are_distinct_from_preserved_attempt(self):
        text = new.prompt('A2-aware', 'storage', 'revision')
        self.assertIn('PI-LUNA03-A2-AWARE-STORAGE', text)
        self.assertIn('luna03-A2-aware-storage-successor', text)
        self.assertNotIn('PI-LUNA03-A-AWARE-STORAGE', text)


if __name__ == '__main__':
    unittest.main()
