"""The explicit source seal includes publication assets, never arbitrary binaries."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/project-intent/scripts/seal_source.py"
spec = importlib.util.spec_from_file_location("source_seal", SCRIPT)
seal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seal)


class SourceSealTests(unittest.TestCase):
    def test_only_exact_publication_assets_are_eligible(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in seal.SOURCE_ASSETS:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"source fixture")
                self.assertEqual(seal.source_path(root, name), path)
            for name in ("project_intent/web/other.woff2", "project_intent/web/private.txt",
                         "scripts/unreviewed.bin", "state/inter-variable.woff2"):
                with self.assertRaises(ValueError):
                    seal.source_path(root, name)

    def test_exact_asset_does_not_allow_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            asset = root / "project_intent/web/inter-variable.woff2"
            asset.parent.mkdir(parents=True)
            target = root / "private"
            target.write_bytes(b"not source")
            asset.symlink_to(target)
            with self.assertRaisesRegex(ValueError, "Symlink refused"):
                seal.source_path(root, "project_intent/web/inter-variable.woff2")
