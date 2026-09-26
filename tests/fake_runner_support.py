"""Locate the sayhi-fakes CLI stand-ins and observe the processes they spawn.

sayhi-fakes (meanaverage/sayhi-fakes, private) supplies scripted `fake-codex`
and `fake-qwen-code` CLIs. This public repository does not vendor that private
source. Point SAYHI_FAKES_ROOT at a checkout (or an unpacked `npm pack` of it);
tests that need it skip with an explicit reason when it is absent.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
MINIMUM_NODE = 20


def fakes_root():
    configured = os.environ.get('SAYHI_FAKES_ROOT')
    if configured:
        return Path(configured).resolve()
    return None


def node_major(binary):
    try:
        version = subprocess.run([binary, '--version'], capture_output=True, text=True, timeout=10).stdout
        return int(version.strip().lstrip('v').split('.')[0])
    except (OSError, ValueError, subprocess.SubprocessError):
        return 0


def require_fakes(test, node=None):
    """Return (fakes root, node binary) or skip the test explicitly."""
    root = fakes_root()
    if root is None:
        raise unittest.SkipTest('SAYHI_FAKES_ROOT is not set; sayhi-fakes CLI integration not run')
    if not (root / 'src/cli/fake-codex.mjs').is_file() or not (root / 'src/cli/fake-qwen-code.mjs').is_file():
        raise unittest.SkipTest(f'SAYHI_FAKES_ROOT does not contain sayhi-fakes CLIs: {root}')
    binary = node or shutil.which('node')
    if not binary or node_major(binary) < MINIMUM_NODE:
        raise unittest.SkipTest(f'Node >= {MINIMUM_NODE} required for sayhi-fakes at {binary}')
    return root, binary


def write_script(path, scenarios):
    Path(path).write_text(json.dumps({'identity': 'sayhi-fake', 'scenarios': scenarios}))
    return path


def log_records(path, kind=None):
    path = Path(path)
    if not path.exists():
        return []
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return [row for row in rows if kind is None or row.get('kind') == kind]


def live_processes(marker):
    """Non-zombie processes whose command line contains `marker` (Linux /proc)."""
    found = []
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit() or int(entry.name) == os.getpid():
            continue
        try:
            command = (entry / 'cmdline').read_bytes().replace(b'\0', b' ').decode(errors='replace')
            state = (entry / 'stat').read_text().rsplit(')', 1)[1].split()[0]
        except OSError:
            continue
        if marker in command and state != 'Z':
            found.append((int(entry.name), command.strip()))
    return found


def wait_until(predicate, timeout=10, interval=.02):
    deadline = time.monotonic() + timeout
    while True:
        value = predicate()
        if value:
            return value
        if time.monotonic() >= deadline:
            raise AssertionError(f'condition not met within {timeout}s')
        time.sleep(interval)


def settle_no_processes(marker, timeout=3):
    """Processes still alive after `timeout` seconds; empty means none leaked."""
    deadline = time.monotonic() + timeout
    while True:
        alive = live_processes(marker)
        if not alive or time.monotonic() >= deadline:
            return alive
        time.sleep(.05)
