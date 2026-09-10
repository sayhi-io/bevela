from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from project_intent import local_git
from project_intent.local_git import Observer, observe


class LocalGitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / "sample"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.name", "Private Author")
        self.git("config", "user.email", "private@example.invalid")
        (self.repo / "file.txt").write_text("one\n")
        self.git("add", "file.txt")
        self.commit("first public subject", "2026-09-08T10:00:00+00:00")
        self.first = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("update-ref", "refs/remotes/origin/main", self.first)
        (self.repo / "file.txt").write_text("two\n")
        self.git("add", "file.txt")
        self.commit("second local subject", "2026-09-09T11:00:00+00:00")
        self.second = self.git("rev-parse", "HEAD").stdout.strip()
        self.config = {"local_git_calendar": {
            "root": str(self.root), "lookback_days": 30, "commit_limit": 10,
            "repositories": [{"name": "sample", "scope": "scope/visible"}],
        }}
        self.now = datetime(2026, 9, 10, tzinfo=timezone.utc)

    def git(self, *arguments, env=None):
        return subprocess.run(["git", "-C", str(self.repo), *arguments], check=True,
                              capture_output=True, text=True, env=env)

    def commit(self, subject, at):
        import os
        env = dict(os.environ, GIT_AUTHOR_DATE=at, GIT_COMMITTER_DATE=at)
        self.git("commit", "-qm", subject, env=env)

    def test_scoped_named_repository_and_local_publication(self):
        result = observe(self.config, {"scopes": ["scope/visible"], "local_git_calendar": True}, now=self.now)
        self.assertEqual(result["status"], "observed")
        self.assertEqual([row["oid"] for row in result["commits"]], [self.second, self.first])
        self.assertEqual([row["publication"] for row in result["commits"]], ["local-only", "remote-tracking"])
        encoded = str(result)
        self.assertNotIn(str(self.root), encoded)
        self.assertNotIn("Private Author", encoded)
        self.assertNotIn("private@example.invalid", encoded)

    def test_permission_and_scope_filter_before_observation(self):
        self.assertIsNone(observe(self.config, {"scopes": ["scope/visible"]}, now=self.now))
        with patch("project_intent.local_git._repository", side_effect=AssertionError("must filter first")):
            hidden = observe(self.config, {"scopes": ["scope/hidden"], "local_git_calendar": True}, now=self.now)
        self.assertEqual(hidden["commits"], [])
        self.assertEqual(hidden["status"], "not-configured-for-scope")
        self.assertEqual(hidden["coverage"]["configured_repositories"], 0)
        self.assertEqual(hidden["coverage"]["observed_repositories"], 0)

    def test_hidden_repository_configuration_does_not_change_projection(self):
        principal = {"scopes": ["scope/visible"], "local_git_calendar": True}
        expected = observe(self.config, principal, now=self.now)
        config = {"local_git_calendar": dict(self.config["local_git_calendar"])}
        config["local_git_calendar"]["repositories"] = [
            *self.config["local_git_calendar"]["repositories"],
            {"name": "../hidden-invalid", "scope": "scope/hidden"},
            {"name": "missing", "scope": "scope/hidden"},
        ]
        actual = observe(config, principal, now=self.now)
        self.assertEqual(actual, expected)
        self.assertEqual(actual["coverage"]["configured_repositories"], 1)

    def test_invalid_or_symlinked_configuration_fails_closed(self):
        invalid = {"local_git_calendar": {"root": "relative", "repositories": []}}
        self.assertEqual(observe(invalid, {"scopes": [], "local_git_calendar": True})["status"], "unavailable")
        alias = self.root / "alias"
        alias.symlink_to(self.repo, target_is_directory=True)
        config = {"local_git_calendar": {"root": str(self.root),
                  "repositories": [{"name": "alias", "scope": "scope/visible"}]}}
        result = observe(config, {"scopes": ["scope/visible"], "local_git_calendar": True}, now=self.now)
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["commits"], [])

    def test_configured_directory_must_be_the_repository_root(self):
        container = self.root / "container"
        child = container / "child"
        child.mkdir(parents=True)
        subprocess.run(["git", "-C", str(container), "init", "-q"], check=True)
        config = {"local_git_calendar": {"root": str(container),
                  "repositories": [{"name": "child", "scope": "scope/visible"}]}}
        result = observe(config, {"scopes": ["scope/visible"], "local_git_calendar": True}, now=self.now)
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["commits"], [])

    def test_ambient_git_directory_cannot_redirect_observation(self):
        outside = self.root / "outside"
        outside.mkdir()
        subprocess.run(["git", "-C", str(outside), "init", "-q"], check=True)
        subprocess.run(["git", "-C", str(outside), "config", "user.name", "Outside"], check=True)
        subprocess.run(["git", "-C", str(outside), "config", "user.email", "outside@example.invalid"], check=True)
        (outside / "secret.txt").write_text("secret\n")
        subprocess.run(["git", "-C", str(outside), "add", "secret.txt"], check=True)
        environment = dict(os.environ, GIT_AUTHOR_DATE="2026-09-09T12:00:00+00:00",
                           GIT_COMMITTER_DATE="2026-09-09T12:00:00+00:00")
        subprocess.run(["git", "-C", str(outside), "commit", "-qm", "outside secret"],
                       check=True, env=environment)
        with patch.dict(os.environ, {"GIT_DIR": str(outside / ".git")}):
            result = observe(self.config, {"scopes": ["scope/visible"],
                             "local_git_calendar": True}, now=self.now)
        self.assertEqual([row["oid"] for row in result["commits"]], [self.second, self.first])
        self.assertNotIn("outside secret", str(result))

    def test_clock_skew_does_not_hide_remote_reachability(self):
        original_branch = self.git("branch", "--show-current").stdout.strip()
        self.git("checkout", "-qb", "skew-local", self.first)
        (self.repo / "skew.txt").write_text("ancestor\n")
        self.git("add", "skew.txt")
        self.commit("newer remote ancestor", "2026-09-09T12:00:00+00:00")
        ancestor = self.git("rev-parse", "HEAD").stdout.strip()
        (self.repo / "skew.txt").write_text("old child\n")
        self.git("add", "skew.txt")
        self.commit("older-dated remote tip", "2026-08-01T12:00:00+00:00")
        child = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("update-ref", "refs/remotes/origin/skew", child)
        self.git("reset", "--hard", ancestor)
        self.git("checkout", "-q", original_branch)
        result = observe(self.config, {"scopes": ["scope/visible"],
                         "local_git_calendar": True}, now=self.now)
        publication = {row["oid"]: row["publication"] for row in result["commits"]}
        self.assertEqual(publication[ancestor], "remote-tracking")

    def test_future_commit_timestamp_is_explicitly_excluded(self):
        (self.repo / "future.txt").write_text("future\n")
        self.git("add", "future.txt")
        self.commit("future commit", "2026-09-11T10:00:00+00:00")
        result = observe(self.config, {"scopes": ["scope/visible"], "local_git_calendar": True}, now=self.now)
        self.assertNotIn("future commit", str(result["commits"]))
        self.assertEqual(result["coverage"]["future_timestamps_excluded"], 1)

    def test_identical_authorized_reads_are_briefly_cached(self):
        observer = Observer(self.config)
        principal = {"scopes": ["scope/visible"], "local_git_calendar": True}
        with patch("project_intent.local_git._repository", wraps=local_git._repository) as repository:
            first = observer.view(principal)
            first["commits"].clear()
            second = observer.view(principal)
        self.assertEqual(repository.call_count, 1)
        self.assertTrue(second["commits"])


if __name__ == "__main__":
    unittest.main()
