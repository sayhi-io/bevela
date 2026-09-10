"""Bounded, explicitly configured local Git evidence for Mission Control."""
from datetime import datetime, timedelta, timezone
import copy
import os
from pathlib import Path
import re
import subprocess
import threading
import time

MAX_REPOSITORIES = 32
MAX_COMMITS = 100
MAX_LOOKBACK_DAYS = 365
MAX_OUTPUT_BYTES = 512 * 1024
MAX_REMOTE_COMMITS = 4096


def _git(path, arguments, timeout=4):
    environment = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
    }
    for variable in ("LANG", "LC_ALL", "LC_CTYPE"):
        if variable in os.environ:
            environment[variable] = os.environ[variable]
    result = subprocess.run(
        ["git", "-c", "credential.helper=", "-c", "core.hooksPath=/dev/null",
         "-c", "log.showSignature=false", "-C", str(path), *arguments],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        timeout=timeout, check=False,
        env=environment,
    )
    if result.returncode or len(result.stdout) > MAX_OUTPUT_BYTES:
        raise OSError("Bounded local Git observation failed")
    return result.stdout


def _timestamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Commit timestamp lacks timezone")
    return parsed


def _subject(value):
    text = value.decode("utf-8", "replace")
    text = "".join(character if ord(character) >= 32 else " " for character in text)
    return " ".join(text.split())[:160] or "Commit without a subject"


def _repository(path, name, scope, since, observed, limit):
    top_level_raw = _git(path, ["rev-parse", "--show-toplevel"])
    try:
        top_level = Path(os.fsdecode(top_level_raw.rstrip(b"\n"))).resolve(strict=True)
    except (OSError, UnicodeError):
        raise OSError("Configured directory is not a repository root")
    if not top_level_raw.endswith(b"\n") or b"\n" in top_level_raw.rstrip(b"\n") or top_level != path:
        raise OSError("Configured directory is not a repository root")
    raw = _git(path, ["log", "--branches", "--remotes", f"--since-as-filter={since.isoformat()}",
                      f"--max-count={limit + 1}", "--format=%H%x09%cI%x09%s"])
    rows = raw.splitlines()
    truncated = len(rows) > limit
    rows = rows[:limit]
    remote_raw = _git(path, ["rev-list", "--remotes", f"--since-as-filter={since.isoformat()}",
                             f"--max-count={MAX_REMOTE_COMMITS + 1}"])
    remote_rows = remote_raw.splitlines()
    remote_complete = len(remote_rows) <= MAX_REMOTE_COMMITS
    remote = {row.decode("ascii", "ignore") for row in remote_rows[:MAX_REMOTE_COMMITS]}
    commits, future = [], 0
    for row in rows:
        parts = row.split(b"\t", 2)
        if len(parts) != 3:
            raise ValueError("Invalid local Git log row")
        oid = parts[0].decode("ascii", "ignore").lower()
        if not re.fullmatch(r"[a-f0-9]{40}|[a-f0-9]{64}", oid):
            raise ValueError("Invalid local Git object ID")
        committed_at = _timestamp(parts[1].decode("ascii", "strict"))
        if committed_at > observed:
            future += 1
            continue
        publication = "remote-tracking" if oid in remote else "local-only" if remote_complete else "unknown"
        commits.append({
            "scope": scope, "repository": name, "oid": oid,
            "committed_at": committed_at.isoformat(),
            "subject": _subject(parts[2]), "publication": publication,
        })
    return commits, truncated, remote_complete, future


def observe(config, principal, selected=None, now=None):
    """Observe named repositories only after principal scope authorization."""
    if principal.get("local_git_calendar") is not True:
        return None
    settings = config.get("local_git_calendar")
    if settings is None:
        return {"status": "not-configured", "commits": []}
    if not isinstance(settings, dict) or set(settings) - {"root", "repositories", "lookback_days", "commit_limit"}:
        return {"status": "unavailable", "commits": []}
    root_value, repositories = settings.get("root"), settings.get("repositories")
    lookback, limit = settings.get("lookback_days", 90), settings.get("commit_limit", 50)
    if (not isinstance(root_value, str) or not isinstance(repositories, list)
            or not 1 <= len(repositories) <= MAX_REPOSITORIES
            or type(lookback) is not int or not 1 <= lookback <= MAX_LOOKBACK_DAYS
            or type(limit) is not int or not 1 <= limit <= MAX_COMMITS):
        return {"status": "unavailable", "commits": []}
    root = Path(root_value)
    try:
        if not root.is_absolute() or root.is_symlink() or root.resolve() != root or not root.is_dir():
            raise OSError("Invalid local Git root")
    except OSError:
        return {"status": "unavailable", "commits": []}
    allowed = set(principal.get("scopes", []))
    observed = now or datetime.now(timezone.utc)
    since = observed - timedelta(days=lookback)
    commits, failures, truncated, remote_partial, future, successes, visible_count = [], 0, 0, 0, 0, 0, 0
    seen = set()
    for entry in repositories:
        if not isinstance(entry, dict):
            continue
        scope = entry.get("scope")
        if not isinstance(scope, str) or not scope:
            continue
        if scope not in allowed or (selected and scope != selected):
            continue
        if (set(entry) != {"name", "scope"} or not isinstance(entry.get("name"), str)
                or not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", entry["name"])):
            failures += 1
            continue
        name = entry["name"]
        identity = (name, scope)
        if identity in seen:
            failures += 1
            continue
        seen.add(identity)
        visible_count += 1
        path = root / name
        try:
            if path.is_symlink() or path.resolve() != path or path.parent != root or not path.is_dir():
                raise OSError("Invalid configured repository")
            rows, was_truncated, remote_complete, future_count = _repository(path, name, scope, since, observed, limit)
            commits.extend(rows)
            successes += 1
            truncated += int(was_truncated)
            remote_partial += int(not remote_complete)
            future += future_count
        except (OSError, ValueError, subprocess.SubprocessError, UnicodeError):
            failures += 1
    commits.sort(key=lambda item: (item["committed_at"], item["repository"], item["oid"]), reverse=True)
    status = "not-configured-for-scope" if not visible_count and not failures else "unavailable" if failures and not commits else "partial" if failures or truncated or remote_partial else "observed"
    return {
        "status": status, "observed_at": observed.isoformat(), "commits": commits,
        "coverage": {
            "configured_repositories": visible_count, "observed_repositories": successes,
            "lookback_days": lookback, "commit_limit_per_repository": limit,
            "truncated_repositories": truncated, "remote_coverage_partial": remote_partial,
            "future_timestamps_excluded": future,
            "meaning": "Named local repositories and their local/remote-tracking refs only; no fetch, author identity, branch name, diff, body, or work-duration inference.",
        },
    }


class Observer:
    """Serialize and briefly cache identical authorized observations."""
    def __init__(self, config, ttl_seconds=30):
        self.config = config
        self.ttl_seconds = ttl_seconds
        self.lock = threading.Lock()
        self.cache = {}

    def view(self, principal, selected=None):
        if principal.get("local_git_calendar") is not True:
            return None
        key = (tuple(sorted(principal.get("scopes", []))), selected)
        with self.lock:
            current = time.monotonic()
            cached = self.cache.get(key)
            if cached and current - cached[0] < self.ttl_seconds:
                return copy.deepcopy(cached[1])
            result = observe(self.config, principal, selected)
            self.cache[key] = (current, result)
            return copy.deepcopy(result)
