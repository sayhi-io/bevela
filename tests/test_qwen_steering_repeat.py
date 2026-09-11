import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from experiments import qwen_steering_repeat as repeat


class RepeatTests(unittest.TestCase):
    def test_only_generated_manifest_binding_excluded(self):
        # Populate every required static key without coupling to its enumeration.
        plan = {'pi_manifest': {'steering.json': 'session-one', 'backend.py': 'frozen'}}
        for _ in range(40):
            try:
                baseline = repeat.identity(plan)
                break
            except KeyError as exc:
                plan[exc.args[0]] = 'frozen'
        else:
            self.fail('Unexpected unbounded identity schema')
        other = copy.deepcopy(plan)
        other['pi_manifest']['steering.json'] = 'session-two'
        self.assertEqual(repeat.identity(other), baseline)
        other['pi_manifest']['backend.py'] = 'changed'
        self.assertNotEqual(repeat.identity(other), baseline)
        for key in plan.keys() - {'pi_manifest'}:
            changed = copy.deepcopy(plan)
            changed[key] = 'changed'
            self.assertNotEqual(repeat.identity(changed), baseline, key)
        with self.assertRaises(KeyError):
            repeat.identity({})

    def prepared(self, batch):
        entries = []
        for i in range(1, 11):
            inner = batch / f'T{i:02d}'
            inner.mkdir()
            (inner / 'frozen.json').write_text('{}')
            entries.append(dict(name=inner.name, sha256=repeat.sha(inner / 'frozen.json')))
        (batch / 'cohort.json').write_text(json.dumps(dict(version=repeat.VERSION,
            source_sha256=repeat.sha(repeat.__file__), entries=entries, identity={'fixed': True})))

    def test_sequential_ten_and_no_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            batch = Path(directory)
            self.prepared(batch)
            calls = []
            fake = SimpleNamespace(utc=lambda: 'now', verify=lambda *a, **k: {},
                run_all=lambda inner: calls.append(inner.name),
                write_json=lambda path, data: path.write_text(json.dumps(data)))
            with patch.object(repeat, 'runner', return_value=fake), \
                    patch.object(repeat, 'project', side_effect=lambda inner: inner), \
                    patch.object(repeat, 'identity', return_value={'fixed': True}), \
                    patch.object(repeat, 'verify_config'):
                repeat.run_all(batch)
                self.assertEqual(calls, [f'T{i:02d}' for i in range(1, 11)])
                with self.assertRaisesRegex(ValueError, 'replay'):
                    repeat.run_all(batch)
                self.assertEqual(len(calls), 10)

    def test_tamper_blocks_all_launches(self):
        with tempfile.TemporaryDirectory() as directory:
            batch = Path(directory)
            self.prepared(batch)
            (batch / 'T01/frozen.json').write_text('{"changed":true}')
            with patch.object(repeat, 'runner') as factory:
                with self.assertRaisesRegex(ValueError, 'changed'):
                    repeat.run_all(batch)
                factory.assert_not_called()

    def test_infrastructure_failure_not_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            batch = Path(directory)
            self.prepared(batch)
            fake = SimpleNamespace(utc=lambda: 'now', verify=lambda *a, **k: {})
            def fail(inner):
                raise RuntimeError('infrastructure')
            fake.run_all = fail
            with patch.object(repeat, 'runner', return_value=fake), \
                    patch.object(repeat, 'project', side_effect=lambda inner: inner), \
                    patch.object(repeat, 'identity', return_value={'fixed': True}), \
                    patch.object(repeat, 'verify_config'):
                with self.assertRaisesRegex(RuntimeError, 'infrastructure'):
                    repeat.run_all(batch)
                self.assertTrue((batch / 'started.json').exists())
                self.assertFalse((batch / 'completed.json').exists())


if __name__ == '__main__':
    unittest.main()
