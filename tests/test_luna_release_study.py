import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments import luna_release_study as study
from experiments.luna_release_evaluation import process


class LunaReleaseStudyTests(unittest.TestCase):
    def test_model_and_equal_limits(self):
        self.assertEqual(study.MODEL, 'gpt-5.6-luna')
        for arm in study.ORDER:
            for role in study.ROLES:
                prompt=study.prompt(arm,role,'initial')
                self.assertIn('medium worker',prompt)
                self.assertIn('30 minutes',prompt)
                self.assertIn('R2-specific acceptance failures are expected',prompt)
                self.assertEqual('Additional channel: actual Project Intent' in prompt, arm.endswith('aware'))

    def test_revision_successor_registration_is_distinct(self):
        self.assertIn('luna03-A-aware-storage-successor',study.prompt('A-aware','storage','revision'))
        self.assertNotIn('storage-successor',study.prompt('A-aware','storage','initial'))

    def test_repo_role_paths(self):
        self.assertEqual(study.paths('A-control','export')[1].parts[-2:],('support','export'))
        self.assertEqual(study.paths('A-control','integration')[1].parts[-2:],('status','integration'))

    def test_missing_preflight_is_not_permission_to_run(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(study,'ROOT',Path(temp)):
            with self.assertRaises(FileNotFoundError): study.run_arm('A-control')
            self.assertFalse((Path(temp)/'arms/A-control/execution-start.json').exists())

    def test_freeze_rejects_source_drift(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(study,'ROOT',Path(temp)):
            study.write_json(Path(temp)/'freeze.json',{'inputs':{},'limits':study.LIMITS,'order':list(study.ORDER)})
            with self.assertRaisesRegex(ValueError,'drift'): study.require_frozen('A-control')

    def test_setup_resume_refuses_completed_or_started_arms(self):
        for marker in ('setup.json','execution-start.json','context/snapshot.json','context/map.json'):
            with tempfile.TemporaryDirectory() as temp, patch.object(study,'ROOT',Path(temp)):
                directory=Path(temp)/'arms/A-aware'
                (directory/marker).parent.mkdir(parents=True,exist_ok=True)
                (directory/marker).write_text('{}')
                with self.assertRaisesRegex(ValueError,'unfinished, unstarted'):
                    study.validate_setup_resume('A-aware')

    def test_process_failure_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'evidence'
            result=process(['/usr/bin/false'],path)
            self.assertFalse(result['passed'])
            self.assertEqual(json.loads((path/'result.json').read_text())['exit_code'],1)
            with self.assertRaises(FileExistsError): process(['/usr/bin/true'],path)


if __name__ == '__main__': unittest.main()
