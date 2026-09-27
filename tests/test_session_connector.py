import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from project_intent.session_connector import attach, continue_session, CodexBackend, resume_outcome


class ConnectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(['git', 'init', '-q', str(self.root / 'checkout')], check=True)
        self.session = '01a07387-d85b-78f3-8924-2e085ce13936'
        self.config = self.root / 'config.json'
        self.target = dict(scope='sayhi/project-intent', workstream='PI-MISSION-01', session=self.session, checkout=str(self.root / 'checkout'))
        self.config.write_text(json.dumps(dict(operator='test-operator', authority_ref='user-task', allowed_targets=[self.target], state_directory=str(self.root / 'state'))))
        self.config.chmod(0o600)
        self.rollout = self.root / 'rollout.jsonl'
        self.rollout.write_text(json.dumps(dict(type='session_meta', payload=dict(id=self.session, cwd=self.target['checkout'])))+'\nDO NOT READ CONVERSATION')
        self.common = (str(self.config), *self.target.values())

    def test_exact_attachment_and_idempotent_delivery(self):
        result = attach(*self.common, self.rollout)
        self.assertEqual(result['session'], self.session)
        with patch('project_intent.session_connector.CodexBackend.deliver', return_value={'status':'queued','execution':'unconfirmed'}) as deliver:
            receipt = continue_session(*self.common, 'request1', 'Inspect existing evidence')
            duplicate = continue_session(*self.common, 'request1', 'Inspect existing evidence')
            self.assertEqual(receipt['execution'], 'unconfirmed')
            self.assertTrue(duplicate['duplicate']); self.assertEqual(deliver.call_count, 1)
            with self.assertRaises(ValueError): continue_session(*self.common, 'request1', 'Different work')

    def test_wrong_scope_and_checkout_refused(self):
        with self.assertRaises(ValueError): attach(self.config, 'other', *self.common[2:], self.rollout)
        self.rollout.write_text(json.dumps(dict(type='session_meta',payload=dict(id=self.session,cwd='/tmp'))))
        with self.assertRaises(ValueError): attach(*self.common, self.rollout)

    def test_private_config_and_missing_attachment(self):
        with self.assertRaises(FileNotFoundError): continue_session(*self.common, 'r1', 'hello')
        self.config.chmod(0o644)
        with self.assertRaises(ValueError): attach(*self.common, self.rollout)

    def test_crash_is_not_retried(self):
        attach(*self.common, self.rollout)
        with patch('project_intent.session_connector.CodexBackend.deliver', side_effect=RuntimeError('crash')):
            with self.assertRaises(RuntimeError): continue_session(*self.common, 'r1', 'hello')
        with patch('project_intent.session_connector.CodexBackend.deliver') as deliver:
            result = continue_session(*self.common, 'r1', 'hello')
            self.assertEqual(result['status'], 'uncertain'); deliver.assert_not_called()

    def test_explicit_origin_and_expiry(self):
        cfg = json.loads(self.config.read_text())
        cfg['allowed_targets'][0]['session_origin_cwd'] = str(self.root)
        self.config.write_text(json.dumps(cfg))
        self.rollout.write_text(json.dumps(dict(type='session_meta',payload=dict(id=self.session,cwd=str(self.root)))))
        record = attach(*self.common, self.rollout)
        self.assertEqual(record['session_origin_cwd'], str(self.root))
        self.assertEqual(record['checkout'], self.target['checkout'])
        path = self.root / 'state' / (self.session + '.attachment.json')
        record['expires_at'] = '2000-01-01T00:00:00+00:00'
        path.write_text(json.dumps(record))
        with self.assertRaises(ValueError): continue_session(*self.common, 'r2', 'hello')

    def test_no_recursive_resume_or_symlink_rollout(self):
        attach(*self.common, self.rollout)
        with patch.dict(os.environ, {'CODEX_THREAD_ID':self.session}):
            with self.assertRaises(ValueError): continue_session(*self.common, 'r2', 'hello', 'resume')
        link = self.root / 'linked.jsonl'; link.symlink_to(self.rollout)
        with self.assertRaises(OSError): attach(*self.common, link)

    def stub_codex(self, stdout='', exit_code=0):
        """A real `codex` executable on PATH that records argv/stdin (no sayhi-fakes needed)."""
        bin_dir = self.root / 'bin'; bin_dir.mkdir(exist_ok=True)
        stub = bin_dir / 'codex'
        stub.write_text(f"#!{sys.executable}\nimport json, sys\n"
                        f"open({str(self.root / 'argv.json')!r}, 'w').write(json.dumps([sys.argv[1:], sys.stdin.read()]))\n"
                        f"sys.stdout.write({stdout!r})\nsys.exit({exit_code})\n")
        stub.chmod(0o755)
        environment = patch.dict(os.environ, {'PATH': f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}"})
        environment.start(); self.addCleanup(environment.stop)
        return lambda: json.loads((self.root / 'argv.json').read_text())

    def test_queue_exact_receipt_and_shell_free(self):
        observed = self.stub_codex(f'Queued message 01a07387-d85b-78f3-8924-2e085ce13937 for thread {self.session}.\n')
        result = CodexBackend().deliver(self.session, '/tmp', 'literal $(example)', 'queue')
        self.assertEqual(result['status'], 'queued')
        self.assertEqual(observed()[0], ['queue', '--thread', self.session, '--message', 'literal $(example)'])
        self.assertEqual(observed()[1], '')
        self.stub_codex('', 1)
        self.assertEqual(CodexBackend().deliver(self.session, '/tmp', 'hello', 'resume')['status'], 'uncertain')

    def test_resume_requires_exact_thread_and_turn(self):
        events = '\n'.join(json.dumps(x) for x in [dict(type='thread.started',thread_id=self.session),dict(type='turn.completed')])
        observed = self.stub_codex(events)
        self.assertEqual(CodexBackend().deliver(self.session, '/tmp','hello','resume')['status'], 'turn-completed')
        self.assertEqual(observed(), [['exec', 'resume', '--json', self.session, '-'], 'hello'])
        self.stub_codex(events, 1)
        self.assertEqual(CodexBackend().deliver(self.session, '/tmp','hello','resume')['status'], 'uncertain')

    def test_missing_codex_is_unavailable(self):
        with patch.dict(os.environ, {'PATH': str(self.root / 'empty')}):
            self.assertEqual(CodexBackend().deliver(self.session, '/tmp', 'hello', 'resume')['status'], 'unavailable')

    def test_resume_outcome_order_and_terminal_rules(self):
        s = self.session
        start, turn, done = dict(type='thread.started', thread_id=s), dict(type='turn.started'), dict(type='turn.completed')
        item = dict(type='item.completed', item=dict(type='agent_message'))
        def text(*rows): return '\n'.join(r if isinstance(r, str) else json.dumps(r) for r in rows)
        accepted = [text(start, turn, item, done), text('[1]', 'not json', start, turn, done),
                    text(start, turn, dict(type='error', message='retrying'), done)]
        rejected = ['', text(start, turn), text(done, start), text(start, turn, done, item),
                    text(dict(type='thread.started', thread_id='other'), start, turn, done),
                    text(start, turn, dict(type='turn.failed', error={}), done), text(start, turn, done, done),
                    text(dict(type='thread.started', thread_id='other'), turn, done), text(start, turn, '{"type":"turn.completed"')]
        for value in accepted: self.assertTrue(resume_outcome(value, s), value)
        for value in rejected: self.assertFalse(resume_outcome(value, s), value)

if __name__ == '__main__': unittest.main()
