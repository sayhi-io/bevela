import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from experiments import qwen_compact_pi_v2 as route

SOURCE = Path(__file__).resolve().parents[1]


class QwenWorkerCLITests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        parent = Path(temp.name)
        runtime = parent / 'runtime/bin'
        runtime.mkdir(parents=True)
        (runtime / 'qwen').write_text('console.log("0.23.2");\n')
        self.engine = route.runner()
        self.root = self.engine.prepare(parent / 'trial', 'C', SOURCE,
                                        runtime.parent, 'http://127.0.0.1:8078/v1', 5)
        self.cli = [sys.executable, '-B', '-I', str(self.root / 'pi-source/project_intent/_worker_cli.py')]
        self.options = ['--worker-config', '.pi/worker.json', '--scope', self.engine.common.SCOPE,
                        '--workstream', 'PRODUCER']

    def call(self, *args):
        return subprocess.run(self.cli + list(args), cwd=self.root / 'work',
                              capture_output=True, text=True, timeout=15)

    def test_help_errors_and_generated_commands_stay_on_filtered_route(self):
        help_result = self.call('--help')
        self.assertEqual(help_result.returncode, 0)
        self.assertNotIn('presence', help_result.stdout)
        self.assertNotIn('presence', self.call('invalid-command').stderr)
        oriented = self.call('onboard', *self.options)
        self.assertEqual(oriented.returncode, 0, oriented.stderr)
        self.assertIn(self.cli[-1], oriented.stdout)
        context = json.loads(self.call('start', *self.options).stdout)['integration_context']
        refreshed = subprocess.run(context['refresh']['argv'] + ['--help'],
                                   capture_output=True, text=True, timeout=15)
        self.assertEqual(refreshed.returncode, 0)
        self.assertNotIn('presence', refreshed.stdout)

    def test_hidden_command_cannot_overwrite_enrollment_and_renewal_works(self):
        args = self.options + ['--session', 'qwen-test', '--access', 'edit', '--touching-path', 'catalog.py']
        self.assertEqual(self.call('enroll', *args).returncode, 0)
        before = self.engine.manifest(self.root / 'work/.pi/presence')
        self.assertEqual(self.call('presence', *args).returncode, 2)
        self.assertEqual(self.engine.manifest(self.root / 'work/.pi/presence'), before)
        self.assertEqual(self.call('enroll', *args, '--working', 'renewed').returncode, 0)
        self.assertEqual(self.call('enroll', *args, '--inactive').returncode, 0)

    def test_general_backend_and_frozen_prompt_unchanged(self):
        general = subprocess.run([sys.executable, '-B', '-I', str(SOURCE / 'project_intent/_worker_cli.py'), '--help'],
                                 capture_output=True, text=True, timeout=15)
        self.assertIn('presence', general.stdout)
        self.assertEqual((self.root / 'pi-source/project_intent/cli.py').read_bytes(),
                         (SOURCE / 'project_intent/cli.py').read_bytes())
        self.assertEqual((self.root / 'work/AGENTS.md').read_text(),
                         route.compact.instructions(self.engine.common.SCOPE))
        self.engine.verify(self.root)
        self.engine.preflight(self.root)

    def test_modified_adapter_rejected(self):
        (self.root / 'pi-source/project_intent/_worker_cli.py').write_text('different')
        with self.assertRaises(ValueError):
            self.engine.verify(self.root)

    def test_one_run_does_not_change_historical_defaults(self):
        single = route.runner(1)
        self.assertEqual(single.ORDER, ('C1',))
        self.assertEqual(route.compact.PROFILE['runs'], 3)
        self.assertEqual(route.runner().ORDER, ('C1', 'C2', 'C3'))
        with self.assertRaises(ValueError):
            route.runner(0)
