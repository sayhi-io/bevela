#!/usr/bin/env python3
"""Publish the committed checkout to the pinned loopback dogfood service."""

from __future__ import annotations

import argparse
import base64
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import urllib.error
import urllib.request


class PublishError(RuntimeError):
    pass


def run(argv: list[str], *, cwd: Path | None = None) -> str:
    result = subprocess.run(
        argv, cwd=cwd, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, check=False,
    )
    if result.returncode:
        detail = result.stdout.strip()
        raise PublishError(f"Failed: {' '.join(argv)}" + (f"\n{detail}" if detail else ""))
    return result.stdout.strip()


def git(root: Path, *args: str) -> str:
    return run(["git", "-C", str(root), *args])


@contextmanager
def publish_lock(state: Path):
    path = state / ".publish-loopback.lock"
    handle = path.open("a")
    os.chmod(path, 0o600)
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as error:
        handle.close()
        raise PublishError("Another loopback publication is already running") from error
    try:
        yield
    finally:
        fcntl.flock(handle, fcntl.LOCK_UN)
        handle.close()


def lock_release(root: Path) -> None:
    for directory, _, files in os.walk(root):
        os.chmod(directory, 0o555)
        for name in files:
            path = Path(directory, name)
            if path.is_symlink():
                continue
            mode = path.stat().st_mode
            os.chmod(path, 0o555 if mode & stat.S_IXUSR else 0o444)


def clean_failed_candidate(pending: Path, destination: Path, promoted: bool) -> None:
    if pending.exists():
        shutil.rmtree(pending)
    if promoted and destination.exists():
        shutil.rmtree(destination)


def authenticated_smoke(state: Path, port: int) -> None:
    access = json.loads((state / "operator-access.json").read_text())
    token = base64.b64encode(
        f"{access['username']}:{access['password']}".encode()
    ).decode()
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/observatory",
        headers={"Authorization": "Basic " + token},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read()
        if response.status != 200 or b'id="metrics"' not in body:
            raise PublishError("Live observatory smoke check failed")


def verify_service(unit: str, source: Path, previous_pid: str) -> str:
    run(["systemctl", "--user", "is-active", "--quiet", unit])
    pid = run(["systemctl", "--user", "show", unit, "-p", "MainPID", "--value"])
    if not pid or pid == previous_pid:
        raise PublishError("Service restart did not create a new process")
    argv = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
    if not any(
        item and b"project-intent" in item and Path(item.decode()).resolve() == source / ".venv/bin/project-intent"
        for item in argv
    ):
        raise PublishError(f"Running service is not pinned to {source}")
    return pid


def restore_release(state: Path, current: Path, old: Path, unit: str, previous_pid: str) -> None:
    rollback = state / f".current-rollback-{os.getpid()}"
    rollback.symlink_to(old)
    os.replace(rollback, current)
    run(["systemctl", "--user", "restart", unit])
    verify_service(unit, old, previous_pid)


def publish_locked(args: argparse.Namespace, state: Path) -> str:
    root = Path(__file__).resolve().parents[1]
    releases = state / "releases"
    current = state / "current"
    if not (state / "config.json").is_file() or not releases.is_dir():
        raise PublishError(f"Not a Project Intent state directory: {state}")
    if not current.is_symlink():
        raise PublishError(f"Current release pointer is not a symlink: {current}")
    if git(root, "status", "--porcelain", "--untracked-files=no"):
        raise PublishError("Tracked checkout changes must be committed before publishing")

    commit = git(root, "rev-parse", "HEAD")
    short = commit[:7]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name = f"mission-control-{short}-{stamp}"
    destination = releases / name
    pending = releases / f".{name}.pending-{os.getpid()}"
    if destination.exists() or pending.exists():
        raise PublishError(f"Release path already exists: {destination}")

    old = current.resolve()
    if old.name != "source" or old.parent.parent != releases:
        raise PublishError(f"Current release is outside the managed release directory: {old}")
    promoted = False
    try:
        pending.mkdir(mode=0o700)
        run(["git", "clone", "--quiet", "--no-local", "--no-checkout", str(root), str(pending / "source")])
        git(pending / "source", "checkout", "--quiet", "--detach", commit)
        pending.rename(destination)
        promoted = True
        source = destination / "source"
        run([sys.executable, "-m", "venv", str(source / ".venv")])
        python = source / ".venv/bin/python"
        run([str(python), "-m", "pip", "install", "--quiet", "--disable-pip-version-check", "--no-input", "--no-deps", str(source)])
        run([str(python), "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"], cwd=source)
        node_tests = sorted(source.glob("tests/*.test.cjs")) + sorted(source.glob("tests/test_*.cjs"))
        run(["node", "--test", *map(str, node_tests)], cwd=source)
        run(["node", "--check", "project_intent/web/app.js"], cwd=source)
        if git(source, "rev-parse", "HEAD") != commit:
            raise PublishError("Candidate checkout does not match the requested commit")
        lock_release(source)
    except Exception:
        clean_failed_candidate(pending, destination, promoted)
        raise

    source = destination / "source"
    link = state / f".current-{short}-{os.getpid()}"
    if current.resolve() != old:
        raise PublishError(f"Current release changed while candidate was building: {current.resolve()}")
    old_pid = run(["systemctl", "--user", "show", args.unit, "-p", "MainPID", "--value"])
    try:
        link.symlink_to(source)
        os.replace(link, current)
        run(["systemctl", "--user", "restart", args.unit])
        new_pid = verify_service(args.unit, source, old_pid)
        authenticated_smoke(state, args.port)
    except Exception as error:
        try:
            restore_release(state, current, old, args.unit, locals().get("new_pid", old_pid))
        except Exception as rollback_error:
            raise PublishError(
                f"Activation failed: {error}; rollback to {old} also failed: {rollback_error}"
            ) from error
        raise PublishError(f"Activation failed and was rolled back to {old}: {error}") from error
    return f"Published {short} → http://127.0.0.1:{args.port}/observatory"


def publish(args: argparse.Namespace) -> str:
    state = args.state_dir.resolve()
    if not (state / "config.json").is_file() or not (state / "releases").is_dir():
        raise PublishError(f"Not a Project Intent state directory: {state}")
    with publish_lock(state):
        return publish_locked(args, state)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument(
        "--state-dir", type=Path,
        default=Path.home() / "sayhi/state/project-intent",
    )
    result.add_argument("--unit", default="project-intent-dogfood.service")
    result.add_argument("--port", type=int, default=8290)
    return result


if __name__ == "__main__":
    try:
        print(publish(parser().parse_args()))
    except (PublishError, OSError, KeyError, json.JSONDecodeError, urllib.error.URLError) as error:
        print(f"Publish failed: {error}", file=sys.stderr)
        raise SystemExit(1)
