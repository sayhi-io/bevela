import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments import qwen_steering as route
from experiments import qwen_steering_hook as hook

SOURCE = Path(__file__).resolve().parents[1]
DECLARED = {'related_tasks': [], 'workers': [], 'omitted_tasks': 0, 'omitted_workers': 0}


class SteeringTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.parent = Path(temp.name)
        self.work = self.parent / 'work'
        self.work.mkdir()
        (self.work / 'example.py').write_text('VALUE = 1\n')
        self.config = dict(enabled=True, checkout=str(self.work), scope='test/project',
                           sessions={'worker-1': 'TASK'},
                           baseline={'example.py': hook.file_digest(self.work, 'example.py')})
        self.event = dict(session_id='worker-1', cwd=str(self.work), hook_event_name='PostToolUse')
        self.env = patch.dict(os.environ, {'QWEN_SESSION_ID': 'worker-1'})
        self.env.start()
        self.addCleanup(self.env.stop)

    def call(self, event=None, config=None):
        return hook.handle(config or self.config, event or self.event, self.parent / 'state',
                           context_reader=lambda *_: DECLARED)

    def test_off_is_noop_without_state(self):
        self.assertEqual(self.call(config={**self.config, 'enabled': False}), {})
        self.assertFalse((self.parent / 'state').exists())

    def test_initial_then_changed_source_without_reporting(self):
        self.assertIn('additionalContext', self.call()['hookSpecificOutput'])
        self.assertEqual(self.call(), {})
        (self.work / 'example.py').write_text('VALUE = 2\n')
        message = self.call()['hookSpecificOutput']['additionalContext']
        self.assertIn('example.py', message)
        self.assertNotIn('VALUE = 2', message)
        self.assertIn('author and semantic impact unverified', message)
        self.assertEqual(self.call(), {})

    def test_declarations_refresh_without_source_change(self):
        self.call()
        with patch.dict(DECLARED, workers=[{'working': 'new public contract'}]):
            self.assertIn('new public contract', self.call()['hookSpecificOutput']['additionalContext'])

    def test_session_checkout_and_event_fenced(self):
        for field, value in [('session_id', 'other'), ('cwd', '/tmp'), ('hook_event_name', 'Stop')]:
            with self.assertRaises(ValueError):
                self.call(event={**self.event, field: value})

    def test_missing_symlink_and_outside_source(self):
        self.call()
        (self.work / 'example.py').unlink()
        self.assertIn('example.py', self.call()['hookSpecificOutput']['additionalContext'])
        (self.work / 'example.py').symlink_to('/etc/passwd')
        with self.assertRaises((ValueError, OSError)):
            self.call()
        with self.assertRaises(ValueError):
            hook.file_digest(self.work, '../outside.py')

    def test_notice_budget_and_no_tool_decisions(self):
        for number in range(hook.MAX_NOTICES + 3):
            (self.work / 'example.py').write_text(str(number))
            value = self.call()
            self.assertNotIn('decision', value)
        state = json.loads((self.parent / 'state/state.json').read_text())
        self.assertEqual(state['notices'], hook.MAX_NOTICES)
        self.assertEqual(state['suppressed'], 3)

    def test_no_transcript_or_tool_response_inspection(self):
        value = self.call(event={**self.event, 'transcript_path': '/not/available',
                                'tool_response': 'secret evaluator answer', 'tool_input': {'command': 'irrelevant'}})
        self.assertNotIn('secret evaluator', json.dumps(value))

    def prepare(self, enabled):
        runtime = self.parent / 'runtime/bin'
        runtime.mkdir(parents=True, exist_ok=True)
        (runtime / 'qwen').write_text('console.log("0.23.2");\n')
        engine = route.runner(enabled, 1)
        root = engine.prepare(self.parent / str(enabled), 'C', SOURCE,
                              runtime.parent, 'http://127.0.0.1:8078/v1', 5)
        return engine, root

    def test_freeze_toggle_same_tasks_and_actual_native_settings(self):
        off, a = self.prepare(False)
        on, b = self.prepare(True)
        for name in ('producer.txt', 'consumer.txt', 'work/AGENTS.md', 'check_contract.py'):
            self.assertEqual((a / name).read_bytes(), (b / name).read_bytes())
        self.assertEqual((a / 'settings-template.json').read_bytes(), (b / 'settings-template.json').read_bytes())
        self.assertFalse((a / 'pi-source/steering.json').exists())
        on.verify(b, before=True)
        on.preflight(b)
        with self.assertRaises(ValueError):
            off.verify(b)
        plan = json.loads((b / 'plan.json').read_text())
        # Exercise the record wrapper without launching inference.
        with patch.object(on.adapter, 'Relay') as relay, patch.object(on.adapter.subprocess, 'Popen', side_effect=OSError('test launch refusal')):
            relay.return_value.__enter__.return_value = plan['endpoint']
            on.adapter.record(b, 'producer', plan)
        actual = json.loads((b / 'qwen-home/producer/settings.json').read_text())
        self.assertEqual(actual['hooks'], route.hooks(b))
        self.assertNotIn('hooks', on.adapter.settings(plan['model'], plan['endpoint'], 230000, 'medium'))

    def test_hook_bundle_tampering_rejected(self):
        engine, root = self.prepare(True)
        (root / 'pi-source/qwen_steering_hook.py').write_text('tampered')
        with self.assertRaises(ValueError):
            engine.verify(root)


if __name__ == '__main__':
    unittest.main()
