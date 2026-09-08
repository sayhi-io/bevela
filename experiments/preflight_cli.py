"""Prove Git writes and independent handoff/final outputs in a real CLI sandbox."""
import json
from pathlib import Path
import subprocess
import tempfile

from experiments.cli_harness import git, run


def main():
    root = Path(tempfile.mkdtemp(prefix="pi-cli-harness-preflight-"))
    (root / "DISPOSABLE_TRIAL").touch()
    repo, checkout = root / "repo", root / "worker"
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    git(repo, "config", "user.name", "Disposable harness preflight")
    git(repo, "config", "user.email", "trial@example.invalid")
    git(repo, "commit", "--allow-empty", "-m", "preflight base")
    base = git(repo, "rev-parse", "HEAD")
    git(repo, "worktree", "add", "-b", "preflight", str(checkout))
    prompt = """This is a disposable harness smoke test, not a product task.
Do not read external project files or use network/tools other than local shell/file edits.
Create proof.txt containing GIT-WRITE-PROVEN and commit ONLY that file locally.
Write TRIAL_HANDOFF.md containing HANDOFF-DETAIL-MUST-SURVIVE on its own line.
Do not commit the handoff. Do not push or change Git configuration.
Your final response must be exactly FINAL-MESSAGE-SEPARATE.
Do not include the handoff marker in your final response.
"""
    result = run(root, checkout, root / "artifacts", prompt, timeout=180)
    handoff = checkout / "TRIAL_HANDOFF.md"
    final = root / "artifacts" / "final-message.md"
    result["git_commit_proven"] = (
        result["head"] != base and git(checkout, "show", "HEAD:proof.txt") == "GIT-WRITE-PROVEN"
    )
    result["handoff_preserved"] = handoff.exists() and handoff.read_text().strip() == "HANDOFF-DETAIL-MUST-SURVIVE"
    result["final_separate"] = final.exists() and final.read_text().strip() == "FINAL-MESSAGE-SEPARATE"
    result["passed"] = result["exit_code"] == 0 and all(result[k] for k in (
        "git_commit_proven", "handoff_preserved", "final_separate"))
    (root / "preflight.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"root": str(root), **result}, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
