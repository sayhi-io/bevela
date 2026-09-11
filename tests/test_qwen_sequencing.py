import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments import qwen_boundary_resume as boundary
from experiments import qwen_distributed_study as study


class FrozenSequencingTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))
        temporary = tempfile.TemporaryDirectory(prefix='qwen-frozen-sequencing-')
        self.addCleanup(temporary.cleanup)
        self.batch = Path(temporary.name) / 'batch'
        plans = {}
        for label in ('B1', 'C1'):
            root = self.batch / label
            root.mkdir(parents=True)
            (root / 'plan.json').write_text('{}')
            plans[label] = study.sha(root / 'plan.json')
        self.frozen = {'order': ['B1', 'C1'], 'plans': plans,
            'study_sha256': study.sha(study.__file__), 'adapter_sha256': study.sha(study.adapter.__file__),
            'sequencing_policy': boundary.policy_identity()}
        self.save()

    def save(self):
        (self.batch / 'frozen.json').write_text(json.dumps(self.frozen))

    def execute(self, root):
        result = {'accepted': False, 'autonomous_complete': False, 'result': {'groups': {}},
            'project_seconds': 1800, 'usage': {'complete_usage': False}}
        (root / 'result.json').write_text(json.dumps(result))
        return result

    def test_expected_timeout_advances_once_and_rechecks_saved_results(self):
        self.execute(self.batch / 'B1')
        with patch.object(study, 'run', side_effect=self.execute) as execute, \
                patch.object(boundary, 'disposition', return_value={'state': 'reviewed_predetermined_timeout'}) as classify:
            study.run_all(self.batch)
            execute.assert_called_once_with(self.batch / 'C1')
            self.assertEqual([c.args[0].name for c in classify.call_args_list], ['B1', 'C1'])
            study.run_all(self.batch)
            self.assertEqual(execute.call_count, 1)
            self.assertEqual(classify.call_count, 4)
        self.assertFalse(list(self.batch.glob('sequencing-amendment*')))

    def test_missing_or_changed_policy_refuses_before_launch(self):
        for policy in (None, {**boundary.policy_identity(), 'classifier_sha256': '0' * 64}):
            self.frozen['sequencing_policy'] = policy
            self.save()
            with patch.object(study, 'run') as execute, self.assertRaisesRegex(AssertionError, 'policy'):
                study.run_all(self.batch)
            execute.assert_not_called()

    def test_started_without_receipt_never_retries(self):
        (self.batch / 'B1/started.json').write_text('{}')
        with patch.object(study, 'run') as execute, self.assertRaisesRegex(RuntimeError, 'never retry'):
            study.run_all(self.batch)
        execute.assert_not_called()

    def test_policy_change_between_projects_stops_next_launch(self):
        identity = boundary.policy_identity()
        changed = {**identity, 'controller_sha256': '0' * 64}
        with patch.object(boundary, 'policy_identity', side_effect=[identity, identity, changed]), \
                patch.object(study, 'run', side_effect=self.execute) as execute, \
                patch.object(boundary, 'disposition', return_value={'state': 'reviewed_predetermined_timeout'}), \
                self.assertRaisesRegex(AssertionError, 'policy changed'):
            study.run_all(self.batch)
        execute.assert_called_once_with(self.batch / 'B1')


if __name__ == '__main__':
    unittest.main()
