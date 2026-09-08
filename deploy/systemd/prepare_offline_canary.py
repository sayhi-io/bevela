"""Stage real cached intent without copying provider or operator credentials.

This does not create a production config or solve observation-feed migration.
Output must be a new directory, and paths in config are final absolute paths.
Run as the authorized installer; then assign only cache/ to the service user.
"""
import argparse
import hashlib
import json
from pathlib import Path
import secrets


def prepare(source_config, destination):
    destination = Path(destination)
    if not destination.is_absolute() or destination.exists():
        raise ValueError("A new absolute destination is required")
    source = json.loads(Path(source_config).read_text())
    scopes = []
    snapshots = []
    seen = set()
    for index, item in enumerate(source["scopes"]):
        if item["id"] in seen:
            raise ValueError("Duplicate scope")
        seen.add(item["id"])
        path = Path(item["cache"])
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 8 * 1024 * 1024:
            raise ValueError("Bounded regular snapshot required")
        raw = path.read_bytes()
        snapshot = json.loads(raw)
        if snapshot.get("scope_id") != item["id"]:
            raise ValueError("Snapshot scope mismatch")
        snapshots.append(raw)
        # Preserve unavailable observation locations explicitly. No transcript
        # access is granted and no provider token/config is copied.
        scope = {k: item[k] for k in (
            "id", "label", "presence_sources", "enrollment_sources", "report_directory"
        ) if k in item}
        scope["provider"] = {"kind": "snapshot", "path": str(destination / "input" / f"{index}.json")}
        scope["cache"] = str(destination / "cache" / f"{index}.json")
        scopes.append(scope)
    if not scopes:
        raise ValueError("At least one real scope required")
    password = secrets.token_urlsafe(32)
    config = {"principals": {"canary": {
        "token_sha256": hashlib.sha256(password.encode()).hexdigest(),
        "scopes": sorted(seen), "workspace_inventory": True,
    }}, "scopes": scopes}
    if "workspace_inventory" in source:
        config["workspace_inventory"] = source["workspace_inventory"]
    destination.mkdir(mode=0o750)
    for name in ("input", "cache"):
        (destination / name).mkdir(mode=0o750)
    for index, raw in enumerate(snapshots):
        for directory in ("input", "cache"):
            path = destination / directory / f"{index}.json"
            with path.open("xb") as stream:
                stream.write(raw)
            path.chmod(0o640)
    for name, data, mode in (
        ("config.json", config, 0o640),
        ("access.json", {"username": "canary", "password": password}, 0o600),
        ("manifest.json", {"meaning": "real cached-state account canary, not live provider or feed coverage",
                           "scope_count": len(scopes),
                           "snapshot_sha256": [hashlib.sha256(raw).hexdigest() for raw in snapshots]}, 0o640),
    ):
        with (destination / name).open("x") as stream:
            json.dump(data, stream, indent=2)
            stream.write("\n")
        (destination / name).chmod(mode)
    return len(scopes)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-config", required=True)
    parser.add_argument("--destination", required=True)
    args = parser.parse_args()
    count = prepare(args.source_config, args.destination)
    print(json.dumps({"scope_count": count, "mode": "offline-canary", "credentials_printed": False}))
