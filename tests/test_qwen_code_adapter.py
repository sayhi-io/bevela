from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import shutil
import socket
from pathlib import Path
import subprocess
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen

from experiments import qwen_code_adapter as adapter
from experiments import qwen_distributed_study as study
from experiments import qwen_boundary_resume as boundary

ROOT = Path(__file__).resolve().parents[1]


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='qwen-adapter-unit-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_context_thinking_native_instructions_and_compaction(self):
        settings = adapter.settings('local-qwen', 'http://127.0.0.1:1234/v1')
        generation = settings['modelProviders']['openai'][0]['generationConfig']
        self.assertEqual(generation['contextWindowSize'], 230000)
        self.assertEqual(generation['extra_body']['reasoning_effort'], 'xhigh')
        self.assertTrue(generation['extra_body']['chat_template_kwargs']['enable_thinking'])
        self.assertEqual(settings['context']['fileName'], ['AGENTS.md', 'QWEN.md'])
        self.assertEqual(settings['context']['autoCompactThreshold'], .85)
        self.assertFalse(settings['general']['enableAutoUpdate'])
        self.assertNotIn('fallback', settings)

    def test_reject_oversized_context_and_url_credentials(self):
        with self.assertRaises(ValueError):
            adapter.settings('q', 'http://localhost/v1', 262144)
        with self.assertRaises(ValueError):
            adapter.settings('q', 'http://secret:value@localhost/v1')
        for endpoint in ('http:///v1', 'http://localhost/v1?key=private', 'http://localhost/v1#private'):
            with self.assertRaises(ValueError):
                adapter.settings('q', endpoint)

    def test_cli_is_native_not_a_custom_model_loop(self):
        argv = adapter.argv('/trial', 'Complete task', 'local-qwen', 'session')
        self.assertEqual(argv[-1], 'Complete task')
        self.assertIn('--session-id', argv)
        self.assertIn('--approval-mode', argv)
        self.assertIn('stream-json', argv)
        self.assertNotIn('--system-prompt', argv)

    def test_usage_counts_cached_input_as_subset_and_top_level_reasoning(self):
        path = self.root / 'transport.jsonl'
        rows = [{'event': 'request', 'request': 1}, {'event': 'request', 'request': 2},
            {'event':'usage','request':1,'usage':{'prompt_tokens':100,'completion_tokens':20,
                'prompt_tokens_details':{'cached_tokens':60},'reasoning_tokens':12}},
            {'event':'usage','request':2,'usage':{'prompt_tokens':200,'completion_tokens':30,
                'completion_tokens_details':{'reasoning_tokens':15}}}]
        path.write_text('\n'.join(map(json.dumps, rows)))
        value = adapter.usage(path)
        self.assertEqual((value['input_tokens'], value['cached_input_tokens'], value['output_tokens']), (300,60,50))
        self.assertEqual(value['reasoning_tokens'], 27)
        self.assertTrue(value['complete_usage'])

    def test_partial_usage_is_explicit(self):
        path = self.root / 'transport.jsonl'
        path.write_text(json.dumps({'event':'request','request':1})+'\n')
        value = adapter.usage(path)
        self.assertFalse(value['complete_usage'])
        self.assertIsNone(value['reasoning_tokens'])

    def test_absent_transport_usage_is_unknown_not_complete(self):
        value = adapter.usage(self.root/'missing.jsonl')
        self.assertFalse(value['complete_usage'])
        self.assertEqual(value['requests'],0)

    def test_relay_preserves_request_and_response_bytes(self):
        seen = []
        response = (b'data: {"choices":[{"delta":{"reasoning_content":"test"}}]}\n\n'
                    b'data: {"usage":{"prompt_tokens":10,"completion_tokens":3}}\n\n'
                    b'data: [DONE]\n\n')
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_): pass
            def do_POST(self):
                seen.append(self.rfile.read(int(self.headers['Content-Length'])))
                self.send_response(200)
                self.send_header('Content-Type','text/event-stream')
                self.end_headers()
                self.wfile.write(response)
        server = ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread = threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        request = b'{"model":"q", "messages":[],"stream":true,"reasoning_effort":"xhigh"}'
        try:
            with adapter.Relay(f'http://127.0.0.1:{server.server_port}/v1', self.root/'transport.jsonl') as endpoint:
                with urlopen(Request(endpoint+'/chat/completions',data=request),timeout=5) as reply:
                    self.assertEqual(reply.read(),response)
            self.assertEqual(seen,[request])
            self.assertTrue(adapter.usage(self.root/'transport.jsonl')['reasoning_observed'])
        finally:
            server.shutdown()
            server.server_close()

    def test_close_delimited_response_handler_finishes_before_exit(self):
        sent = threading.Event()
        release = threading.Event()
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_): pass
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'data: {}\n\n')
                self.wfile.flush()
                sent.set()
                release.wait(5)
        server = ThreadingHTTPServer(('127.0.0.1',0),Handler)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        relay = adapter.Relay(f'http://127.0.0.1:{server.server_port}/v1',self.root/'closing.jsonl')
        try:
            with relay as endpoint:
                reply = urlopen(Request(endpoint+'/chat/completions',data=b'{"stream":true}'),timeout=5)
                self.assertTrue(sent.wait(2))
                self.assertEqual(reply.read(10),b'data: {}\n\n')
            self.assertFalse(relay.handlers)
            size = relay.output.stat().st_size
            time.sleep(.05)
            self.assertEqual(relay.output.stat().st_size,size)
            reply.close()
        finally:
            release.set()
            server.shutdown()
            server.server_close()

    def test_handler_registered_before_thread_starts(self):
        relay = adapter.Relay('http://127.0.0.1:1234/v1',self.root/'registration.jsonl')
        client, peer = socket.socketpair()
        seen = []
        def start(thread):
            seen.append(thread in relay.handlers and client in relay.sockets)
        try:
            with patch.object(threading.Thread,'start',start):
                relay.server.process_request(client,('local',1))
            self.assertEqual(seen,[True])
        finally:
            client.close()
            peer.close()
            relay.server.server_close()


class QwenStudyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='qwen-study-unit-')
        self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name)
        self.runtime = self.parent/'runtime'
        (self.runtime/'bin').mkdir(parents=True)
        (self.runtime/'bin/qwen').write_text('console.log("test")')

    def prepare(self, condition):
        return study.prepare(self.parent/condition,condition,ROOT,self.runtime,'http://127.0.0.1:1234/v1','test-qwen')

    def test_exact_fixture_and_prompts_preserved_across_arms(self):
        ordinary, aware = self.prepare('B'), self.prepare('C')
        fixture = ROOT/'experiments/assets/distributed_v2/fixture'
        for file in fixture.rglob('*'):
            if file.is_file() and '__pycache__' not in str(file):
                relative = file.relative_to(fixture)
                self.assertEqual((ordinary/'work'/relative).read_bytes(),file.read_bytes())
                self.assertEqual((aware/'work'/relative).read_bytes(),file.read_bytes())
        for role in study.base.ROLES:
            self.assertEqual((ordinary/(role+'.txt')).read_bytes(),(aware/(role+'.txt')).read_bytes())
        self.assertFalse((ordinary/'pi-source').exists())
        self.assertNotIn('CODEX_THREAD_ID',(aware/'work/AGENTS.md').read_text())
        self.assertIn('QWEN_SESSION_ID',(aware/'work/AGENTS.md').read_text())
        study.verify(ordinary,before=True)
        study.verify(aware,before=True)

    def test_fresh_home_and_exact_inputs_fenced(self):
        root = self.prepare('B')
        (root/'qwen-home/catalog/old-chat.json').write_text('old')
        with self.assertRaisesRegex(AssertionError,'not fresh'):
            study.verify(root,before=True)

    def test_frozen_checker_tampering_rejected(self):
        root = self.prepare('B')
        (root/'check_contract.py').write_text('print("pass")')
        with self.assertRaises(AssertionError):
            study.verify(root)

    def test_runtime_tampering_rejected(self):
        root = self.prepare('B')
        (root/'runtime/bin/qwen').write_text('modified')
        with self.assertRaises(AssertionError):
            study.verify(root)

    def test_native_mount_isolation(self):
        root = self.prepare('C')
        study.preflight(root)

    def test_reference_still_passes_fifteen_groups(self):
        fixture = ROOT/'experiments/assets/distributed_v2'
        source = self.parent/'reference'
        shutil.copytree(fixture/'fixture',source)
        shutil.copytree(fixture/'reference',source,dirs_exist_ok=True)
        # The historical evaluator mounts npm even for Python-only scoring.
        # Supply an empty disposable prefix, never the operator's installation.
        (self.parent / '.npm-global').mkdir()
        with patch.object(Path, 'home', return_value=self.parent):
            result = study.base.score(source,fixture/'fixture/acceptance.py')
        self.assertTrue(result['accepted'],result)
        self.assertEqual(len(result['groups']),15)

    def test_primary_study_rejects_unplanned_single_arm(self):
        with self.assertRaises(ValueError):
            self.prepare('A')

    def test_exact_five_per_arm(self):
        self.assertEqual(sum(r.startswith('B') for r in study.ORDER),5)
        self.assertEqual(sum(r.startswith('C') for r in study.ORDER),5)
        self.assertEqual(len(set(study.ORDER)),10)

    def test_restart_does_not_skip_retained_infrastructure_failure(self):
        batch = self.parent/'batch'
        root = batch/'B1'
        root.mkdir(parents=True)
        (root/'plan.json').write_text('{}')
        (root/'result.json').write_text(json.dumps({'native_identity_verified':False,'infrastructure_errors':[]}))
        (batch/'frozen.json').write_text(json.dumps({'order':['B1'],
            'study_sha256':study.sha(study.__file__),'adapter_sha256':study.sha(adapter.__file__),
            'sequencing_policy':boundary.policy_identity(),
            'plans':{'B1':study.sha(root/'plan.json')}}))
        with patch.object(study,'run') as execute, patch.object(boundary, 'disposition',
                side_effect=RuntimeError('Retained trial has unexplained failure')) as classify:
            with self.assertRaisesRegex(RuntimeError,'Retained trial'):
                study.run_all(batch)
            execute.assert_not_called()
            classify.assert_called_once_with(root)

    def test_sequencing_policy_is_frozen_before_any_execution(self):
        batch = self.parent/'policy-freeze'
        with patch.object(study, 'ORDER', ('B1', 'C1')), patch.object(study, 'preflight'):
            study.freeze(batch, ROOT, self.runtime, 'http://127.0.0.1:1234/v1', 'test-qwen')
        frozen = json.loads((batch/'frozen.json').read_text())
        self.assertEqual(frozen['sequencing_policy'], boundary.policy_identity())
        self.assertFalse(list(batch.glob('*/started.json')))

    def test_wrong_native_identity_and_no_transport_are_retained(self):
        root = self.prepare('B')
        directory = root/'catalog'
        directory.mkdir()
        plan = study.verify(root,before=True)
        row = {'role':'catalog','session':plan['sessions']['catalog']}
        (directory/'stdout.jsonl').write_text(json.dumps({'type':'system','subtype':'init',
            'model':'wrong','session_id':'foreign'})+'\n')
        value = study.worker_analysis(root,row)
        self.assertFalse(value['native_identity_verified'])
        self.assertFalse(value['usage']['complete_usage'])
        (directory/'transport.jsonl').write_text(json.dumps({'event':'request','request':1,
            'model':'wrong','reasoning_effort':'xhigh','chat_template_kwargs':{'enable_thinking':True}})+'\n')
        self.assertFalse(study.worker_analysis(root,row)['native_identity_verified'])


if __name__ == '__main__':
    unittest.main()
