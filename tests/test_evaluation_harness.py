import tempfile
from pathlib import Path
import subprocess
import unittest

from experiments.cli_harness import command


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / "DISPOSABLE_TRIAL").touch()
        self.repo = self.root / "repo"
        self.call("init", str(self.repo))
        self.call("-C", str(self.repo), "-c", "user.name=Trial", "-c",
                  "user.email=trial@example.invalid", "commit", "--allow-empty", "-m", "base")
        self.checkout = self.root / "worker"
        self.call("-C", str(self.repo), "worktree", "add", "-b", "worker", str(self.checkout))
        self.output = self.root / "artifacts" / "final-message.md"

    def call(self, *args):
        subprocess.run(["git", *args], check=True, capture_output=True)

    def test_common_git_directory_explicitly_writable(self):
        args = command(self.root, self.checkout, self.output)
        self.assertIn(str(self.repo / ".git"), args)
        self.assertEqual(args[args.index("-s") + 1], "workspace-write")
        self.assertNotIn(str(self.root), args)

    def test_final_output_is_not_handoff(self):
        args = command(self.root, self.checkout, self.output)
        self.assertEqual(args[args.index("-o") + 1], str(self.output))
        with self.assertRaises(ValueError):
            command(self.root, self.checkout, self.checkout / "TRIAL_HANDOFF.md")

    def test_existing_output_is_preserved(self):
        self.output.parent.mkdir()
        self.output.write_text("original")
        with self.assertRaises(ValueError):
            command(self.root, self.checkout, self.output)
        self.assertEqual(self.output.read_text(), "original")

    def test_external_common_git_rejected(self):
        nested = self.root / "nested"
        nested.mkdir()
        (nested / "DISPOSABLE_TRIAL").touch()
        linked = nested / "worker"
        self.call("-C", str(self.repo), "worktree", "add", "-b", "linked", str(linked))
        with self.assertRaises(ValueError):
            command(nested, linked, nested / "final.md")

    def test_symlink_output_escape_rejected(self):
        (self.root / "escape").symlink_to(self.root.parent, target_is_directory=True)
        with self.assertRaises(ValueError):
            command(self.root, self.checkout, self.root / "escape" / "final.md")

    def test_remote_and_missing_marker_rejected(self):
        self.call("-C", str(self.repo), "remote", "add", "origin", "https://example.invalid/repo")
        with self.assertRaises(ValueError):
            command(self.root, self.checkout, self.output)
        self.call("-C", str(self.repo), "remote", "remove", "origin")
        (self.root / "DISPOSABLE_TRIAL").unlink()
        with self.assertRaises(ValueError):
            command(self.root, self.checkout, self.output)
