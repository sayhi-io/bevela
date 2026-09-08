import json
from pathlib import Path
import tempfile
import unittest

from experiments.isolation_v2 import command, run
from experiments.review_bundle import export


class IsolationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pi-isolation-v2-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'DISPOSABLE_TRIAL').touch()
        self.checkout = self.root / 'worker'
        self.checkout.mkdir()

    def test_broad_or_overlapping_mounts_rejected(self):
        for paths in [(self.root,), (Path('/home'),), (self.checkout,)]:
            with self.assertRaises(ValueError):
                command(self.root, self.checkout, ['true'], readonly=paths)

    def test_real_isolation_loopback_and_readonly_peer(self):
        peer = self.root / 'peer'; peer.mkdir()
        (peer / 'note').write_text('peer context')
        hidden = self.root / 'other-arm'; hidden.mkdir()
        (hidden / 'note').write_text('not visible')
        code = '''import socket, pathlib, json
p=pathlib.Path
assert not p(%r).exists()
assert not p('/home/meanaverage/.codex/skills').exists()
assert p(%r).read_text()=='peer context'
try:
 p(%r).write_text('changed')
except OSError: pass
else: raise AssertionError('peer writable')
s=socket.socket(); s.bind(('127.0.0.1',0)); s.listen(); s.close()
p('proof').write_text('local write allowed')
print('passed')
''' % (str(hidden), str(peer/'note'), str(peer/'note'))
        result = run(self.root, self.checkout, ['python3', '-c', code], readonly=[peer])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.checkout/'proof').read_text(), 'local write allowed')

    def test_handoff_preserved_and_manifest_bound(self):
        source = self.checkout / 'TRIAL_HANDOFF.md'
        source.write_text('Exact evidence from A-aware; not a final answer.')
        original = source.read_bytes()
        destination = self.root / 'review'
        audit = export(destination, {'owner.md': (source, 'a'*40)}, [('A-aware', 'candidate')])
        self.assertEqual(source.read_bytes(), original)
        self.assertIn('candidate', (destination/'owner.md').read_text())
        self.assertNotIn('A-aware', (destination/'manifest.json').read_text())
        self.assertEqual(json.loads((destination/'manifest.json').read_text())['owner.md']['sha256'],
                         audit['artifacts']['owner.md']['review_sha256'])
        with self.assertRaises(ValueError):
            export(destination, {'owner.md': (source, 'a'*40)})

    def test_missing_handoff_fails_before_creating_bundle(self):
        destination = self.root / 'review'
        with self.assertRaises(FileNotFoundError):
            export(destination, {'owner.md': (self.checkout/'missing', 'a'*40)})
        self.assertFalse(destination.exists())
