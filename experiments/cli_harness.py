"""Isolated CLI experiment launcher. Does not mutate old trial artifacts."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import time


def git(checkout, *args):
    return subprocess.check_output(
        ["git", "-C", str(checkout), *args], text=True
    ).strip()


def inside(root, path):
    path = Path(path).resolve()
    if path == root or not path.is_relative_to(root):
        raise ValueError(f"Expected a strict descendant of disposable trial root: {path}")
    return path


def command(root, checkout, output, shared=(), model="gpt-6-astra"):
    root = Path(root).resolve(strict=True)
    if not (root / "DISPOSABLE_TRIAL").is_file():
        raise ValueError("Missing explicit DISPOSABLE_TRIAL marker")
    checkout = inside(root, checkout)
    if Path(git(checkout, "rev-parse", "--show-toplevel")).resolve() != checkout:
        raise ValueError("Checkout must be the exact Git worktree root")
    common = inside(root, git(checkout, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    # A disposable repo must not share metadata with any external worktree.
    for line in git(checkout, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            inside(root, line.removeprefix("worktree "))
    if git(checkout, "remote"):
        raise ValueError("Trial repository must have no remotes")
    output = inside(root, output)
    handoff = checkout / "TRIAL_HANDOFF.md"
    if output == handoff.resolve() or output.is_relative_to(checkout):
        raise ValueError("CLI final output must be outside the worker checkout/handoff")
    if output.exists():
        raise ValueError("Refusing to overwrite CLI final output")
    writable = [common]
    for item in shared:
        item = inside(root, item)
        if not item.is_dir():
            raise ValueError("Shared write directory must already exist")
        writable.append(item)
    args = ["codex", "-a", "never", "exec", "--ignore-user-config", "--ignore-rules",
            "--ephemeral", "--enable", "skip_host_skill_discovery",
            "--disable", "plugins", "--disable", "apps", "--disable", "memories",
            "--disable", "multi_agent", "-c", "project_doc_max_bytes=0",
            "-m", model, "-c", 'model_reasoning_effort="medium"',
            "-s", "workspace-write"]
    for directory in dict.fromkeys(writable):
        args += ["--add-dir", str(directory)]
    return args + ["-C", str(checkout), "--json", "-o", str(output), "-"]


def run(root, checkout, artifacts, prompt, shared=(), timeout=720):
    root = Path(root).resolve(strict=True)
    artifacts = inside(root, artifacts)
    args = command(root, checkout, artifacts / "final-message.md", shared)
    # Exclusive creation is intentional: retries get a NEW artifact directory.
    artifacts.mkdir(parents=True, exist_ok=False)
    (artifacts / "prompt.txt").write_text(prompt)
    (artifacts / "command.json").write_text(json.dumps(args, indent=2) + "\n")
    allowed = ("PATH", "HOME", "USER", "LOGNAME", "LANG", "LC_ALL", "TERM",
               "TMPDIR", "SSL_CERT_FILE", "SSL_CERT_DIR")
    env = {k: v for k, v in os.environ.items() if k in allowed}
    start = time.monotonic()
    expired = False
    with (artifacts / "events.jsonl").open("x") as out, (artifacts / "stderr.txt").open("x") as err:
        process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=out, stderr=err,
                                   text=True, env=env, start_new_session=True)
        try:
            process.communicate(prompt, timeout=timeout)
        except subprocess.TimeoutExpired:
            expired = True
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
    result = {"exit_code": process.returncode, "timeout": expired,
              "elapsed_seconds": round(time.monotonic() - start, 3),
              "head": git(checkout, "rev-parse", "HEAD"),
              "handoff_exists": (Path(checkout) / "TRIAL_HANDOFF.md").is_file(),
              "final_output_exists": (artifacts / "final-message.md").is_file()}
    (artifacts / "execution.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("root", "checkout", "artifacts", "prompt"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--shared", action="append", default=[], type=Path)
    parser.add_argument("--timeout", type=int, default=720)
    args = parser.parse_args()
    print(json.dumps(run(args.root, args.checkout, args.artifacts,
                         args.prompt.read_text(), args.shared, args.timeout), indent=2))


if __name__ == "__main__":
    main()
