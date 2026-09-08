"""Static candidate contracts only; not proof of a migrated live service."""
import configparser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
UNITS = ["project-intent-hardened.service"]
DIRECTORY = ROOT / "deploy/systemd"


def unit(name):
    config = configparser.ConfigParser(interpolation=None, strict=False)
    config.optionxform = str
    config.read(DIRECTORY / name)
    return config


class ServiceIdentityCandidateTests(unittest.TestCase):
    def test_explicit_dedicated_accounts(self):
        for name in UNITS:
            service = unit(name)["Service"]
            self.assertNotIn(service["User"], ("", "root", "meanaverage"))
            self.assertEqual(service["Group"], service["User"])
            self.assertNotIn("SupplementaryGroups", service)

    def test_privilege_floor(self):
        for name in UNITS:
            service = unit(name)["Service"]
            self.assertEqual(service["NoNewPrivileges"], "yes")
            self.assertEqual(service["CapabilityBoundingSet"], "")
            self.assertEqual(service["AmbientCapabilities"], "")
            self.assertEqual(service["ProtectSystem"], "strict")
            self.assertEqual(service["ProtectHome"], "yes")
            self.assertEqual(service["PrivateDevices"], "yes")
            self.assertEqual(service["UMask"], "0077")
            self.assertEqual(service["LimitCORE"], "0")

    def test_no_operator_home_or_escalation_in_entrypoint(self):
        for name in UNITS:
            command = unit(name)["Service"]["ExecStart"]
            for forbidden in ("/home/", "sudo", "docker.sock", "/bin/sh", "/bin/bash", "meanaverage@"):
                self.assertNotIn(forbidden, command)
            self.assertNotIn("ExecStartPre", unit(name)["Service"])

    def test_system_boot_and_explicit_admission_interlock(self):
        for name in UNITS:
            config = unit(name)
            self.assertEqual(config["Install"]["WantedBy"], "multi-user.target")
            self.assertTrue(config["Unit"]["AssertPathExists"].startswith("/etc/"))
            self.assertTrue(config["Unit"]["AssertPathExists"].endswith("/admitted"))

    def test_commands_preserve_bounded_interface(self):
        for name in UNITS:
            config = unit(name)
            command = config["Service"]["ExecStart"]
            if "forward" in name:
                self.assertEqual(command.count(" -L "), 3)
                for port in (8081, 9000, 9443):
                    self.assertIn(f"127.0.0.1:{port}:127.0.0.1:{port}", command)
                for flag in ("StrictHostKeyChecking=yes", "IdentityAgent=none", "ForwardAgent=no", "-F /dev/null"):
                    self.assertIn(flag, command)
            elif "connector" in name:
                self.assertIn("--config %d/connector.json run --interval 5", command)
                self.assertIn("LoadCredential", config["Service"])
            else:
                self.assertIn("serve --config /etc/project-intent/config.json --port 8290", command)
                self.assertEqual(config["Service"]["StateDirectory"], "project-intent")


if __name__ == "__main__":
    unittest.main()

