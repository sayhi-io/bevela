"""Versioned four-arm extension of seven_seams; passive native execution only.

No evaluator feedback, workflow barriers, worker retries or PI implementation edits.
Evidence stays outside work: exact streams, timestamped events and source snapshots.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time

from experiments import seven_seams as original

VERSION = 'seven-seams-concurrency/v2'
OPERATIONAL_DOCS = ('ARCHITECTURE.md', 'OPERATIONS.md', 'READ_MODEL.md',
                    'REPORTING.md', 'TASK_REGISTRATION.md', 'SESSION_CONNECTOR.md',
                    'REPAIR_COORDINATION.md')
CONDITIONS = {'A': ('solo',), 'B': ('producer', 'consumer'),
              'C': ('producer', 'consumer'), 'D': ('solo',)}
COMMON = '# Task information\n\nThe two project task texts are in tasks/producer.txt and tasks/consumer.txt.\n'
SCOPE = 'experiment/seven-seams-concurrency-v1'
write_json = original.write_json
manifest = original.manifest
utc = original.utc


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare(condition, pi_source, parent=None, model='gpt-5.6-luna', effort='medium', timeout=600):
    start = time.monotonic()
    roles = CONDITIONS[condition]
    root = Path(tempfile.mkdtemp(prefix='seam-project-', dir=parent)).resolve()
    work = root / 'work'
    shutil.copytree(original.ASSETS / 'fixture', work,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    subprocess.run(['git', 'init', '-q', str(work)], check=True)
    (work / 'tasks').mkdir()
    for role in original.ROLES:
        shutil.copy2(original.ASSETS / (role + '.txt'), work / 'tasks' / (role + '.txt'))
        shutil.copy2(original.ASSETS / (role + '.txt'), root / (role + '.txt'))
    combined = 'Complete both tasks below in this session.\n\n' + '\n'.join(
        (root / (role + '.txt')).read_text() for role in original.ROLES)
    (root / 'solo.txt').write_text(combined)
    (work / 'AGENTS.md').write_text(COMMON)
    pi_enabled = condition in ('C', 'D')
    pi_manifest = None
    if pi_enabled:
        frozen = root / 'pi-source'
        for name in ('project_intent', 'skills/project-intent'):
            source = Path(pi_source) / name
            if source.is_symlink() or any('link' in r for r in manifest(source).values()):
                raise ValueError('PI input contains a link')
            shutil.copytree(source, frozen / name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        (frozen / 'docs').mkdir()
        for name in OPERATIONAL_DOCS:
            shutil.copy2(Path(pi_source) / 'docs' / name, frozen / 'docs' / name)
        for name in ('README.md', 'pyproject.toml'):
            shutil.copy2(Path(pi_source) / name, frozen / name)
        pi_manifest = manifest(frozen)
        context = work / '.pi'
        context.mkdir()
        # Every task fact is also in the ordinary checkout; no evaluator contracts.
        texts = [(role, (root / (role + '.txt')).read_text().strip()) for role in roles]
        snapshot = {'version': 1, 'scope_id': SCOPE,
            'source': {'provider': 'snapshot', 'authoritative': False,
                       'captured_at': utc(), 'mode': 'offline_snapshot'},
            'mission': 'Complete the tasks in tasks/producer.txt and tasks/consumer.txt.',
            'records': [{'kind': 'workstream', 'id': role.upper(), 'revision': '1', 'state': 'active',
                'statement': text, 'scope': text, 'acceptance': [text],
                'boundaries': ['shop/' + seam for seam in original.SEAMS],
                'readiness': {}, 'source_checkout': str(work)} for role, text in texts]}
        write_json(context / 'snapshot.json', snapshot)
        write_json(context / 'worker.json', {'scopes': {SCOPE: {
            'snapshot': str(context / 'snapshot.json'),
            'enrollment_directory': str(context / 'presence'),
            'report_directory': str(context / 'reports')}}})
        prefix = shlex.join([sys.executable, '-B', '-I', str(frozen / 'project_intent/_worker_cli.py'),
                            '--worker-config', str(context / 'worker.json'), '--scope', SCOPE])
        (work / 'AGENTS.md').write_text(COMMON + '\n# Project Intent\n\n'
            'This checkout uses a frozen PI source version with a local task inventory '
            'and cooperative presence, not a production provider connection.\n\n'
            f'PI CLI prefix for every command: `{prefix}`.\n'
            f'Read its skill at `{frozen / "skills/project-intent/SKILL.md"}` and relevant linked guidance. '
            'Use your own CODEX_THREAD_ID with --session for local presence.\n\n'
            + (frozen / 'skills/project-intent/assets/worker-instructions.md').read_text())
    shutil.copy2(Path(original.__file__).with_name('seven_seams_check.py'), root / 'check_contract.py')
    shutil.copytree(work, root / 'before', ignore=shutil.ignore_patterns('.git'))
    write_json(root / 'before.json', manifest(work))
    write_json(root / 'plan.json', {'version': VERSION, 'condition': condition, 'roles': roles,
        'model': model, 'effort': effort, 'created_at': utc(), 'pi_enabled': pi_enabled,
        'pi_manifest': pi_manifest, 'timeout_seconds': timeout,
        'setup_seconds': time.monotonic() - start,
        'input_hashes': {name: sha(root / name) for name in
                         ('producer.txt', 'consumer.txt', 'solo.txt', 'check_contract.py')},
        'recorder_hashes': {'concurrency_study.py': sha(__file__), 'seven_seams.py': sha(original.__file__)},
        'fixture_manifest': manifest(original.ASSETS / 'fixture', ignore_cache=True),
        'limits': 'Inherited native configuration; not hardened host read isolation. '
                  'No prior evidence supplied. Checker remains observer-only. '
                  'Source observations sampled at 100ms, not an atomic filesystem journal.'})
    return root


def verify(root, plan):
    for name, path in [('concurrency_study.py', __file__), ('seven_seams.py', original.__file__)]:
        if sha(path) != plan['recorder_hashes'][name]:
            raise ValueError('Recorder source changed: ' + name)
    for name, digest in plan['input_hashes'].items():
        if sha(root / name) != digest:
            raise ValueError('Frozen input changed: ' + name)
    if plan['pi_enabled']:
        if manifest(root / 'pi-source', ignore_cache=True) != plan['pi_manifest']:
            raise ValueError('Frozen PI changed')
    elif (root / 'pi-source').exists():
        raise ValueError('Control has a PI bundle')


class SourceObserver:
    """Read-only sampled byte history; intentionally knows nothing about correctness."""
    def __init__(self, root):
        self.root = root
        self.lock = threading.Lock()
        self.previous = None
        (root / 'objects').mkdir()
        self.stream = (root / 'source-history.jsonl').open('w')

    def capture(self, trigger='poll'):
        with self.lock:
            files = {}
            errors = []
            for directory, dirs, names in os.walk(self.root / 'work', followlinks=False):
                dirs[:] = sorted(d for d in dirs if d not in ('.git', '.pi', '__pycache__', '.venv'))
                for name in sorted(names):
                    path = Path(directory) / name
                    if path.suffix == '.pyc' or path.is_symlink():
                        continue
                    try:
                        raw = path.read_bytes()
                        digest = hashlib.sha256(raw).hexdigest()
                        target = self.root / 'objects' / digest
                        if not target.exists():
                            target.write_bytes(raw)
                        files[str(path.relative_to(self.root / 'work'))] = digest
                    except OSError as exc:
                        errors.append(str(exc))
            if files != self.previous or errors:
                self.stream.write(json.dumps({'at': utc(), 'mono_ns': time.monotonic_ns(),
                    'trigger': trigger, 'files': files, 'errors': errors}) + '\n')
                self.stream.flush()
                self.previous = files

    def close(self):
        self.stream.close()


def record(root, role, binary, plan, observer):
    directory = root / role
    directory.mkdir()
    argv = original.command(binary, root / 'work', (root / (role + '.txt')).read_text(),
                            plan['model'], plan['effort'])
    write_json(directory / 'command.json', argv)
    row = {'role': role, 'started_at': utc(), 'start_monotonic_ns': time.monotonic_ns()}
    with (directory / 'stdout.jsonl').open('wb') as out, (directory / 'stderr.bin').open('wb') as err, \
            (directory / 'events.jsonl').open('w') as events:
        try:
            process = subprocess.Popen(argv, cwd=root / 'work', stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=err, start_new_session=True)
            row['pid'] = process.pid
            write_json(directory / 'started.json', row)
            def consume():
                for raw in process.stdout:
                    stamp = time.monotonic_ns()
                    out.write(raw)
                    out.flush()
                    try:
                        event = json.loads(raw)
                    except ValueError:
                        event = {'unparsed_utf8': raw.decode(errors='replace')}
                    events.write(json.dumps({'mono_ns': stamp, 'at': utc(), 'event': event}) + '\n')
                    events.flush()
                    if event.get('item', {}).get('type') == 'file_change':
                        observer.capture(role + ':' + event.get('type', 'event'))
            reader = threading.Thread(target=consume, daemon=True)
            reader.start()
            try:
                row['exit_code'] = process.wait(timeout=plan['timeout_seconds'])
            except subprocess.TimeoutExpired:
                row['timed_out'] = True
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                row['exit_code'] = process.returncode
            reader.join(timeout=10)
            row['stream_complete'] = not reader.is_alive()
        except OSError as exc:
            row.update(exit_code=None, launch_error=str(exc))
    row.update(finished_at=utc(), end_monotonic_ns=time.monotonic_ns())
    row['elapsed_seconds'] = (row['end_monotonic_ns'] - row['start_monotonic_ns']) / 1e9
    write_json(directory / 'result.json', row)
    return row


def concurrency(rows):
    start = min(r['start_monotonic_ns'] for r in rows)
    end = max(r['end_monotonic_ns'] for r in rows)
    duration = (end - start) / 1e9
    total = sum((r['end_monotonic_ns'] - r['start_monotonic_ns']) / 1e9 for r in rows)
    changes = sorted([(r['start_monotonic_ns'], 1) for r in rows] +
                     [(r['end_monotonic_ns'], -1) for r in rows])
    active = 0
    peak = 0
    timeline = []
    for stamp, delta in changes:
        active += delta
        peak = max(peak, active)
        timeline.append({'seconds': (stamp - start) / 1e9, 'active': active})
    return {'start_ns': start, 'end_ns': end, 'worker_interval_seconds': duration,
        'worker_seconds': total, 'factor': total / duration if duration else 0,
        'max_simultaneous': peak, 'active_timeline': timeline}


def score(root):
    """One frozen final evaluation on a private copy, never the workers' checkout."""
    with tempfile.TemporaryDirectory(prefix='seam-verify-') as directory:
        target = Path(directory) / 'source'
        shutil.copytree(root / 'after', target, symlinks=True,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.pi'))
        if any('link' in r for r in manifest(target).values()):
            return {'evaluation_error': 'Candidate contains links; probes not executed'}
        try:
            result = subprocess.run([sys.executable, '-B', '-I', str(root / 'check_contract.py'), str(target)],
                                    cwd=target, capture_output=True, text=True, timeout=20)
            return json.loads(result.stdout) if result.returncode == 0 else {
                'evaluation_error': result.stderr, 'checker_exit': result.returncode}
        except (ValueError, subprocess.TimeoutExpired) as exc:
            return {'evaluation_error': str(exc)}


def run(root, codex='codex'):
    root = Path(root).resolve(strict=True)
    plan = json.loads((root / 'plan.json').read_text())
    verify(root, plan)
    if manifest(root / 'work') != json.loads((root / 'before.json').read_text()):
        raise ValueError('Initial checkout changed')
    binary = shutil.which(codex)
    if not binary:
        raise ValueError('Codex not installed')
    with (root / 'started.json').open('x') as stream:
        json.dump({'at': utc(), 'binary': binary,
                   'version': subprocess.check_output([binary, '--version'], text=True).strip()}, stream)
    observer = SourceObserver(root)
    observer.capture('initial')
    stop = threading.Event()
    def poll():
        while not stop.wait(.1):
            observer.capture()
    monitor = threading.Thread(target=poll, daemon=True)
    monitor.start()
    try:
        with ThreadPoolExecutor(max_workers=len(plan['roles'])) as pool:
            futures = [pool.submit(record, root, role, binary, plan, observer) for role in plan['roles']]
            rows = [f.result() for f in futures]
    finally:
        stop.set()
        monitor.join()
        observer.capture('final')
        observer.close()
    window = concurrency(rows)
    archive_start = time.monotonic_ns()
    shutil.copytree(root / 'work', root / 'after', symlinks=True, ignore=shutil.ignore_patterns('.git'))
    write_json(root / 'after.json', manifest(root / 'after'))
    verify(root, plan)
    verification_start = time.monotonic_ns()
    result = score(root)
    end = time.monotonic_ns()
    accepted = result.get('score') == 7 and all(r.get('exit_code') == 0 and not r.get('timed_out') for r in rows)
    summary = {'condition': plan['condition'], 'model': plan['model'], 'effort': plan['effort'],
        'workers': rows, 'concurrency': window, 'result': result, 'accepted': accepted,
        'setup_seconds': plan['setup_seconds'],
        'archive_seconds': (verification_start - archive_start) / 1e9,
        'verification_seconds': (end - verification_start) / 1e9,
        'project_seconds': (end - window['start_ns']) / 1e9,
        'accepted_project_seconds': (end - window['start_ns']) / 1e9 if accepted else None,
        'external_repair_seconds': 0, 'human_interventions': 0,
        'timing_note': 'First final verification occurs after all native workers exit. '
            'In-session integration/repair is included in execution, classified post hoc only. '
            'Failed durations are time-to-final-failure, not time-to-correct-project.'}
    write_json(root / 'results.json', summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'run'))
    parser.add_argument('--condition', choices=CONDITIONS)
    parser.add_argument('--pi-source', type=Path)
    parser.add_argument('--model', default='gpt-5.6-luna')
    parser.add_argument('--effort', default='medium')
    parser.add_argument('--root', type=Path)
    parser.add_argument('--timeout', type=int, default=600)
    args = parser.parse_args()
    if args.action == 'prepare':
        print(prepare(args.condition, args.pi_source, model=args.model, effort=args.effort, timeout=args.timeout))
    else:
        print(json.dumps(run(args.root), indent=2))


if __name__ == '__main__':
    main()
