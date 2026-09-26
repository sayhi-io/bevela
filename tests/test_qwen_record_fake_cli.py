"""Real qwen_code_adapter.record() subprocess I/O against sayhi-fakes `fake-qwen-code`.

The recorder, relay, bubblewrap sandbox and /usr/bin/node launch are unchanged;
only the trial's runtime/bin/qwen is the scripted fake instead of Qwen Code.
"""
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
import uuid

from experiments import analyze_qwen_distributed as analyze
from experiments import qwen_code_adapter as adapter
from experiments import qwen_distributed_study as study
from experiments import qwen_seven_seams as seven_seams
from tests.fake_runner_support import (ROOT, require_fakes, settle_no_processes, wait_until)

NODE = '/usr/bin/node'  # adapter.argv() launches exactly this interpreter
LAUNCHER = textwrap.dedent('''\
    // Trial-local stand-in for Qwen Code; bubblewrap clears the environment.
    const path = require('path');
    const { pathToFileURL } = require('url');
    process.env.SAYHI_FAKE_QWEN_SCRIPT = path.join(__dirname, '..', 'scenario.json');
    process.env.SAYHI_FAKE_QWEN_LOG = path.join(process.env.HOME, '.qwen', 'fake-qwen.jsonl');
    import(pathToFileURL(path.join(__dirname, '..', 'src/cli/fake-qwen-code.mjs')).href).then((cli) => cli.run());
''')
CHILD = textwrap.dedent('''
    import json, sys
    from pathlib import Path
    from experiments import qwen_code_adapter as adapter
    from tests.fake_runner_support import settle_no_processes
    spec = json.loads(sys.argv[1])
    try:
        adapter.record(Path(spec['root']), 'worker', spec['plan'])
    except KeyboardInterrupt:
        # Observe while this recorder is still alive: bubblewrap's
        # --die-with-parent must not be what cleans up a cancelled worker.
        print(json.dumps({'interrupted': True, 'alive': settle_no_processes(spec['root'], 3)}), flush=True)
        sys.exit(130)
''')


def sandbox_available():
    if not shutil.which('bwrap'):
        return False
    probe = subprocess.run(['bwrap', '--ro-bind', '/', '/', '--unshare-user', '--unshare-pid', '--die-with-parent',
                            '--new-session', 'true'], capture_output=True, timeout=10)
    return probe.returncode == 0


class QwenRecordFakeCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not sandbox_available():
            raise unittest.SkipTest('bubblewrap with unprivileged user namespaces is unavailable')

    def setUp(self):
        self.fakes, _ = require_fakes(self, NODE)
        self.temp = tempfile.TemporaryDirectory(prefix='pi-qwen-fake-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'trial'
        (self.root / 'work').mkdir(parents=True)
        (self.root / 'DISPOSABLE_TRIAL').write_text('')
        runtime = self.root / 'runtime'
        shutil.copytree(self.fakes / 'src', runtime / 'src')
        (runtime / 'bin').mkdir()
        (runtime / 'bin/qwen').write_text(LAUNCHER)
        (self.root / 'qwen-home/worker').mkdir(parents=True)
        (self.root / 'worker.txt').write_text('Complete the scripted task.')
        self.session = str(uuid.uuid4())
        self.plan = {'sessions': {'worker': self.session}, 'endpoint': 'http://127.0.0.1:9/v1',
                     'model': 'fake-qwen', 'context_window': 65536, 'server_effort': 'xhigh',
                     'pi_enabled': False, 'timeout_seconds': 20, 'roles': ['worker']}
        (self.root / 'plan.json').write_text(json.dumps(self.plan))
        self.addCleanup(lambda: self.assertEqual(settle_no_processes(str(self.root)), [], 'sandboxed worker leaked'))

    def scenario(self, response):
        (self.root / 'runtime/scenario.json').write_text(json.dumps(
            {'identity': 'sayhi-fake', 'scenarios': [{'endpoint': 'qwen_code', 'response': response}]}))

    def record(self, **plan):
        return adapter.record(self.root, 'worker', dict(self.plan, **plan))

    def stdout(self):
        return (self.root / 'worker/stdout.jsonl').read_text().splitlines()

    def analysis(self, row):
        return study.worker_analysis(self.root, row)

    def assert_receipts(self, row):
        self.assertEqual(json.loads((self.root / 'worker/result.json').read_text()), row)
        started = json.loads((self.root / 'worker/started.json').read_text())
        self.assertEqual((started['pid'], started['session']), (row['pid'], self.session))
        self.assertTrue(row['relay_complete'])

    def test_normal_turn(self):
        self.scenario({'message': 'finished', 'tool_calls': [{'name': 'run_shell_command', 'input': {'command': 'ls'}}]})
        row = self.record()
        self.assertEqual(row['exit_code'], 0)
        self.assertFalse(row.get('timed_out', False))
        self.assertTrue(row['stream_complete'] and row['stream_eof'])
        self.assert_receipts(row)
        records = [json.loads(line) for line in self.stdout()]
        self.assertEqual([r['type'] for r in records], ['system', 'assistant', 'user', 'assistant', 'result'])
        self.assertEqual({r['session_id'] for r in records}, {self.session})
        self.assertEqual(records[0]['model'], 'fake-qwen')
        events = (self.root / 'worker/events.jsonl').read_text().splitlines()
        self.assertEqual([json.loads(line)['event'] for line in events], records)
        value = self.analysis(row)
        self.assertTrue(value['native_success'])
        self.assertEqual([c['name'] for c in value['tool_calls']], ['run_shell_command'])
        # Native argv reached the CLI unchanged through the sandbox.
        log = [json.loads(line) for line in (self.root / 'qwen-home/worker/fake-qwen.jsonl').read_text().splitlines()]
        self.assertEqual(log[1]['session_id'], self.session)
        self.assertEqual(log[1]['output_format'], 'stream-json')
        self.assertEqual(log[1]['prompt'], 'Complete the scripted task.')

    def test_crash_mid_turn(self):
        self.scenario({'crash_after_events': 2, 'crash_exit_code': 3, 'stderr_on_crash': 'native panic',
                       'tool_calls': [{'name': 'read_file', 'input': {}}]})
        row = self.record()
        self.assertEqual(row['exit_code'], 3)
        self.assertTrue(row['stream_complete'])
        self.assert_receipts(row)
        self.assertEqual(len(self.stdout()), 2)
        self.assertIn(b'native panic', (self.root / 'worker/stderr.bin').read_bytes())
        value = self.analysis(row)
        self.assertFalse(value['native_success'])
        self.assertEqual(value['native_final'], [])

    def test_crash_by_signal(self):
        self.scenario({'crash_after_events': 1, 'crash_signal': 'SIGKILL'})
        row = self.record()
        self.assertNotEqual(row['exit_code'], 0)
        self.assertTrue(row['stream_complete'])
        self.assertFalse(self.analysis(row)['native_success'])

    def test_malformed_and_non_object_lines(self):
        self.scenario({'events': [
            {'type': 'system', 'subtype': 'init', 'session_id': '{{session_id}}', 'model': 'fake-qwen'},
            '{"type":"assistant","message":', '[1, 2]', '"text"', '{"type":"assistant","message":"flat string"}',
            {'type': 'assistant', 'session_id': '{{session_id}}', 'message': {'content': 'not a list'}},
            {'type': 'result', 'subtype': 'success', 'is_error': False, 'session_id': '{{session_id}}', 'result': 'ok'}]})
        row = self.record()
        self.assertEqual(row['exit_code'], 0)
        events = [json.loads(line)['event'] for line in (self.root / 'worker/events.jsonl').read_text().splitlines()]
        self.assertEqual(events[1], {'unparsed': '{"type":"assistant","message":\n'})
        self.assertEqual(events[2:4], [[1, 2], 'text'])
        value = self.analysis(row)
        self.assertTrue(value['native_success'])
        self.assertEqual(value['tool_calls'], [])
        # Every consumer of the recorded stream tolerates the same lines.
        self.assertEqual(analyze.tool_events(self.root, 'worker', row['start_monotonic_ns']), [])
        self.assertTrue(seven_seams.telemetry(self.root, row, self.plan)['native_success'])

    def test_out_of_order_result_before_init(self):
        self.scenario({'events': [
            {'type': 'result', 'subtype': 'success', 'is_error': False, 'session_id': '{{session_id}}', 'result': 'ok'},
            {'type': 'system', 'subtype': 'init', 'session_id': '{{session_id}}', 'model': 'fake-qwen'},
            {'type': 'result', 'subtype': 'error_during_execution', 'is_error': True, 'session_id': '{{session_id}}'}]})
        row = self.record()
        value = self.analysis(row)
        # The last terminal record decides; an early success does not.
        self.assertFalse(value['native_success'])

    def test_silence_within_timeout_is_not_failure(self):
        self.scenario({'first_event_ms': 1500})
        started = time.monotonic()
        row = self.record(timeout_seconds=10)
        self.assertGreaterEqual(time.monotonic() - started, 1.5)
        self.assertEqual(row['exit_code'], 0)
        self.assertNotIn('timed_out', row)
        self.assertTrue(self.analysis(row)['native_success'])

    def test_timeout_mid_turn_stops_sandbox_and_records(self):
        self.scenario({'event_ms': 60000, 'tool_calls': [{'name': 'read_file', 'input': {}}]})
        row = self.record(timeout_seconds=1.5)
        self.assertTrue(row['timed_out'])
        self.assertIn(row['exit_code'], (-signal.SIGTERM, -signal.SIGKILL))
        self.assertTrue(row['stream_complete'])
        self.assertLess(row['elapsed_seconds'], 10)
        self.assert_receipts(row)
        self.assertEqual(len(self.stdout()), 1)  # init only; the turn was stalled
        self.assertEqual(settle_no_processes(str(self.root), 1), [])

    def test_cancel_mid_turn_stops_worker_and_blocks_retry(self):
        self.scenario({'event_ms': 60000, 'tool_calls': [{'name': 'read_file', 'input': {}}]})
        child = subprocess.Popen([sys.executable, '-c', CHILD, json.dumps({'root': str(self.root), 'plan': self.plan})],
                                 cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                 start_new_session=True)
        self.addCleanup(lambda: child.poll() is None and child.kill())
        wait_until(lambda: (self.root / 'worker/stdout.jsonl').exists() and self.stdout())
        child.send_signal(signal.SIGINT)
        stdout, stderr = child.communicate(timeout=30)
        self.assertEqual(child.returncode, 130, stderr)
        self.assertEqual(json.loads(stdout), {'interrupted': True, 'alive': []})
        # Started without a final receipt: controllers refuse automatic retry
        # (qwen_boundary_resume.run, qwen_distributed_study.run_all).
        self.assertTrue((self.root / 'worker/started.json').exists())
        self.assertFalse((self.root / 'worker/result.json').exists())


if __name__ == '__main__':
    unittest.main()
