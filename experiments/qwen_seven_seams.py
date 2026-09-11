"""Original seven-seam Qwen Medium 3+3; passive native recorder, no coaching."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import fcntl
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid

from experiments import concurrency_study as common
from experiments import isolation_v2
from experiments import qwen_code_adapter as adapter

VERSION = 'qwen-original-seven-seams/v1'
ORDER = ('B1', 'C1', 'C2', 'B2', 'B3', 'C3')
MODEL = 'qwen38-27b-dflash2'
ROLES = ('producer', 'consumer')
MODULES = (common, common.original, adapter, isolation_v2)
sha, manifest, write_json, utc = common.sha, common.manifest, common.write_json, common.utc


def prepare(parent, condition, source, runtime, endpoint, timeout=1800):
    preparation_started = time.monotonic()
    if condition not in ('B', 'C') or timeout <= 0:
        raise ValueError('Expected B/C and a positive worker budget')
    parent = Path(parent)
    parent.mkdir(parents=True, exist_ok=False)
    root = common.prepare(condition, source, parent, MODEL, 'medium', timeout)
    work = root / 'work'
    # Undo ONLY the later equal-information extension. These generated task
    # copies are not part of the original fixture; never remove user source.
    for role in ROLES:
        (work / 'tasks' / (role + '.txt')).unlink()
    (work / 'tasks').rmdir()
    if condition == 'B':
        (work / 'AGENTS.md').unlink()
    else:
        path = work / 'AGENTS.md'
        path.write_text(path.read_text().removeprefix(common.COMMON).replace(
            sys.executable, '/usr/bin/python3').replace(
            'Use your own CODEX_THREAD_ID with --session for local presence.',
            'Use your own QWEN_SESSION_ID environment value with --session for local presence. '
            'You are Qwen Code, not Codex; do not use --codex.'))
        # The project README now publishes historical benchmark results. Keep
        # runtime/skill bytes, but do not mount those results to treatment workers.
        (root / 'pi-source/README.md').write_text(
            '# Project Intent worker runtime\n\nRead skills/project-intent/SKILL.md '
            'and its linked operational guidance. Use the configured CLI prefix '
            'from your actual task checkout AGENTS.md.\n')
        path = work / '.pi/snapshot.json'
        snapshot = json.loads(path.read_text())
        snapshot['mission'] = 'Preserve seven shop contracts while representation and presentation change concurrently.'
        write_json(path, snapshot)
    (work / '.gitignore').write_text('__pycache__/\n*.pyc\n.pi/presence/\n.pi/reports/\n')
    subprocess.run(['git', '-C', str(work), 'add', '.'], check=True)
    subprocess.run(['git', '-C', str(work), '-c', 'user.name=Fixture', '-c',
                    'user.email=fixture@example.invalid', 'commit', '-qm', 'Frozen original seven-seam fixture'], check=True)
    # Preserve the upstream preparation separately; regenerate only new-study
    # baseline snapshots before any worker has launched.
    (root / 'before').rename(root / 'upstream-before')
    (root / 'plan.json').rename(root / 'upstream-plan.json')
    shutil.copytree(work, root / 'before', ignore=shutil.ignore_patterns('.git'))
    write_json(root / 'before.json', manifest(work, ignore_cache=True))
    runtime = Path(runtime).resolve(strict=True)
    for path in runtime.rglob('*'):
        if path.is_symlink() and not path.resolve().is_relative_to(runtime):
            raise ValueError('External runtime symlink')
    shutil.copytree(runtime, root / 'runtime', symlinks=True)
    (root / 'DISPOSABLE_TRIAL').touch()
    sessions = {role: str(uuid.uuid4()) for role in ROLES}
    for role in ROLES:
        (root / 'qwen-home' / role).mkdir(parents=True)
    write_json(root / 'settings-template.json', adapter.settings(MODEL, endpoint, effort='medium'))
    plan = json.loads((root / 'upstream-plan.json').read_text())
    plan.update(version=VERSION, server_effort='medium', context_window=230000,
        endpoint=endpoint, sessions=sessions, before_sha256=sha(root / 'before.json'),
        pi_manifest=manifest(root / 'pi-source', ignore_cache=True) if condition == 'C' else None,
        runtime_manifest=manifest(root / 'runtime'), settings_sha256=sha(root / 'settings-template.json'),
        study_sha256=sha(__file__), module_hashes={Path(m.__file__).name: sha(m.__file__) for m in MODULES},
        information='Original own-role prompt plus shared source; PI exposes peer tasks via inventory. No shared future-task document.',
        limits='Two native Qwen workers; 230k context; native compaction; filesystem isolation, shared network. No steering or retries.',
        setup_seconds=time.monotonic()-preparation_started)
    write_json(root / 'plan.json', plan)
    return root


def verify(root, before=False):
    root = Path(root)
    plan = json.loads((root / 'plan.json').read_text())
    if (plan['version'], plan['model'], plan['effort'], plan['server_effort'], plan['roles']) != (
            VERSION, MODEL, 'medium', 'medium', list(ROLES)):
        raise ValueError('Study controls changed')
    if sha(__file__) != plan['study_sha256'] or any(
            sha(m.__file__) != plan['module_hashes'][Path(m.__file__).name] for m in MODULES):
        raise ValueError('Recorder source changed')
    common.verify(root, plan)
    if sha(root / 'before.json') != plan['before_sha256'] or sha(root / 'settings-template.json') != plan['settings_sha256']:
        raise ValueError('Frozen baseline/settings changed')
    if manifest(root / 'runtime') != plan['runtime_manifest']:
        raise ValueError('Native runtime changed')
    if before:
        if manifest(root / 'work', ignore_cache=True) != json.loads((root / 'before.json').read_text()):
            raise ValueError('Initial work changed')
        if any(list((root / 'qwen-home' / role).iterdir()) for role in ROLES):
            raise ValueError('Native home is not fresh')
    return plan


def preflight(root):
    plan = verify(root, before=True)
    for role in ROLES:
        probe_role = 'preflight-' + role
        (root/'qwen-home'/probe_role).mkdir()
        version = subprocess.run(adapter.sandbox(root,probe_role,
            ['/usr/bin/node',str(root/'runtime/bin/qwen'),'--version'],str(uuid.uuid4()),
            pi=plan['pi_enabled']),capture_output=True,text=True,timeout=30)
        if version.returncode or version.stdout.strip() != '0.23.2':
            raise RuntimeError('Frozen Qwen Code must start in isolation and report 0.23.2')
        code = ('from pathlib import Path; import subprocess; '
            f'assert not Path({str(root / "plan.json")!r}).exists(); '
            f'assert not Path({str(root / "upstream-before")!r}).exists(); '
            'assert not Path("tasks").exists(); '
            'assert not Path("/home/meanaverage/sayhi/repos").exists(); '
            'assert not list(Path.home().glob(".codex/**")); '
            'assert not list((Path.home()/".qwen").iterdir()); '
            'subprocess.run(["git","status","--porcelain"],check=True); '
            'p=Path(".isolation-probe");p.write_text("ok");p.unlink(); ')
        if plan['pi_enabled']:
            code += ('subprocess.run(["/usr/bin/python3","-B","-I",'
                f'{str(root / "pi-source/project_intent/_worker_cli.py")!r},'
                '"onboard","--worker-config",str(Path.cwd()/".pi/worker.json"),'
                f'"--scope",{common.SCOPE!r},"--workstream",{role.upper()!r}],check=True,stdout=subprocess.DEVNULL)')
        else:
            code += f'assert not Path({str(root / "pi-source")!r}).exists(); assert not Path(".pi").exists()'
        result = subprocess.run(adapter.sandbox(root, role, ['/usr/bin/python3', '-B', '-c', code],
            plan['sessions'][role], pi=plan['pi_enabled']), capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise RuntimeError('Isolation/PI preflight failed: ' + result.stderr)
    verify(root, before=True)


def telemetry(root, row, plan):
    folder = root / row['role']
    events = []
    for line in (folder / 'stdout.jsonl').read_text().splitlines():
        try:
            events.append(json.loads(line))
        except ValueError:
            pass
    transport = [json.loads(line) for line in (folder / 'transport.jsonl').read_text().splitlines()]
    initial = [e for e in events if e.get('type') == 'system' and e.get('subtype') == 'init']
    final = [e for e in events if e.get('type') == 'result']
    requests = [e for e in transport if e.get('event') == 'request']
    controls = bool(requests) and all(e.get('model') == MODEL and e.get('reasoning_effort') == 'medium'
        and e.get('chat_template_kwargs', {}).get('enable_thinking') is True
        and e.get('max_tokens') == 32768 for e in requests)
    identity = bool(initial) and all(e.get('session_id') == row['session'] and e.get('model') == MODEL for e in initial)
    final_identity = bool(final) and all(e.get('session_id') == row['session'] for e in final)
    errors = [e for e in transport if e.get('event') in ('transport_error', 'handler_error')
              or (e.get('event') == 'response' and e.get('status', 200) >= 400)]
    cutoff = row['start_monotonic_ns'] + plan['timeout_seconds'] * 1e9
    # Only a socket error at/after the actual deadline may be timeout cleanup.
    unexpected = [e for e in errors if not (row.get('timed_out') and e.get('event') == 'transport_error'
                  and e.get('mono_ns', 0) >= cutoff)]
    return dict(role=row['role'], session=row['session'], controls_verified=controls,
        initialization_verified=identity, final_identity_verified=final_identity,
        final_identity_mismatch=bool(final) and not final_identity,
        native_success=bool(final and final[-1].get('subtype') == 'success' and not final[-1].get('is_error')),
        usage=adapter.usage(folder / 'transport.jsonl'), transport_errors=errors,
        unexpected_transport_errors=unexpected,
        native_final=final, native_initialization=initial)


def score(root):
    """Same checker bytes; generated code sees only a private verification copy."""
    with tempfile.TemporaryDirectory(prefix='verification-', dir=root) as directory:
        target = Path(directory) / 'source'
        shutil.copytree(root/'after', target, symlinks=True,
            ignore=shutil.ignore_patterns('__pycache__','*.pyc','.pi'))
        if any('link' in value for value in manifest(target).values()):
            return {'evaluation_error':'Candidate contains links; no probes executed'}
        try:
            result = isolation_v2.run(root,target,
                ['/usr/bin/python3','-B','-I',str(root/'check_contract.py'),str(target)],
                readonly=[root/'check_contract.py'],timeout=20)
            return json.loads(result.stdout) if result.returncode == 0 else {
                'evaluation_error':result.stderr,'checker_exit':result.returncode}
        except (ValueError,subprocess.TimeoutExpired) as error:
            return {'evaluation_error':str(error)}


def run(root):
    root = Path(root)
    plan = verify(root, before=True)
    with (root / 'started.json').open('x') as stream:
        json.dump({'at': utc(), 'plan_sha256': sha(root / 'plan.json')}, stream)
    observer = common.SourceObserver(root)
    observer.capture('initial')
    stop = threading.Event()
    def poll():
        while not stop.wait(.1):
            observer.capture()
    monitor = threading.Thread(target=poll, daemon=True)
    monitor.start()
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(adapter.record, root, role, plan, observer) for role in ROLES]
            rows = [future.result() for future in futures]
    except Exception as error:
        write_json(root / 'infrastructure-failure.json', {'at': utc(), 'error_type': type(error).__name__,
            'meaning': 'Partial evidence retained; no automatic retry or next project.'})
        raise
    finally:
        stop.set()
        monitor.join()
        observer.capture('final')
        observer.close()
    window = common.concurrency(rows)
    archive_start = time.monotonic_ns()
    shutil.copytree(root / 'work', root / 'after', symlinks=True, ignore=shutil.ignore_patterns('.git'))
    write_json(root / 'after.json', manifest(root / 'after', ignore_cache=True))
    observed = [telemetry(root, row, plan) for row in rows]
    write_json(root / 'worker-analysis.json', observed)
    verify(root)
    verification_start = time.monotonic_ns()
    verdict = score(root)
    end = time.monotonic_ns()
    baseline = json.loads((root / 'before.json').read_text())
    final_files = manifest(root / 'after', ignore_cache=True)
    protected = ('AGENTS.md', 'README.md', '.pi/snapshot.json', '.pi/worker.json')
    changed_inputs = [name for name in protected if final_files.get(name) != baseline.get(name)]
    binding_ok = all(t['controls_verified'] and t['initialization_verified'] for t in observed)
    terminal_ok = all(row.get('timed_out') or item['final_identity_verified']
                      for row,item in zip(rows,observed))
    infra_ok = binding_ok and terminal_ok and not changed_inputs and all(not t['unexpected_transport_errors']
        and not t['final_identity_mismatch'] for t in observed) and all(
        r.get('stream_complete') and r.get('relay_complete') and not r.get('launch_error') for r in rows)
    finished = all(r.get('exit_code') == 0 and not r.get('timed_out') for r in rows) and all(
        t['native_success'] and t['final_identity_verified'] for t in observed)
    value = dict(version=VERSION, condition=plan['condition'], model=MODEL, effort='medium',
        result=verdict, accepted=verdict.get('score') == 7 and infra_ok and finished,
        workers=rows, telemetry=observed, infrastructure_ok=infra_ok, concurrency=window,
        protected_inputs_changed=changed_inputs,
        setup_seconds=plan['setup_seconds'], archive_seconds=(verification_start-archive_start)/1e9,
        verification_seconds=(end-verification_start)/1e9, project_seconds=(end-window['start_ns'])/1e9,
        human_interventions=0, external_repair_seconds=0)
    write_json(root / 'result.json', value)
    return value


def freeze(batch, source, runtime, endpoint, timeout=1800):
    batch = Path(batch).resolve()
    batch.mkdir(parents=True, exist_ok=False)
    plans = {}
    matched = None
    frozen_pi = None
    for trial in ORDER:
        root = prepare(batch / trial, trial[0], source, runtime, endpoint, timeout)
        preflight(root)
        plan = verify(root, before=True)
        signature = (plan['runtime_manifest'], plan['fixture_manifest'], plan['input_hashes'], plan['settings_sha256'])
        if matched is not None and signature != matched:
            raise ValueError('Matched inputs changed during preparation')
        matched = signature
        if plan['pi_enabled']:
            if frozen_pi is not None and plan['pi_manifest'] != frozen_pi:
                raise ValueError('PI behavior changed during preparation')
            frozen_pi = plan['pi_manifest']
        plans[trial] = dict(root=str(root.relative_to(batch)), sha256=sha(root / 'plan.json'))
    write_json(batch / 'frozen.json', dict(version=VERSION, at=utc(), order=ORDER, plans=plans,
        model=MODEL, effort='medium', study_sha256=sha(__file__),
        source_commit=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()))


def run_all(batch):
    batch = Path(batch).resolve()
    with (batch / '.execution.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        frozen = json.loads((batch / 'frozen.json').read_text())
        if frozen['version'] != VERSION or frozen['study_sha256'] != sha(__file__) or frozen['order'] != list(ORDER):
            raise ValueError('Batch freeze changed')
        # Verify all fresh projects before the first model, never silently resume.
        for trial in ORDER:
            entry = frozen['plans'][trial]
            root = batch / entry['root']
            if sha(root / 'plan.json') != entry['sha256'] or (root / 'started.json').exists():
                raise ValueError('Plan changed or project already started')
            verify(root, before=True)
        with (batch / 'started.json').open('x') as stream:
            json.dump({'at': utc(), 'frozen_sha256': sha(batch / 'frozen.json')}, stream)
        for trial in ORDER:
            root = batch / frozen['plans'][trial]['root']
            if sha(root / 'plan.json') != frozen['plans'][trial]['sha256']:
                raise ValueError('Next frozen plan changed')
            print(json.dumps({'trial': trial, 'state': 'starting', 'at': utc()}), flush=True)
            result = run(root)
            print(json.dumps({'trial':trial, 'score':result['result'].get('score'),
                'accepted':result['accepted'], 'seconds':result['project_seconds'],
                'timeouts':sum(bool(r.get('timed_out')) for r in result['workers']),
                'infrastructure_ok':result['infrastructure_ok']}), flush=True)
            if not result['infrastructure_ok'] or 'evaluation_error' in result['result']:
                raise RuntimeError('Stop after infrastructure/evaluation failure; preserve remaining projects')
        write_json(batch / 'completed.json', {'at':utc(), 'projects':len(ORDER)})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze','run'))
    parser.add_argument('batch', type=Path)
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--runtime', type=Path)
    parser.add_argument('--endpoint')
    parser.add_argument('--timeout', type=int, default=1800)
    args = parser.parse_args()
    if args.action == 'freeze':
        if not args.runtime or not args.endpoint:
            parser.error('freeze requires runtime and endpoint')
        freeze(args.batch,args.source,args.runtime,args.endpoint,args.timeout)
    else:
        run_all(args.batch)
