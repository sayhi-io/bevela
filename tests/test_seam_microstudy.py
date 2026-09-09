import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from experiments import seam_microstudy as study
from project_intent.model import validate_snapshot


class SeamMicrostudyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = study.prepare(Path(self.temp.name))

    def test_identical_source_and_prompts_control_has_no_coordination(self):
        for source in (study.ASSETS / "fixture").iterdir():
            for arm in ("control", "pi"):
                self.assertEqual(source.read_bytes(), (self.root / arm / "work" / source.name).read_bytes())
        self.assertFalse((self.root / "control/work/AGENTS.md").exists())
        self.assertFalse((self.root / "control/work/.pi").exists())
        self.assertEqual(len(list((self.root / "control/work").iterdir())), 6)
        for task in study.TASKS:
            self.assertEqual((self.root / f"{task}.txt").read_text(), study.task_text(task))

    def test_real_pi_schema_with_shared_semantic_surface_no_invented_presence(self):
        context = self.root / "pi/work/.pi"
        snapshot = validate_snapshot(json.loads((context / "snapshot.json").read_text()))
        first, second = snapshot["records"]
        self.assertEqual(set(first["boundaries"]) & set(second["boundaries"]), {"shop/money"})
        self.assertFalse((context / "presence").exists())
        self.assertNotIn("conformance_assertions", first)
        cli = subprocess.run([sys.executable, "-m", "project_intent.cli", "onboard", "--worker-config", str(context / "worker.json"),
                              "--scope", study.SCOPE, "--workstream", "PRICES"],
                             cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
        self.assertEqual(cli.returncode, 0, cli.stderr)
        response = json.loads(cli.stdout)
        self.assertEqual(response["orientation"]["assignment"]["id"], "PRICES")
        self.assertTrue(response["orientation"]["convergence"])

    def test_native_command_not_custom_agent_or_configuration_reset(self):
        argv = study.command("codex", Path("/task"), "do task", "gpt-5.6-luna", "medium")
        self.assertEqual(argv, ["codex", "exec", "--json", "--sandbox", "workspace-write", "-m", "gpt-5.6-luna", "-c",
                                'model_reasoning_effort="medium"', "-C", "/task", "do task"])

    def test_recorder_preserves_raw_bytes_and_does_not_send_followups(self):
        class Process:
            pid = 123

            def __init__(inner, argv, **kwargs):
                self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
                self.assertNotIn("env", kwargs)
                kwargs["stdout"].write(b'{"arbitrary":"raw"}\n\x00\xff')
                kwargs["stderr"].write(b"warning\r\n\xff")

            def wait(inner):
                return 7

        with patch.object(study.subprocess, "Popen", Process):
            result = study.record(self.root, "control", "prices", "codex", "luna", "medium")
        self.assertEqual(result["exit_code"], 7)
        self.assertGreaterEqual(result["elapsed_seconds"], 0)
        self.assertEqual((self.root / "control/prices/stdout.jsonl").read_bytes(), b'{"arbitrary":"raw"}\n\x00\xff')
        self.assertEqual((self.root / "control/prices/stderr.bin").read_bytes(), b"warning\r\n\xff")

    def test_run_keeps_uncommitted_output_and_never_reruns_or_repairs(self):
        calls = []

        def record(root, arm, task, *args):
            calls.append((arm, task))
            (root / arm / "work" / f"{task}.bin").write_bytes(b"\x00\xff")
            return {"arm": arm, "task": task, "exit_code": 0,
                    "start_monotonic_ns": 10, "end_monotonic_ns": 20}

        with patch.object(study, "record", side_effect=record), \
             patch.object(study.shutil, "which", return_value="codex"), \
             patch.object(study.subprocess, "check_output", return_value="codex-cli test"):
            study.run(self.root)
            with self.assertRaises(ValueError):
                study.run(self.root)
        self.assertCountEqual(calls, [(arm, task) for arm in ("control", "pi") for task in study.TASKS])
        self.assertEqual((self.root / "control/after/prices.bin").read_bytes(), b"\x00\xff")
        self.assertTrue(all(row["pi_setup"] for row in study.differences(self.root)))

    def test_manifest_does_not_follow_symlinks_and_detects_deletions(self):
        checkout = self.root / "control/work"
        (checkout / "outside").symlink_to("/no-such-path")
        before = study.manifest(checkout)
        self.assertEqual(before["outside"], {"link": "/no-such-path"})
        (checkout / "catalog.py").unlink()
        self.assertNotIn("catalog.py", study.manifest(checkout))
        with self.assertRaisesRegex(ValueError, "source changed"):
            study.run(self.root, arms=("control",))


if __name__ == "__main__":
    unittest.main()
