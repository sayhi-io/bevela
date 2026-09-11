import copy
from datetime import timedelta
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from project_intent.enrollment import registration, read_registrations
from project_intent.model import project, utcnow, valid_presence
from project_intent.runtime import write_json
from project_intent.runtime_identity import runtime_session_ref, validate_runtime_session
from project_intent.worker_context import checkout_identity, nearby_workers, integration_context

ROOT = Path(__file__).resolve().parents[1]
THREAD = '550e8400-e29b-41d4-a716-446655440000'


class RuntimeIdentityTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = json.loads((ROOT / '.project-intent/snapshot.json').read_text())
        self.scope = self.snapshot['scope_id']
        self.checkout = checkout_identity(ROOT)
        self.ref = {'runtime': 'codex', 'id': THREAD, 'host': self.checkout['host'], 'instance': 'local-codex'}

    def record(self, **kwargs):
        record = registration(self.snapshot, 'PI-MISSION-01', 'runner', 'work', [], [], **kwargs)
        record['checkout'] = self.checkout
        return record

    def test_separate_pi_and_runtime_id_survives_renew_and_release(self):
        for runtime in ('codex', 'qwen-code'):
            with self.subTest(runtime=runtime):
                ref = dict(self.ref, runtime=runtime)
                first = self.record(runtime_session=ref)
                renewed = self.record(old=first)
                released = self.record(old=renewed, inactive=True)
                self.assertEqual(released['session'], 'runner')
                self.assertEqual(released['runtime_session'], ref)
                self.assertIsNone(released['telemetry'])
                self.assertEqual(self.record(old=released)['runtime_session'], ref)

    def test_rebinding_conversation_host_or_instance_is_rejected(self):
        first = self.record(runtime_session=self.ref)
        for key, value in (('id', 'another'), ('host', 'another-host'), ('runtime', 'qwen-code'), ('instance', 'other')):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.record(old=first, runtime_session=dict(self.ref, **{key: value}))

    def test_legacy_codex_is_explicit_only_with_telemetry_metadata(self):
        plain = self.record()
        plain['session'] = THREAD
        self.assertIsNone(runtime_session_ref(plain))
        plain['telemetry'] = {'kind': 'codex-local-usage', 'path': '/not/read'}
        expected = {k: self.ref[k] for k in ('runtime', 'id', 'host')}
        self.assertEqual(runtime_session_ref(plain), expected)
        self.assertEqual(registration(self.snapshot, 'PI-MISSION-01', THREAD, '', [], [], old=plain)['runtime_session'], expected)

    def test_invalid_or_mismatched_telemetry_reference_rejected(self):
        for field, value in (('id', ''), ('id', '../file'), ('id', 'x' * 201), ('host', []),
                             ('runtime', 'qwen3.8'), ('instance', 'https://token@host'), ('authority', 'deploy')):
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_runtime_session(dict(self.ref, **{field: value}))
        with self.assertRaises(ValueError):
            self.record(path='/telemetry', runtime_session=self.ref)
        malformed = self.record()
        malformed['runtime_session'] = dict(self.ref, id=['not-text'])
        self.assertFalse(valid_presence(malformed))

    def test_scoped_views_and_peer_context_keep_reference(self):
        record = self.record(runtime_session=self.ref)
        record['touching_seams'] = ['intent/projection']
        state = {'id': self.scope, 'label': 'test', 'provider_status': 'offline', 'snapshot': self.snapshot, 'presence': [record]}
        view = project([state], [self.scope])
        self.assertEqual(view['sessions'][0]['runtime_session'], self.ref)
        self.assertNotIn(THREAD, json.dumps(project([state], ['other'])))
        nearby = nearby_workers([state], self.checkout, [], [], self.scope)
        self.assertEqual(nearby[0]['runtime_session'], self.ref)
        selected = next(r for r in self.snapshot['records'] if r['id'] == 'PI-MISSION-01')
        context = integration_context(state, selected, self.checkout)
        self.assertEqual(context['last_known_workers'][0]['runtime_session'], self.ref)
        expired = copy.deepcopy(record)
        for key in ('claimed_at', 'heartbeat_at', 'expires_at'):
            expired[key] = (utcnow() - timedelta(hours=2 if key == 'expires_at' else 3)).isoformat()
        state['presence'] = [expired]
        row = project([state], [self.scope])['sessions'][0]
        self.assertEqual(row['status'], 'expired')
        self.assertEqual(row['runtime_session'], self.ref)

    def test_file_roundtrip_keeps_reference_without_telemetry(self):
        with tempfile.TemporaryDirectory() as directory:
            write_json(Path(directory) / 'runner.json', self.record(runtime_session=self.ref))
            rows, failures = read_registrations({'directory': directory}, self.scope, {'PI-MISSION-01'})
            self.assertEqual(failures, 0)
            self.assertEqual(rows[0][0]['runtime_session'], self.ref)
            self.assertIsNone(rows[0][1])

    def cli(self, directory, extra=(), env=None):
        return subprocess.run([sys.executable, '-m', 'project_intent.cli', 'enroll',
            '--snapshot', str(ROOT / '.project-intent/snapshot.json'), '--workstream', 'PI-MISSION-01',
            '--session', 'runner', '--directory', directory, *extra],
            cwd=ROOT, env=env, capture_output=True, text=True)

    def test_cli_qwen_and_codex_aliases_need_no_transcript(self):
        for runtime in ('codex', 'qwen-code'):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as directory:
                result = self.cli(directory, ['--runtime', runtime, '--runtime-session', THREAD])
                self.assertEqual(result.returncode, 0, result.stderr)
                output = json.loads(result.stdout)
                self.assertEqual(output['runtime_session']['id'], THREAD)
                self.assertEqual(output['runtime_session']['runtime'], runtime)
                self.assertEqual(output['telemetry'], 'not-connected')
                renewed = self.cli(directory)
                self.assertEqual(json.loads(renewed.stdout)['runtime_session'], output['runtime_session'])
                released = self.cli(directory, ['--inactive'])
                self.assertEqual(json.loads(released.stdout)['runtime_session'], output['runtime_session'])

    def test_cli_partial_or_invalid_reference_does_not_write(self):
        for extra in (['--runtime', 'codex'], ['--runtime-session', THREAD],
                      ['--runtime', 'qwen-code', '--runtime-session', '../bad'],
                      ['--runtime-instance', 'daemon']):
            with self.subTest(extra=extra), tempfile.TemporaryDirectory() as directory:
                result = self.cli(directory, extra)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((Path(directory) / 'runner.json').exists())

    def test_codex_flag_adds_reference_and_preserves_instance_on_renew(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'rollout.jsonl'
            path.write_text(json.dumps({'type': 'session_meta', 'payload': {'id': 'runner'}}) + '\n')
            result = self.cli(directory, ['--codex', '--telemetry-file', str(path), '--runtime-instance', 'local-codex'])
            self.assertEqual(result.returncode, 0, result.stderr)
            ref = json.loads(result.stdout)['runtime_session']
            self.assertEqual(ref['runtime'], 'codex')
            self.assertEqual(ref['id'], 'runner')
            renewed = self.cli(directory, ['--codex'])
            self.assertEqual(renewed.returncode, 0, renewed.stderr)
            self.assertEqual(json.loads(renewed.stdout)['runtime_session'], ref)

    def test_codex_env_selects_own_thread_and_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            logs = root / 'sessions/2026/09/10'
            logs.mkdir(parents=True)
            (logs / ('rollout-test-' + THREAD + '.jsonl')).write_text(
                json.dumps({'type': 'session_meta', 'payload': {'id': THREAD}}) + '\n')
            command = [sys.executable, '-m', 'project_intent.cli', 'enroll', '--codex',
                       '--snapshot', str(ROOT / '.project-intent/snapshot.json'),
                       '--workstream', 'PI-MISSION-01', '--directory', str(root / 'presence')]
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                                    env=dict(os.environ, CODEX_HOME=directory, CODEX_THREAD_ID=THREAD))
            self.assertEqual(result.returncode, 0, result.stderr)
            output = json.loads(result.stdout)
            self.assertEqual(output['session'], THREAD)
            self.assertEqual(output['runtime_session']['id'], THREAD)
