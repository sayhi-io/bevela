"""Real CodexBackend subprocess I/O against the sayhi-fakes `fake-codex` CLI.

Nothing here replaces the runner: `codex` on PATH is a POSIX shell launcher that
runs fake-codex as its own child, reproducing the npm launcher topology
(codex-cli/bin/codex.js spawns the native binary; SIGKILL cannot be forwarded).
"""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
import uuid
from unittest.mock import patch

from project_intent.session_connector import CodexBackend, attach, continue_session
from tests.fake_runner_support import (ROOT, log_records, require_fakes, settle_no_processes,
                                       wait_until, write_script)

CHILD = textwrap.dedent('''
    import json, sys
    from project_intent.session_connector import continue_session
    spec = json.loads(sys.argv[1])
    try:
        continue_session(*spec['common'], spec['request'], spec['message'], 'resume')
    except KeyboardInterrupt:
        print('interrupted', flush=True)
        sys.exit(130)
''')


class FakeCodexCase(unittest.TestCase):
    def setUp(self):
        self.fakes, self.node = require_fakes(self)
        self.temp = tempfile.TemporaryDirectory(prefix='pi-codex-fake-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.session = str(uuid.uuid4())
        self.checkout = self.root / 'checkout'
        subprocess.run(['git', 'init', '-q', str(self.checkout)], check=True)
        launcher = self.root / 'bin/codex'
        launcher.parent.mkdir()
        # Deliberately not `exec`: the shell stays the direct child, like the
        # npm launcher, so only whole-group signalling stops fake-codex.
        launcher.write_text(f'#!/bin/sh\n"{self.node}" "{self.fakes}/bin/fake-codex.mjs" "$@"\nexit $?\n')
        launcher.chmod(0o755)
        self.script = self.root / 'codex-script.json'
        self.log = self.root / 'codex-log.jsonl'
        write_script(self.script, [])
        self.env = {'PATH': f'{launcher.parent}{os.pathsep}{os.environ.get("PATH", "")}',
                    'SAYHI_FAKE_CODEX_SCRIPT': str(self.script), 'SAYHI_FAKE_CODEX_LOG': str(self.log),
                    'SAYHI_FAKE_STATE': str(self.root / 'counters.json')}
        environment = patch.dict(os.environ, self.env)
        environment.start()
        self.addCleanup(environment.stop)
        self.addCleanup(self.assert_no_leaks)

    def assert_no_leaks(self):
        self.assertEqual(settle_no_processes(self.session), [], 'fake-codex process leaked')

    def scenario(self, response, **extra):
        write_script(self.script, [dict({'name': 'turn', 'endpoint': 'codex_exec', 'response': response}, **extra)])

    def resume(self, message='continue the task', **timeouts):
        return CodexBackend(**timeouts).deliver(self.session, str(self.checkout), message, 'resume')


class CodexFakeCliTests(FakeCodexCase):
    # -- normal turns --------------------------------------------------------
    def test_normal_resume_turn_is_observed_complete(self):
        self.scenario({'message': 'done', 'commands': [{'command': 'git status', 'output': 'clean'}]})
        result = self.resume('literal $(not-a-shell) message')
        self.assertEqual(result, {'status': 'turn-completed', 'execution': 'observed-complete',
                                  'acceptance': 'not-assessed'})
        argv = log_records(self.log, 'argv')
        self.assertEqual(argv[0]['argv'], ['exec', 'resume', '--json', self.session, '-'])
        prompt = log_records(self.log, 'prompt')[0]
        self.assertEqual((prompt['resume_id'], prompt['prompt']), (self.session, 'literal $(not-a-shell) message'))

    def test_normal_queue_receipt(self):
        result = CodexBackend().deliver(self.session, str(self.checkout), 'queued $(literal)', 'queue')
        self.assertEqual(result['status'], 'queued')
        self.assertRegex(result['message_id'], r'^[0-9a-f-]{36}$')
        self.assertEqual(log_records(self.log, 'argv')[0]['argv'],
                         ['queue', '--thread', self.session, '--message', 'queued $(literal)'])

    def test_failed_turn_is_uncertain(self):
        self.scenario({'fail': 'model refused'})
        result = self.resume()
        self.assertEqual((result['status'], result['exit_code']), ('uncertain', 1))

    # -- crash mid-turn ------------------------------------------------------
    def test_crash_mid_turn_exit_code(self):
        self.scenario({'crash_after_events': 2, 'crash_exit_code': 3, 'stderr_on_crash': 'native panic'})
        result = self.resume()
        self.assertEqual((result['status'], result['exit_code']), ('uncertain', 3))

    def test_crash_mid_turn_by_signal(self):
        self.scenario({'crash_after_events': 2, 'crash_signal': 'SIGKILL'})
        result = self.resume()
        # The shell launcher reports the child's signal as 128 + 9.
        self.assertEqual((result['status'], result['exit_code']), ('uncertain', 137))

    def test_clean_exit_without_terminal_event_is_uncertain(self):
        self.scenario({'crash_after_events': 2, 'crash_exit_code': 0})
        self.assertEqual(self.resume()['status'], 'uncertain')

    # -- malformed or out-of-order JSONL -------------------------------------
    def test_malformed_line_is_ignored_but_never_counted(self):
        self.scenario({'malformed_after_events': 2})
        self.assertEqual(self.resume()['status'], 'turn-completed')
        self.scenario({'events': [{'type': 'thread.started', 'thread_id': '{{thread_id}}'}, {'type': 'turn.started'},
                                  '{"type":"turn.completed","usage":'], 'exit_code': 0})
        self.assertEqual(self.resume()['status'], 'uncertain')

    def test_non_object_json_lines_do_not_crash_parser(self):
        self.scenario({'events': ['[1,2]', '"text"', '42', 'null', {'type': 'thread.started', 'thread_id': '{{thread_id}}'},
                                  {'type': 'turn.started'}, {'type': 'turn.completed', 'usage': {}}]})
        self.assertEqual(self.resume()['status'], 'turn-completed')

    def test_items_after_terminal_turn_event_are_uncertain(self):
        self.scenario({'out_of_order': True})
        self.assertEqual(self.resume()['status'], 'uncertain')

    def test_completion_before_exact_thread_is_uncertain(self):
        self.scenario({'events': [{'type': 'turn.completed', 'usage': {}}, {'type': 'thread.started', 'thread_id': '{{thread_id}}'}]})
        self.assertEqual(self.resume()['status'], 'uncertain')

    def test_foreign_thread_is_uncertain(self):
        self.scenario({'events': [{'type': 'thread.started', 'thread_id': 'foreign'},
                                  {'type': 'thread.started', 'thread_id': '{{thread_id}}'},
                                  {'type': 'turn.started'}, {'type': 'turn.completed', 'usage': {}}]})
        self.assertEqual(self.resume()['status'], 'uncertain')

    def test_failed_then_completed_turn_is_uncertain(self):
        self.scenario({'events': [{'type': 'thread.started', 'thread_id': '{{thread_id}}'}, {'type': 'turn.started'},
                                  {'type': 'turn.failed', 'error': {'message': 'x'}}, {'type': 'turn.completed', 'usage': {}}]})
        self.assertEqual(self.resume()['status'], 'uncertain')

    # -- silence versus timeouts ---------------------------------------------
    def test_silence_within_timeout_is_not_failure(self):
        self.scenario({'first_event_ms': 1200, 'event_ms': 300})
        started = time.monotonic()
        self.assertEqual(self.resume(resume_timeout=10)['status'], 'turn-completed')
        self.assertGreaterEqual(time.monotonic() - started, 1.2)

    def test_silence_past_timeout_stops_whole_process_group(self):
        self.scenario({'first_event_ms': 60000})
        started = time.monotonic()
        result = self.resume(resume_timeout=1, kill_grace=2)
        elapsed = time.monotonic() - started
        self.assertEqual(result['status'], 'uncertain')
        self.assertIn('Transport interrupted', result['reason'])
        self.assertLess(elapsed, 5)
        # Before the fix only the shell launcher was killed and fake-codex kept
        # running the turn as an orphan.
        self.assertEqual(settle_no_processes(self.session, timeout=1), [])

    def test_stalled_mid_turn_after_events_times_out(self):
        self.scenario({'event_ms': 60000})
        result = self.resume(resume_timeout=1, kill_grace=2)
        self.assertEqual(result['status'], 'uncertain')
        self.assertEqual(settle_no_processes(self.session, timeout=1), [])

    def test_launcher_ignoring_sigterm_is_killed_after_grace(self):
        launcher = self.root / 'bin/codex'
        launcher.write_text(f'#!/bin/sh\ntrap "" TERM\n"{self.node}" "{self.fakes}/bin/fake-codex.mjs" "$@"\n')
        self.scenario({'first_event_ms': 60000})
        started = time.monotonic()
        self.assertEqual(self.resume(resume_timeout=.5, kill_grace=1)['status'], 'uncertain')
        self.assertLess(time.monotonic() - started, 5)


class CodexFakeCliSessionTests(FakeCodexCase):
    """continue_session receipts across cancellation and explicit resumption."""

    def setUp(self):
        super().setUp()
        self.config = self.root / 'config.json'
        target = dict(scope='sayhi/project-intent', workstream='PI-MISSION-01', session=self.session,
                      checkout=str(self.checkout))
        self.state = self.root / 'state'
        self.config.write_text(json.dumps(dict(operator='test-operator', authority_ref='user-task',
                                               allowed_targets=[target], state_directory=str(self.state))))
        self.config.chmod(0o600)
        rollout = self.root / 'rollout.jsonl'
        rollout.write_text(json.dumps(dict(type='session_meta', payload=dict(id=self.session, cwd=str(self.checkout)))) + '\n')
        self.common = [str(self.config), *target.values()]
        attach(*self.common, rollout)

    def test_cancel_mid_turn_then_explicit_resume(self):
        write_script(self.script, [
            {'name': 'stalled', 'endpoint': 'codex_exec', 'times': 1, 'response': {'event_ms': 60000}},
            {'name': 'resumed', 'endpoint': 'codex_exec', 'response': {'message': 'resumed'}}])
        child = subprocess.Popen([sys.executable, '-c', CHILD, json.dumps(
            {'common': self.common, 'request': 'r1', 'message': 'first attempt'})],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
        self.addCleanup(lambda: child.poll() is None and child.kill())
        wait_until(lambda: log_records(self.log, 'prompt'))
        time.sleep(.3)  # thread.started emitted; the turn is now stalled mid-stream
        receipt_path = self.state / 'r1.receipt.json'
        self.assertEqual(json.loads(receipt_path.read_text())['status'], 'uncertain')
        child.send_signal(signal.SIGINT)
        stdout, stderr = child.communicate(timeout=15)
        self.assertEqual((child.returncode, stdout.strip()), (130, 'interrupted'), stderr)
        self.assertEqual(settle_no_processes(self.session, timeout=1), [], 'cancel orphaned fake-codex')
        receipt = json.loads(receipt_path.read_text())
        self.assertEqual((receipt['status'], receipt['execution'], receipt['interrupted']),
                         ('uncertain', 'unknown', 'KeyboardInterrupt'))
        self.assertIn('observed_at', receipt)

        # Same request after interruption: the uncertain receipt stands; nothing relaunches.
        launches = len(log_records(self.log, 'argv'))
        duplicate = continue_session(*self.common, 'r1', 'first attempt', 'resume')
        self.assertTrue(duplicate['duplicate'])
        self.assertEqual(duplicate['status'], 'uncertain')
        self.assertEqual(len(log_records(self.log, 'argv')), launches)

        # An explicit new request resumes the same thread and is observed complete.
        resumed = continue_session(*self.common, 'r2', 'after interruption', 'resume')
        self.assertEqual((resumed['status'], resumed['execution']), ('turn-completed', 'observed-complete'))
        self.assertEqual(log_records(self.log, 'argv')[-1]['argv'], ['exec', 'resume', '--json', self.session, '-'])
        self.assertTrue(log_records(self.log, 'prompt')[-1]['prompt'].endswith('after interruption'))

    def test_timeout_receipt_is_persisted(self):
        self.scenario({'first_event_ms': 60000})
        receipt = continue_session(*self.common, 'r3', 'slow', 'resume',
                                   backend=CodexBackend(resume_timeout=.5, kill_grace=1))
        self.assertEqual(receipt['status'], 'uncertain')
        self.assertEqual(json.loads((self.state / 'r3.receipt.json').read_text())['status'], 'uncertain')


if __name__ == '__main__':
    unittest.main()
