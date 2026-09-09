"""Execute the public Depot checker unchanged against an explicit source root.

No model calls or recorder integration. Reference source is never copied here.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys


ASSETS = Path(__file__).resolve().parent / 'assets/distributed_v1'


def check(source_root, checker=None, python=None):
    source_root = Path(source_root).resolve(strict=True)
    checker = Path(checker or ASSETS / 'fixture/acceptance.py').resolve(strict=True)
    result = subprocess.run([str(python or sys.executable), '-B', '-I', str(checker), str(source_root)],
                            cwd=source_root, capture_output=True, text=True, timeout=60)
    try:
        data = json.loads(result.stdout)
    except ValueError as exc:
        raise RuntimeError('Checker did not emit one JSON object') from exc
    if result.returncode != 0 or 'infrastructure_error' in data:
        raise RuntimeError('Checker infrastructure failure: ' + str(data))
    if not isinstance(data.get('accepted'), bool) or not isinstance(data.get('groups'), dict):
        raise RuntimeError('Invalid checker envelope')
    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source_root', type=Path)
    parser.add_argument('--checker', type=Path)
    args = parser.parse_args()
    print(json.dumps(check(args.source_root, args.checker), sort_keys=True))
