import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "publish_loopback", ROOT / "scripts/publish_loopback.py"
)
publish_loopback = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publish_loopback)


class PublishLoopbackTests(unittest.TestCase):
    def test_command_failure_includes_suppressed_output(self):
        with self.assertRaisesRegex(publish_loopback.PublishError, "useful failure"):
            publish_loopback.run(["sh", "-c", "echo useful failure; exit 7"])

    def test_lock_release_preserves_only_executable_bit(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as external_directory:
            root = Path(directory)
            plain = root / "plain"
            executable = root / "executable"
            external = Path(external_directory) / "external"
            plain.write_text("plain")
            executable.write_text("executable")
            executable.chmod(0o755)
            external.write_text("external")
            external.chmod(0o755)
            (root / "external-link").symlink_to(external)
            publish_loopback.lock_release(root)
            self.assertEqual(plain.stat().st_mode & 0o777, 0o444)
            self.assertEqual(executable.stat().st_mode & 0o777, 0o555)
            self.assertEqual(external.stat().st_mode & 0o777, 0o755)
            self.assertEqual(root.stat().st_mode & 0o777, 0o555)

    def test_defaults_are_the_dogfood_route(self):
        args = publish_loopback.parser().parse_args([])
        self.assertEqual(args.unit, "project-intent-dogfood.service")
        self.assertEqual(args.port, 8290)
        self.assertEqual(args.state_dir, Path.home() / "sayhi/state/project-intent")

    def test_virtual_environment_is_built_at_the_final_release_path(self):
        source = (ROOT / "scripts/publish_loopback.py").read_text()
        rename = source.index("pending.rename(destination)")
        venv = source.index('"-m", "venv"')
        self.assertLess(rename, venv)

    def test_failed_rename_cleanup_preserves_unowned_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pending = root / "pending"
            destination = root / "destination"
            pending.mkdir()
            destination.mkdir()
            marker = destination / "owned-by-someone-else"
            marker.write_text("keep")
            publish_loopback.clean_failed_candidate(pending, destination, promoted=False)
            self.assertFalse(pending.exists())
            self.assertEqual(marker.read_text(), "keep")

    def test_publish_lock_rejects_a_concurrent_publisher(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            with publish_loopback.publish_lock(state):
                with self.assertRaisesRegex(publish_loopback.PublishError, "already running"):
                    with publish_loopback.publish_lock(state):
                        self.fail("concurrent lock unexpectedly acquired")

    def test_restore_repoints_restarts_and_verifies_old_release(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            current = state / "current"
            newer = state / "releases/new/source"
            old = state / "releases/old/source"
            newer.mkdir(parents=True)
            old.mkdir(parents=True)
            current.symlink_to(newer)
            with mock.patch.object(publish_loopback, "run") as run, mock.patch.object(
                publish_loopback, "verify_service"
            ) as verify:
                publish_loopback.restore_release(state, current, old, "example.service", "12")
            self.assertEqual(current.resolve(), old)
            run.assert_called_once_with(["systemctl", "--user", "restart", "example.service"])
            verify.assert_called_once_with("example.service", old, "12")


if __name__ == "__main__":
    unittest.main()
