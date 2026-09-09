"""Refund/migration torture study: no-PI passive native Codex recorder.

run launches exactly two native sessions once.
No task staging, messages, repairs, retries, adjudicator or subsequent batch run.
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
import sys
import tempfile
import time

ASSETS = Path(__file__).with_suffix('')
ROLES = ('producer', 'consumer')
SEAMS = ('units', 'both_features', 'rounding', 'inventory', 'retry_safety', 'persistence', 'receipts')
SCOPE = 'experiment/torture-refunds-v1'


def utc():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2) + '\n')


def manifest(root, ignore_cache=False):
    result = {}
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d != '.git' and not (ignore_cache and d == '__pycache__'))
        for name in sorted(set(dirs + files)):
            path = Path(directory) / name
            info = path.lstat()
            key = str(path.relative_to(root))
            if stat.S_ISLNK(info.st_mode):
                result[key] = {'link': os.readlink(path)}
            elif stat.S_ISREG(info.st_mode):
                raw = path.read_bytes()
                result[key] = {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw), 'mode': stat.S_IMODE(info.st_mode)}
            elif not stat.S_ISDIR(info.st_mode):
                raise ValueError('Cannot faithfully archive special file: ' + key)
    return result


def command(codex, checkout, prompt, model, effort):
    # Same native invocation used in the previous microstudy.
    return [codex, 'exec', '--json', '--sandbox', 'workspace-write', '-m', model,
            '-c', f'model_reasoning_effort="{effort}"', '-C', str(checkout), prompt]


def verify_inputs(root, plan):
    if (root / 'pi-source').exists():
        raise ValueError('Control must not contain a PI source bundle')
    for name, digest in plan['input_hashes'].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Frozen input changed: ' + name)


def record(root, role, binary, plan):
    directory = root / role
    directory.mkdir()
    argv = command(binary, root / 'work', (root / (role + '.txt')).read_text(), plan['model'], plan['effort'])
    write_json(directory / 'command.json', argv)
    row = {'role': role, 'started_at': utc(), 'start_monotonic_ns': time.monotonic_ns()}
    with (directory / 'stdout.jsonl').open('wb') as out, (directory / 'stderr.bin').open('wb') as err:
        try:
            process = subprocess.Popen(argv, cwd=root / 'work', stdin=subprocess.DEVNULL, stdout=out, stderr=err)
            row['pid'] = process.pid
            write_json(directory / 'started.json', row)
            row['exit_code'] = process.wait()
        except OSError as exc:
            row.update(exit_code=None, launch_error=str(exc))
    row.update(finished_at=utc(), end_monotonic_ns=time.monotonic_ns())
    row['elapsed_seconds'] = (row['end_monotonic_ns'] - row['start_monotonic_ns']) / 1e9
    write_json(directory / 'result.json', row)
    return row


def run(root, codex='codex'):
    root = Path(root).resolve(strict=True)
    plan = json.loads((root / 'plan.json').read_text())
    verify_inputs(root, plan)
    if manifest(root / 'work') != json.loads((root / 'before.json').read_text()):
        raise ValueError('Prepared checkout changed before launch')
    binary = shutil.which(codex)
    if not binary:
        raise ValueError('Native Codex executable unavailable')
    version = subprocess.check_output([binary, '--version'], text=True).strip()
    # Exclusive marker prevents repeats; no automatic retry overwrites a run.
    with (root / 'started.json').open('x') as stream:
        json.dump({'at': utc(), 'codex': binary, 'version': version}, stream)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(record, root, role, binary, plan) for role in ROLES]
        rows = [future.result() for future in futures]
    shutil.copytree(root / 'work', root / 'after', symlinks=True, ignore=shutil.ignore_patterns('.git'))
    write_json(root / 'after.json', manifest(root / 'after'))
    verify_inputs(root, plan)
    summary = {'workers': rows,
        'wall_seconds': (max(r['end_monotonic_ns'] for r in rows) - min(r['start_monotonic_ns'] for r in rows)) / 1e9,
        'completion': 'Processes exited, not an acceptance verdict', 'control_runs': 1}
    write_json(root / 'summary.json', summary)
    return summary


def check(root):
    root = Path(root).resolve(strict=True)
    if not (root / 'summary.json').is_file():
        raise ValueError('Wait for both workers to exit; no mid-run scoring/feedback')
    plan = json.loads((root / 'plan.json').read_text())
    verify_inputs(root, plan)
    before = json.loads((root / 'before.json').read_text())
    after = json.loads((root / 'after.json').read_text())
    if manifest(root / 'after') != after:
        raise ValueError('Archived output changed')
    differences = [name for name in sorted(before.keys() | after.keys()) if before.get(name) != after.get(name)]
    # Inspect literal differences first. Execute only a disposable copy; discard
    # bytecode caches so probes exercise recorded source, not a stale worker cache.
    with tempfile.TemporaryDirectory(prefix='pi-seven-check-') as directory:
        target = Path(directory) / 'source'
        shutil.copytree(root / 'after', target, symlinks=True, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.pi'))
        if any('link' in item for item in manifest(target).values()):
            raise ValueError('Candidate contains symlinks; inspect before executing post-run probes')
        process = subprocess.run([sys.executable, '-B', '-I', str(root / 'check_contract.py'), str(target)],
                                 cwd=target, capture_output=True, text=True, timeout=20)
        if process.returncode:
            raise ValueError('Post-run probe failed: ' + process.stderr)
        result = json.loads(process.stdout)
    result.update(byte_different_files=differences, control_runs=1,
                  baseline=plan['baseline'], process_results=json.loads((root / 'summary.json').read_text()))
    with (root / 'results.json').open('x') as stream:
        json.dump(result, stream, indent=2)
    return result



def prepare(model='gpt-5.6-luna', effort='high', parent=None):
    root = Path(tempfile.mkdtemp(prefix='shop-torture-', dir=parent)).resolve()
    shutil.copytree(ASSETS / 'fixture', root / 'work', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    subprocess.run(['git', 'init', '-q', str(root / 'work')], check=True)
    for role in ROLES:
        shutil.copy2(ASSETS / (role + '.txt'), root / (role + '.txt'))
    shutil.copy2(Path(__file__), root / 'recorder.py')
    shutil.copy2(Path(__file__).with_name('torture_refunds_check.py'), root / 'check_contract.py')
    before = manifest(root / 'work')
    if any('link' in row for row in before.values()):
        raise ValueError('Fixture must not contain symlinks')
    assert not (root / 'work/AGENTS.md').exists() and not (root / 'work/.pi').exists()
    shutil.copytree(root / 'work', root / 'before', ignore=shutil.ignore_patterns('.git'))
    write_json(root / 'before.json', before)
    inputs = {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
              for name in ('producer.txt', 'consumer.txt', 'recorder.py', 'check_contract.py')}
    write_json(root / 'plan.json', {
        'version': 'torture-refunds/control-v1', 'model': model, 'effort': effort,
        'roles': list(ROLES), 'problems': list(SEAMS), 'input_hashes': inputs,
        'control_runs': 1, 'pi_enabled': False, 'created_at': utc(),
        'execution': 'One trial: two concurrent native Codex workers in one shared checkout',
        'baseline': 'New overlapping-edit fixture; older seven-label scores are not directly comparable.',
        'limits': 'Native configuration inherited, no hardened host read isolation. No deadlines, steering, retries or next trial. Reference solution and scorer are not supplied in the worker checkout.'})
    return root


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    setup = sub.add_parser('prepare')
    setup.add_argument('--model', default='gpt-5.6-luna')
    setup.add_argument('--effort', default='high', choices=('low', 'medium', 'high', 'xhigh', 'max'))
    setup.add_argument('--parent', type=Path)
    for action in ('run', 'check'):
        sub.add_parser(action).add_argument('root', type=Path)
    args = parser.parse_args()
    if args.action == 'prepare':
        print(prepare(args.model, args.effort, args.parent))
    else:
        print(json.dumps(run(args.root) if args.action == 'run' else check(args.root), indent=2))


if __name__ == '__main__':
    main()
