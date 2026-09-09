"""Prepare a tiny shared checkout; record native Codex processes without steering.

No model API, agent loop, staged task delivery, code merging, repair or review.
Runtime artifacts belong in a private temporary directory, never product source.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import stat
import subprocess
import tempfile
import time


ASSETS = Path(__file__).with_suffix("")
TASKS = ("prices", "receipt")
SCOPE = "experiment/seam-micro"
DEFAULT_PI = "/home/meanaverage/sayhi/bin/project-intent"


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def utc():
    return datetime.now(timezone.utc).isoformat()


def task_text(task):
    return (ASSETS / f"{task}.txt").read_text()


def manifest(root):
    """Inventory literal files, links and modes without following links or .git."""
    result = {}
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d != ".git")
        for name in sorted(set(files + dirs)):
            path = Path(directory) / name
            info = path.lstat()
            key = str(path.relative_to(root))
            if stat.S_ISLNK(info.st_mode):
                result[key] = {"link": os.readlink(path)}
            elif stat.S_ISREG(info.st_mode):
                data = path.read_bytes()
                result[key] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                               "mode": stat.S_IMODE(info.st_mode)}
            elif not stat.S_ISDIR(info.st_mode):
                raise ValueError(f"Cannot faithfully archive special file: {key}")
    return result


def install_pi(checkout, pi_command):
    """Task inventory and real PI CLI, not fabricated worker observations."""
    context = checkout / ".pi"
    context.mkdir()
    snapshot = {
        "version": 1, "scope_id": SCOPE,
        "source": {"provider": "snapshot", "authoritative": False,
                   "captured_at": utc(), "mode": "offline_snapshot"},
        "mission": "Tiny shop prices, checkout totals and receipt display.",
        "records": [
            {"kind": "workstream", "id": task.upper(), "statement": task_text(task).strip(),
             "revision": "1", "state": "active", "scope": task_text(task).strip(),
             "acceptance": [task_text(task).strip()], "readiness": {},
             "source_checkout": str(checkout),
             "boundaries": ["shop/money", f"shop/{task}"]}
            for task in TASKS
        ],
    }
    write_json(context / "snapshot.json", snapshot)
    write_json(context / "worker.json", {"scopes": {SCOPE: {
        "snapshot": str(context / "snapshot.json"),
        "enrollment_directory": str(context / "presence"),
        "report_directory": str(context / "reports"),
    }}})
    cli = f"{shlex.quote(pi_command)} --worker-config .pi/worker.json --scope {SCOPE}"
    (checkout / "AGENTS.md").write_text(
        "# Project Intent\n\n"
        "Use Project Intent for your task. This checkout has a local task inventory "
        "and live cooperative worker declarations; it is not connected to production.\n\n"
        f"CLI: `{cli}`. Run `onboard --query 'your task keywords'`, then onboard "
        "your matching workstream. Enroll your own session with actual edit paths, "
        "touching seams, approaching seams and working description. Use the local "
        "worker-config on every call, including the printed enrollment command. "
        "Use your own CODEX_THREAD_ID with --session for local presence. "
        "Consult nearby work and keep your declaration current as your work changes; "
        "release it with --inactive when finished. These declarations are context, "
        "not locks or instructions to wait.\n"
    )


def prepare(parent=None, pi_command=DEFAULT_PI):
    root = Path(tempfile.mkdtemp(prefix="pi-seam-", dir=parent)).resolve()
    # Outside the SayHi workspace: do not inherit its mandatory PI AGENTS.md in control.
    for arm in ("control", "pi"):
        checkout = root / arm / "work"
        shutil.copytree(ASSETS / "fixture", checkout)
        subprocess.run(["git", "init", "-q", str(checkout)], check=True)
        if arm == "pi":
            install_pi(checkout, pi_command)
        shutil.copytree(checkout, root / arm / "before", ignore=shutil.ignore_patterns(".git"))
        write_json(root / arm / "before.json", manifest(checkout))
    for task in TASKS:
        (root / f"{task}.txt").write_bytes((ASSETS / f"{task}.txt").read_bytes())
    write_json(root / "study.json", {
        "created_at": utc(), "target_seconds": 30,
        "target_is_not_a_deadline": True,
        "recording": "Native Codex exec; workspace-write, otherwise inherited configuration and environment",
        "pi_command": pi_command,
        "treatment": "Only pi/work has PI setup; identical per-task prompts",
        "checkout_sharing": "Two concurrent sessions in each shared checkout",
        "isolation": "Separate condition directories, native workspace-write sandbox; not read isolation",
    })
    return root


def command(codex, checkout, prompt, model, effort):
    return [codex, "exec", "--json", "--sandbox", "workspace-write", "-m", model,
            "-c", f'model_reasoning_effort="{effort}"', "-C", str(checkout), prompt]


def record(root, arm, task, codex, model, effort):
    directory = root / arm / task
    directory.mkdir()
    argv = command(codex, root / arm / "work", (root / f"{task}.txt").read_text(), model, effort)
    write_json(directory / "command.json", argv)
    result = {"arm": arm, "task": task, "started_at": utc(),
              "start_monotonic_ns": time.monotonic_ns()}
    with (directory / "stdout.jsonl").open("wb") as stdout, (directory / "stderr.bin").open("wb") as stderr:
        try:
            process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                       cwd=root / arm / "work")
            result.update(pid=process.pid, exit_code=process.wait())
        except OSError as error:
            result.update(exit_code=None, launch_error=str(error))
    result.update(finished_at=utc(), end_monotonic_ns=time.monotonic_ns())
    result["elapsed_seconds"] = (result["end_monotonic_ns"] - result["start_monotonic_ns"]) / 1e9
    write_json(directory / "result.json", result)
    return result


def run(root, arms=("control", "pi"), codex="codex", model="gpt-5.6-luna", effort="medium"):
    root = Path(root).resolve(strict=True)
    if not (root / "study.json").is_file():
        raise ValueError("Prepare a disposable study first")
    # Validate before marking anything started. No rerun overwrites original bytes.
    for arm in arms:
        if arm not in ("control", "pi") or (root / arm / "started.json").exists():
            raise ValueError("Unknown or already started condition")
        if manifest(root / arm / "work") != json.loads((root / arm / "before.json").read_text()):
            raise ValueError("Prepared source changed before start")
    binary = shutil.which(codex)
    if not binary:
        raise ValueError("Native Codex executable unavailable")
    version = subprocess.check_output([binary, "--version"], text=True).strip()
    for arm in arms:
        with (root / arm / "started.json").open("x") as stream:
            json.dump({"at": utc(), "codex": binary, "version": version,
                       "requested_model": model, "requested_effort": effort,
                       "environment": "inherited unchanged; no credential/config values copied"}, stream)
    jobs = [(arm, task) for task in TASKS for arm in arms]
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        futures = [pool.submit(record, root, arm, task, binary, model, effort) for arm, task in jobs]
        results = [future.result() for future in futures]
    for arm in arms:
        # Snapshot only after both writers exit; never attribute the shared tree to one worker.
        checkout = root / arm / "work"
        after = root / arm / "after"
        shutil.copytree(checkout, after, symlinks=True, ignore=shutil.ignore_patterns(".git"))
        write_json(root / arm / "after.json", manifest(after))
        rows = [r for r in results if r["arm"] == arm]
        start = min(r["start_monotonic_ns"] for r in rows)
        end = max(r["end_monotonic_ns"] for r in rows)
        overlap = min(r["end_monotonic_ns"] for r in rows) - max(r["start_monotonic_ns"] for r in rows)
        write_json(root / arm / "summary.json", {
            "wall_seconds": (end - start) / 1e9,
            "process_overlap_seconds": max(0, overlap) / 1e9,
            "overlap_is_not_proof_of_concurrent_seam_edits": True,
            "workers": rows,
            "completion": "processes exited; not an acceptance verdict",
        })
    return results


def differences(root):
    """Exact file inventory comparison; no semantic verdict or candidate execution."""
    root = Path(root)
    left, right = [json.loads((root / arm / "after.json").read_text()) for arm in ("control", "pi")]
    return [{"path": path, "control": left.get(path), "pi": right.get(path),
             "pi_setup": path == "AGENTS.md" or path.startswith(".pi/")}
            for path in sorted(left.keys() | right.keys()) if left.get(path) != right.get(path)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    setup = sub.add_parser("prepare")
    setup.add_argument("--parent", type=Path)
    setup.add_argument("--pi-command", default=DEFAULT_PI)
    launch = sub.add_parser("run")
    launch.add_argument("root", type=Path)
    launch.add_argument("--arm", choices=("control", "pi", "both"), default="both")
    launch.add_argument("--codex", default="codex")
    launch.add_argument("--model", default="gpt-5.6-luna")
    launch.add_argument("--effort", default="medium")
    compare = sub.add_parser("diff")
    compare.add_argument("root", type=Path)
    args = parser.parse_args()
    if args.action == "prepare":
        print(prepare(args.parent, args.pi_command))
    elif args.action == "run":
        arms = ("control", "pi") if args.arm == "both" else (args.arm,)
        print(json.dumps(run(args.root, arms, args.codex, args.model, args.effort), indent=2))
    else:
        print(json.dumps(differences(args.root), indent=2))


if __name__ == "__main__":
    main()
