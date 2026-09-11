#!/usr/bin/env python3
"""Copy an explicitly reviewed Project Intent source list and bind its bytes."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath


ROOT_FILES = {"AGENTS.md", "README.md", "PROJECT.md", "pyproject.toml", ".gitignore"}
# Exact audited assets, not general permission to include binary or text state.
SOURCE_ASSETS = {"project_intent/web/inter-variable.woff2", "project_intent/web/INTER-LICENSE.txt",
                 "scripts/publish_loopback.py"}
ROOT_DIRS = {"project_intent", "tests", "docs", "skills", ".github"}
FORBIDDEN = {".git", ".venv", "node_modules", "__pycache__", "state", "runtime", "evidence"}
SUFFIXES = {".py", ".md", ".toml", ".json", ".js", ".cjs", ".css", ".html", ".yaml", ".yml", ".svg"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def source_path(root, value):
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"Non-relative source path: {value}")
    if any(part in FORBIDDEN or part.endswith(".egg-info") for part in path.parts):
        raise ValueError(f"Operational/build path refused: {value}")
    allowed = value in ROOT_FILES or value in SOURCE_ASSETS or value == ".project-intent/snapshot.json"
    allowed = allowed or (path.parts[0] in ROOT_DIRS and path.suffix in SUFFIXES)
    if not allowed:
        raise ValueError(f"Outside Project Intent source allowlist: {value}")
    target = root.joinpath(*path.parts)
    for parent in [target, *target.parents]:
        if parent == root:
            break
        if parent.is_symlink():
            raise ValueError(f"Symlink refused: {value}")
    if not target.is_file():
        raise ValueError(f"Not a source file: {value}")
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--files", type=Path, help="Reviewed newline-separated relative paths")
    parser.add_argument("--output", type=Path, help="New evidence directory, must not exist")
    parser.add_argument("--verify", type=Path, help="Verify an existing output directory")
    args = parser.parse_args()
    if args.verify:
        root = args.verify.resolve()
        manifest = json.loads((root / "manifest.json").read_text())
        entries = manifest["files"]
        for entry in entries:
            data = source_path(root / "source", entry["path"]).read_bytes()
            if digest(data) != entry["sha256"] or len(data) != entry["bytes"]:
                raise ValueError(f"Source changed: {entry['path']}")
        encoded = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()
        if digest(encoded) != manifest["manifest_sha256"]:
            raise ValueError("Manifest content changed")
        print(json.dumps({"verified_files": len(entries), "manifest_sha256": digest(encoded)}))
        return
    if not all([args.source, args.files, args.output]):
        parser.error("--source, --files and --output are required when sealing")
    root = args.source.resolve()
    output = args.output.absolute()
    if output.exists() or output.is_symlink() or root == output or root in output.parents:
        raise ValueError("Output must be a new directory outside source")
    values = sorted(set(line.strip() for line in args.files.read_text().splitlines() if line.strip()))
    if not values:
        raise ValueError("Empty source selection")
    captured = [(value, source_path(root, value).read_bytes()) for value in values]
    output.mkdir(mode=0o700, parents=False)
    entries = []
    for value, data in captured:
        target = output / "source" / value
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        entries.append({"path": value, "sha256": digest(data), "bytes": len(data)})
    for value, data in captured:
        if source_path(root, value).read_bytes() != data:
            raise ValueError(f"Source changed while sealing; discard this incomplete result: {value}")
    encoded = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()
    manifest = {"contract": "sayhi.project-intent.source-seal/v1", "source": str(root),
                "meaning": "Explicit source bytes, not a Git commit, CI run, or secret scan",
                "files": entries, "manifest_sha256": digest(encoded)}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"sealed_files": len(entries), "manifest_sha256": digest(encoded),
                      "output": str(output)}))


if __name__ == "__main__":
    main()
