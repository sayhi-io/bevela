"""Identical-objective native Codex study, original seven seams, version 1.

Only launch/record/isolate: no assigned roles, model feedback or repair controller.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
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

from experiments import concurrency_study as base

VERSION = 'seven-seams-self-organizing/v4'
CONDITIONS = {'A': 1, 'B': 3, 'C': 3, 'D': 1}
SCOPE = 'experiment/seven-seams-self-organizing-v4'
PROMPT = '''Implement the complete seven-seam project migration and preserve all existing and required behavior. Other workers may be working concurrently on this same project.

Your responsibility is to make useful progress toward the complete accepted result while avoiding unnecessary duplicate work and incompatible changes.

Inspect the repository and use the normal development and coordination capabilities available in your environment. Decide for yourself what work to take on, what has already been handled, what remains, and what needs integration or repair.

Do not wait for a human to divide the task.

The project is complete only when the combined repository passes the frozen seven-seam acceptance checker.
'''
COMMON = '''# Project information

The complete requirements are in OBJECTIVE.md; existing helper contracts are in README.md.
Use `python3 -m unittest -v` for the existing tests and
`python3 acceptance.py .` for the frozen seven-seam acceptance checker.
'''
sha, manifest, write_json, utc = base.sha, base.manifest, base.write_json, base.utc


def prepare(condition, pi_source, parent=None, model='gpt-5.6-luna', effort='medium', timeout=600):
    started = time.monotonic()
    root = Path(tempfile.mkdtemp(prefix='seam-self-', dir=parent)).resolve()
    work = root / 'work'
    shutil.copytree(base.original.ASSETS / 'fixture', work,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    requirements = '\n'.join((base.original.ASSETS / (r + '.txt')).read_text()
                             for r in base.original.ROLES)
    (work / 'OBJECTIVE.md').write_text(requirements)
    (root / 'common.txt').write_text(PROMPT)
    roles = ['worker' + str(i + 1) for i in range(CONDITIONS[condition])]
    for role in roles:
        (root / (role + '.txt')).write_text(PROMPT)
        profile = root / 'native' / role
        profile.mkdir(parents=True)
        # Fresh stock profile: no old sessions, memory, plugins or task instructions.
        (profile / 'config.toml').write_text('service_tier = "default"\n'
            f'[projects.{json.dumps(str(work))}]\ntrust_level = "trusted"\n')
    (work / 'AGENTS.md').write_text(COMMON)
    pi_manifest = None
    if condition in ('C', 'D'):
        frozen = root / 'pi-source'
        for name in ('project_intent', 'skills/project-intent'):
            source = Path(pi_source) / name
            if source.is_symlink() or any('link' in r for r in manifest(source).values()):
                raise ValueError('PI source contains links')
            shutil.copytree(source, frozen / name,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        (frozen / 'docs').mkdir()
        for name in base.OPERATIONAL_DOCS:
            shutil.copy2(Path(pi_source) / 'docs' / name, frozen / 'docs' / name)
        for name in ('README.md', 'pyproject.toml'):
            shutil.copy2(Path(pi_source) / name, frozen / name)
        pi_manifest = manifest(frozen)
        context = work / '.pi'
        context.mkdir()
        write_json(context / 'snapshot.json', {'version': 1, 'scope_id': SCOPE,
            'source': {'provider': 'snapshot', 'authoritative': False,
                       'captured_at': utc(), 'mode': 'offline_snapshot'},
            'mission': PROMPT.strip(), 'records': [{
                'kind': 'workstream', 'id': 'PROJECT', 'revision': '1', 'state': 'active',
                'statement': 'Complete the seven-seam shop migration and presentation.',
                'scope': requirements, 'acceptance': [requirements],
                'boundaries': ['shop/' + s for s in base.original.SEAMS],
                'readiness': {}, 'source_checkout': str(work)}]})
        write_json(context / 'worker.json', {'scopes': {SCOPE: {
            'snapshot': str(context / 'snapshot.json'),
            'enrollment_directory': str(context / 'presence'),
            'report_directory': str(context / 'reports')}}})
        prefix = shlex.join(['/usr/bin/python3', '-B', '-I', str(frozen / 'project_intent/_worker_cli.py'),
                            '--worker-config', str(context / 'worker.json'), '--scope', SCOPE])
        (work / 'AGENTS.md').write_text(COMMON + '\n# Project Intent\n\n'
            'This checkout uses a frozen PI source version with a local task inventory '
            'and cooperative presence, not a production provider connection.\n\n'
            f'PI CLI prefix for every command: `{prefix}`.\n'
            f'Read its skill at `{frozen / "skills/project-intent/SKILL.md"}` and relevant linked guidance. '
            'Use your own CODEX_THREAD_ID with --session for local presence.\n\n'
            + (frozen / 'skills/project-intent/assets/worker-instructions.md').read_text())
    checker = Path(base.original.__file__).with_name('seven_seams_check.py')
    shutil.copy2(checker, root / 'check_contract.py')
    shutil.copy2(checker, work / 'acceptance.py')
    (work / '.gitignore').write_text('__pycache__/\n*.pyc\n.pi/presence/\n.pi/reports/\n')
    subprocess.run(['git', 'init', '-q', str(work)], check=True)
    subprocess.run(['git', '-C', str(work), 'add', '.'], check=True)
    subprocess.run(['git', '-C', str(work), '-c', 'user.name=Fixture', '-c',
                    'user.email=fixture@example.invalid', 'commit', '-qm', 'Frozen initial project'], check=True)
    shutil.copytree(work, root / 'before', ignore=shutil.ignore_patterns('.git'))
    write_json(root / 'before.json', manifest(work))
    write_json(root / 'plan.json', {'version': VERSION, 'condition': condition, 'roles': roles,
        'model': model, 'effort': effort, 'created_at': utc(), 'pi_enabled': pi_manifest is not None,
        'pi_manifest': pi_manifest, 'timeout_seconds': timeout,
        'setup_seconds': time.monotonic() - started,
        'input_hashes': {n: sha(root / n) for n in ['common.txt', 'check_contract.py'] + [r + '.txt' for r in roles]},
        'recorder_hashes': {Path(m.__file__).name: sha(m.__file__) for m in (base, base.original)},
        'self_recorder_sha256': sha(__file__),
        'profile_hashes': {r: sha(root / 'native' / r / 'config.toml') for r in roles},
        'fixture_manifest': manifest(base.original.ASSETS / 'fixture', ignore_cache=True),
        'task_hashes': {r: sha(base.original.ASSETS / (r + '.txt')) for r in base.original.ROLES},
        'limits': 'Fresh native profiles and mount/PID namespaces; only own checkout, own profile, '
            'system tools and optional frozen PI bundle mounted. No prior evidence or peer transcripts. '
            'Network retained for native authentication/inference; not a hostile-code network security boundary. '
            'Source sampling 100ms is not an atomic journal. No worker follow-ups.'})
    return root


def verify(root, plan):
    base.verify(root, plan)
    if sha(__file__) != plan['self_recorder_sha256']:
        raise ValueError('Self-organizing recorder changed')
    if plan['roles'] != ['worker' + str(i + 1) for i in range(CONDITIONS[plan['condition']])]:
        raise ValueError('Worker count changed')
    if any((root / (r + '.txt')).read_text() != PROMPT for r in plan['roles']):
        raise ValueError('Prompts are not identical')


def sandbox(root, role, argv, auth=None):
    """Mount only this project and this worker's fresh native profile, not host evidence."""
    user = Path.home()
    native_home = user / '.codex'
    npm = user / '.npm-global'
    args = ['/usr/bin/bwrap', '--die-with-parent', '--unshare-pid', '--new-session',
        '--ro-bind', '/usr', '/usr', '--symlink', 'usr/bin', '/bin',
        '--symlink', 'usr/sbin', '/sbin', '--symlink', 'usr/lib', '/lib',
        '--ro-bind', '/etc', '/etc', '--proc', '/proc', '--dev', '/dev',
        '--tmpfs', '/tmp', '--dir', str(user), '--ro-bind', str(npm), str(npm),
        '--bind', str(root / 'work'), str(root / 'work'),
        '--bind', str(root / 'native' / role), str(native_home),
        '--unsetenv', 'CODEX_HOME', '--unsetenv', 'CODEX_SQLITE_HOME', '--unsetenv', 'CODEX_THREAD_ID',
        '--unsetenv', 'PYTHONPATH', '--chdir', str(root / 'work')]
    resolver = Path('/etc/resolv.conf').resolve(strict=True)
    if not resolver.is_relative_to('/etc'):
        args += ['--ro-bind', str(resolver), str(resolver)]
    if auth is not None:
        args += ['--ro-bind', str(auth), str(native_home / 'auth.json')]
    if (root / 'pi-source').exists():
        args += ['--ro-bind', str(root / 'pi-source'), str(root / 'pi-source')]
    return args + list(argv)


