import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from experiments import qwen_distributed_steering as route
from experiments import qwen_nested_steering_hook as nested

SOURCE = Path(__file__).resolve().parents[1]


class DistributedSteeringTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.parent = Path(temporary.name)
        self.runtime = self.parent / 'runtime'
        (self.runtime / 'bin').mkdir(parents=True)
        (self.runtime / 'bin/qwen').write_text('console.log("0.23.2");\n')

    def prepare(self):
        engine = route.runner()
        root = engine.prepare(self.parent / 'trial', SOURCE, self.runtime, 'http://127.0.0.1:8078/v1')
        return engine, root

    def test_unchanged_fixture_tasks_and_checker(self):
        engine, root = self.prepare()
        plan = engine.verify(root, before=True)
        actual = engine.manifest(root / 'work')
        for name, value in plan['fixture_manifest'].items():
            self.assertEqual(actual[name], value, name)
        for role in plan['roles']:
            self.assertEqual((root / (role + '.txt')).read_bytes(), (root / 'work/tasks' / (role + '.txt')).read_bytes())
        self.assertEqual(engine.sha(root / 'check_contract.py'), engine.sha(root / 'work/acceptance.py'))
        self.assertEqual(len(set(plan['sessions'].values())), 4)
        self.assertEqual(plan['server_effort'], 'medium')
        settings = json.loads((root / 'settings-template.json').read_text())
        self.assertEqual(settings['model']['reasoningEffort'], 'none')
        self.assertFalse(settings['modelProviders']['openai'][0]['generationConfig']['extra_body']['chat_template_kwargs']['enable_thinking'])
        self.assertNotIn('Read `', (root / 'work/AGENTS.md').read_text())

    def test_real_hook_nested_source_and_all_roles(self):
        engine, root = self.prepare()
        engine.preflight(root)
        plan = engine.verify(root, before=True)
        config = json.loads((root / 'pi-source/steering.json').read_text())
        self.assertEqual(len(config['baseline']), 12)
        self.assertNotIn('acceptance.py', config['baseline'])
        self.assertIn('catalog/CONTRACT.md', config['baseline'])
        for role in plan['roles']:
            event = dict(session_id=plan['sessions'][role], cwd=str(root / 'work'), hook_event_name='UserPromptSubmit')
            env = {**os.environ, 'HOME': str(root / 'qwen-home' / role), 'QWEN_SESSION_ID': event['session_id']}
            def call():
                return subprocess.run(['/usr/bin/python3', '-B', '-I', str(root / 'pi-source/qwen_nested_steering_hook.py')],
                    input=json.dumps(event), capture_output=True, text=True, env=env, check=True)
            result = call()
            self.assertEqual(result.stderr, '')
            self.assertIn('PI update:', result.stdout)
            path = root / 'work' / role / 'CONTRACT.md'
            path.write_text(path.read_text() + '\nNew contract observation\n')
            self.assertIn(role + '/CONTRACT.md', call().stdout)
            self.assertEqual(json.loads(call().stdout), {})

    def test_nested_symlink_and_escape_refused(self):
        work = self.parent / 'work'
        work.mkdir()
        (work / 'component').symlink_to(self.runtime, target_is_directory=True)
        for name in ('../runtime/bin/qwen', '/etc/passwd', 'component/bin/qwen'):
            with self.assertRaises((ValueError, OSError)):
                nested.file_digest(work, name)
        self.assertEqual(nested.file_digest(work, 'missing/file.py'), 'missing')

    def test_changes_fenced_and_no_rerun(self):
        engine, root = self.prepare()
        (root / 'started.json').write_text('{}')
        with self.assertRaises(FileExistsError):
            engine.run(root)
        (root / 'catalog.txt').write_text('Different task')
        with self.assertRaises(AssertionError):
            engine.verify(root)


if __name__ == '__main__':
    unittest.main()
