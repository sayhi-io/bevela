import json
from pathlib import Path
import tempfile
import unittest

from experiments import qwen_distributed_cap500 as route

SOURCE = Path(__file__).resolve().parents[1]


class CapTests(unittest.TestCase):
    def test_only_cap_diff_and_private_modules(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            runtime = parent / 'runtime/bin'
            runtime.mkdir(parents=True)
            (runtime / 'qwen').write_text('console.log("0.23.2");\n')
            old_settings = route.previous.profiles.settings
            old = route.previous.runner()
            new = route.runner()
            a = old.prepare(parent / 'old', SOURCE, runtime.parent, 'http://localhost:8078/v1')
            b = new.prepare(parent / 'new', SOURCE, runtime.parent, 'http://localhost:8078/v1')
            pa, pb = old.verify(a, before=True), new.verify(b, before=True)
            self.assertIs(route.previous.profiles.settings, old_settings)
            for key in ('fixture_manifest', 'input_hashes', 'runtime_manifest', 'treatment_hashes',
                        'qwen_profile', 'timeout_seconds', 'compact_template_sha256'):
                self.assertEqual(pa[key], pb[key], key)
            sa = json.loads((a / 'settings-template.json').read_text())
            sb = json.loads((b / 'settings-template.json').read_text())
            self.assertEqual(sb['model'].pop('maxToolCallsPerTurn'), 500)
            self.assertEqual(sa, sb)
            self.assertEqual((a / 'work/AGENTS.md').read_bytes(), (b / 'work/AGENTS.md').read_bytes())
            self.assertEqual({k:v for k,v in pa['pi_manifest'].items() if k != 'steering.json'},
                             {k:v for k,v in pb['pi_manifest'].items() if k != 'steering.json'})
            new.preflight(b)
            self.assertTrue(set(pa['sessions'].values()).isdisjoint(pb['sessions'].values()))
            (b / 'started.json').write_text('{}')
            with self.assertRaises(FileExistsError):
                new.run(b)
            settings_file = b / 'settings-template.json'
            actual = json.loads(settings_file.read_text())
            actual['model']['maxToolCallsPerTurn'] = 501
            settings_file.write_text(json.dumps(actual))
            with self.assertRaises((AssertionError, ValueError)):
                new.verify(b)


if __name__ == '__main__':
    unittest.main()