def preflight(root, codex):
    plan = json.loads((root / 'plan.json').read_text())
    verify(root, plan)
    for role in plan['roles']:
        # No inference. Check namespace isolation, Git, original tests, CLI executable.
        code = ('import pathlib, subprocess, socket; '
            f'assert not pathlib.Path({str(root / "before")!r}).exists(); '
            f'assert not pathlib.Path({str(Path.home() / "sayhi/state")!r}).exists(); '
            'assert not list((pathlib.Path.home()/".codex/sessions").glob("**/*.jsonl")); '
            'assert socket.getaddrinfo("chatgpt.com",443); '
            'subprocess.run(["git","status","--porcelain"],check=True); '
            'subprocess.run(["python3","-B","-m","unittest","-q"],check=True); '
            f'subprocess.run([{codex!r},"--version"],check=True); '
            f'subprocess.run([{codex!r},"sandbox","-c",\'sandbox_mode="danger-full-access"\',"--",'
            '"/usr/bin/python3","-c",'
            '\'from pathlib import Path; p=Path(".sandbox-preflight-probe"); '
            'p.write_text("probe"); p.unlink()\'],check=True)')
        result = subprocess.run(sandbox(root, role, ['/usr/bin/python3', '-c', code]),
                                capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise ValueError('Isolation preflight failed: ' + result.stderr)
    if plan['pi_enabled']:
        args = ['/usr/bin/python3', '-B', '-I', str(root / 'pi-source/project_intent/_worker_cli.py'),
            '--worker-config', str(root / 'work/.pi/worker.json'), '--scope', SCOPE,
            'onboard', '--workstream', 'PROJECT']
        data = json.loads(subprocess.check_output(sandbox(root, plan['roles'][0], args), text=True))
        assert data['orientation']['assignment']['id'] == 'PROJECT'
    # Python tests may create ignored bytecode; remove only the generated cache in this disposable checkout.
    cache = root / 'work/__pycache__'
    if cache.exists():
        shutil.rmtree(cache)
    assert manifest(root / 'work') == json.loads((root / 'before.json').read_text())


def record(root, role, binary, plan, observer):
    directory = root / role
    directory.mkdir()
    native = base.original.command(binary, root / 'work', (root / (role + '.txt')).read_text(),
                                   plan['model'], plan['effort'])
    # Exactly one sandbox: the outer namespace enforces allowed mounts/writes.
    native[native.index('--sandbox') + 1] = 'danger-full-access'
    native[1:1] = ['--ask-for-approval', 'never']
    argv = sandbox(root, role, native, Path.home() / '.codex/auth.json')
    write_json(directory / 'command.json', native)
    write_json(directory / 'isolation-command.json', argv)
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


def run(root, codex='codex'):
    root = Path(root).resolve(strict=True)
    plan = json.loads((root / 'plan.json').read_text())
    verify(root, plan)
    assert manifest(root / 'work') == json.loads((root / 'before.json').read_text())
    for role, digest in plan['profile_hashes'].items():
        assert sha(root / 'native' / role / 'config.toml') == digest
    binary = shutil.which(codex)
    if not binary:
        raise ValueError('Codex not installed')
    with (root / 'started.json').open('x') as stream:
        json.dump({'at': utc(), 'binary': binary,
            'version': subprocess.check_output([binary, '--version'], text=True).strip()}, stream)
    observer = base.SourceObserver(root)
    observer.capture('initial')
    stop = threading.Event()
    def poll():
        while not stop.wait(.1):
            observer.capture()
    monitor = threading.Thread(target=poll, daemon=True)
    monitor.start()
    try:
        with ThreadPoolExecutor(max_workers=len(plan['roles'])) as pool:
            futures = [pool.submit(record, root, r, binary, plan, observer) for r in plan['roles']]
            rows = [f.result() for f in futures]
    finally:
        stop.set()
        monitor.join()
        observer.capture('final')
        observer.close()
    window = base.concurrency(rows)
    archive_start = time.monotonic_ns()
    shutil.copytree(root / 'work', root / 'after', symlinks=True, ignore=shutil.ignore_patterns('.git'))
    write_json(root / 'after.json', manifest(root / 'after'))
    verify(root, plan)
    check_start = time.monotonic_ns()
    result = base.score(root)
    end = time.monotonic_ns()
    accepted = result.get('score') == 7 and all(r.get('exit_code') == 0 and not r.get('timed_out') for r in rows)
    summary = {'condition': plan['condition'], 'model': plan['model'], 'effort': plan['effort'],
        'workers': rows, 'concurrency': window, 'result': result, 'accepted': accepted,
        'setup_seconds': plan['setup_seconds'], 'archive_seconds': (check_start - archive_start) / 1e9,
        'verification_seconds': (end - check_start) / 1e9,
        'project_seconds': (end - window['start_ns']) / 1e9,
        'accepted_project_seconds': (end - window['start_ns']) / 1e9 if accepted else None,
        'checker_modified': sha(root / 'after/acceptance.py') != sha(root / 'check_contract.py'),
        'external_repair_seconds': 0, 'human_interventions': 0,
        'timing_note': 'Final verification after all native exits. Earlier worker verification and sampled '
            'source correctness analyzed post hoc, not live feedback. In-session repair included in execution.'}
    write_json(root / 'results.json', summary)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'run', 'preflight'))
    parser.add_argument('--root', type=Path)
    parser.add_argument('--condition', choices=CONDITIONS)
    parser.add_argument('--pi-source', type=Path)
    parser.add_argument('--codex', default='/home/meanaverage/.npm-global/bin/codex')
    args = parser.parse_args()
    if args.action == 'prepare':
        print(prepare(args.condition, args.pi_source))
    elif args.action == 'preflight':
        preflight(args.root, args.codex)
    else:
        print(json.dumps(run(args.root, args.codex), indent=2))
