"""Seven-problem PI-only fixture and passive native Codex recorder.

prepare never launches a model. run launches exactly two native sessions once.
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
SEAMS = ('prices', 'stock', 'weights', 'discounts', 'delivery', 'contacts', 'orders')
SCOPE = 'experiment/seven-seams-v1'


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


def prepare(pi_source, parent=None, model='gpt-5.6-luna', effort='medium'):
    pi_source = Path(pi_source).resolve(strict=True)
    for name in ('project_intent/_worker_cli.py', 'skills/project-intent/SKILL.md', 'skills/project-intent/assets/worker-instructions.md'):
        if not (pi_source / name).is_file():
            raise ValueError('Select the actual PI source release with CLI and worker skill')
    root = Path(tempfile.mkdtemp(prefix='pi-seven-', dir=parent)).resolve()
    checkout = root / 'work'
    shutil.copytree(ASSETS / 'fixture', checkout)
    subprocess.run(['git', 'init', '-q', str(checkout)], check=True)
    frozen = root / 'pi-source'
    frozen.mkdir()
    # Runtime evidence keeps an exact code/doc copy, not a mutable worktree pointer.
    for name in ('project_intent', 'skills/project-intent', 'docs'):
        source = pi_source / name
        if source.is_symlink() or any('link' in entry for entry in manifest(source).values()):
            raise ValueError('Selected PI source contains links; reconcile before freezing inputs')
        shutil.copytree(source, frozen / name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in ('README.md', 'pyproject.toml'):
        if (pi_source / name).is_symlink():
            raise ValueError('Selected PI root files cannot be symlinks')
        shutil.copy2(pi_source / name, frozen / name)
    for role in ROLES:
        shutil.copy2(ASSETS / (role + '.txt'), root / (role + '.txt'))
    shutil.copy2(Path(__file__), root / 'recorder.py')
    shutil.copy2(Path(__file__).with_name('seven_seams_check.py'), root / 'check_contract.py')
    context = checkout / '.pi'
    context.mkdir()
    snapshot = {'version': 1, 'scope_id': SCOPE,
        'source': {'provider': 'snapshot', 'authoritative': False, 'captured_at': utc(), 'mode': 'offline_snapshot'},
        'mission': 'Preserve seven shop contracts while representation and presentation change concurrently.',
        'records': [{'kind': 'workstream', 'id': role.upper(), 'revision': '1', 'state': 'active',
                     'statement': (root / (role + '.txt')).read_text().strip(),
                     'scope': (root / (role + '.txt')).read_text().strip(),
                     'acceptance': [(root / (role + '.txt')).read_text().strip()],
                     'boundaries': ['shop/' + seam for seam in SEAMS], 'readiness': {},
                     'source_checkout': str(checkout)} for role in ROLES]}
    write_json(context / 'snapshot.json', snapshot)
    write_json(context / 'worker.json', {'scopes': {SCOPE: {
        'snapshot': str(context / 'snapshot.json'), 'enrollment_directory': str(context / 'presence'),
        'report_directory': str(context / 'reports')}}})
    cli = shlex.join([sys.executable, '-B', '-I', str(frozen / 'project_intent/_worker_cli.py'),
                     '--worker-config', str(context / 'worker.json'), '--scope', SCOPE])
    (checkout / 'AGENTS.md').write_text(
        '# Project Intent\n\nThis checkout uses a frozen PI source version with a local task inventory '
        'and cooperative presence, not a production provider connection.\n\n'
        f'PI CLI prefix for every command: `{cli}`.\n'
        f'Read its skill at `{frozen / "skills/project-intent/SKILL.md"}` and relevant linked guidance. '
        'Use your own CODEX_THREAD_ID with --session for local presence.\n\n'
        + (frozen / 'skills/project-intent/assets/worker-instructions.md').read_text())
    shutil.copytree(checkout, root / 'before', ignore=shutil.ignore_patterns('.git'))
    write_json(root / 'before.json', manifest(checkout))
    write_json(root / 'plan.json', {
        'version': 'seven-seams/v1', 'roles': list(ROLES), 'problems': list(SEAMS), 'scope': SCOPE,
        'created_at': utc(), 'pi_source_origin': str(pi_source), 'pi_source_manifest': manifest(frozen),
        'input_hashes': {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                         for name in ('producer.txt', 'consumer.txt', 'recorder.py', 'check_contract.py')},
        'model': model, 'effort': effort, 'control_runs': 0,
        'execution': 'Two concurrent native Codex sessions in one shared Git checkout; one run only',
        'limits': 'Native config/environment inherited. No hardened host read isolation. No steering, forced deadline or automatic next trial.',
        'baseline': 'New fixture: old one-problem control scores are not a matched quantitative baseline.'})
    return root


def command(codex, checkout, prompt, model, effort):
    # Same native invocation used in the previous microstudy.
    return [codex, 'exec', '--json', '--sandbox', 'workspace-write', '-m', model,
            '-c', f'model_reasoning_effort="{effort}"', '-C', str(checkout), prompt]


def verify_inputs(root, plan):
    if manifest(root / 'pi-source', ignore_cache=True) != plan['pi_source_manifest']:
        raise ValueError('Frozen PI input changed')
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
        'completion': 'Processes exited, not an acceptance verdict', 'control_runs': 0}
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
    result.update(byte_different_files=differences, control_runs=0,
                  baseline=plan['baseline'], process_results=json.loads((root / 'summary.json').read_text()))
    with (root / 'results.json').open('x') as stream:
        json.dump(result, stream, indent=2)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    setup = sub.add_parser('prepare')
    setup.add_argument('--pi-source', required=True, type=Path)
    setup.add_argument('--parent', type=Path)
    setup.add_argument('--model', default='gpt-5.6-luna')
    setup.add_argument('--effort', default='medium', choices=('low', 'medium', 'high', 'xhigh', 'max'))
    launch = sub.add_parser('run')
    launch.add_argument('root', type=Path)
    launch.add_argument('--codex', default='codex')
    score = sub.add_parser('check')
    score.add_argument('root', type=Path)
    args = parser.parse_args()
    if args.action == 'prepare':
        print(prepare(args.pi_source, args.parent, args.model, args.effort))
    elif args.action == 'run':
        print(json.dumps(run(args.root, args.codex), indent=2))
    else:
        print(json.dumps(check(args.root), indent=2))


if __name__ == '__main__':
    main()
