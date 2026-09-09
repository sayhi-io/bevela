"""Frozen distributed-project study: native launch, isolation and passive evidence.

No staged changes, actor, model feedback, automatic repairs or worker retries.
One project per invocation; component workers inside that project run concurrently.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import stat
import tempfile
import threading
import time

from experiments import concurrency_study as common
from experiments import seven_seams_self_organizing as native
from experiments import self_organizing_analysis as analysis

VERSION = 'sol-distributed/software-v1'
MODEL, EFFORT = 'gpt-5.6-sol', 'medium'
PI_COMMIT = '689a91979e313ac295e2e9277d82b4c9d0dff573'
ROLES = ('catalog', 'orders', 'settlement', 'reporting')
SCOPE = 'experiment/sol-distributed-v1'
sha, manifest, write_json, utc = common.sha, common.manifest, common.write_json, common.utc
IGNORE = shutil.ignore_patterns('__pycache__', '*.pyc')
COMMON = '''# Project execution

Read README.md, OBJECTIVE.md and the component tasks in tasks/.
All workers share this project. Use ordinary shell, Git, source inspection and tests.
Run `python3 -B acceptance.py .` for the integrated acceptance checker.
Do not change acceptance.py, OBJECTIVE.md or tasks/ to weaken the task.
You may add component tests. There will be no further task messages after launch.
'''


def copy_pi(source, target):
    for name in ('project_intent', 'skills/project-intent'):
        shutil.copytree(source / name, target / name, ignore=IGNORE)
    (target / 'docs').mkdir()
    for name in common.OPERATIONAL_DOCS:
        shutil.copy2(source / 'docs' / name, target / 'docs' / name)
    shutil.copy2(source / 'pyproject.toml', target / 'pyproject.toml')


class SourceObserver(common.SourceObserver):
    """Study-local observer includes unsupported states; historical recorder stays frozen."""
    def capture(self, trigger='poll'):
        with self.lock:
            files, errors = {}, []
            for directory, dirs, names in os.walk(self.root / 'work', followlinks=False):
                dirs[:] = sorted(d for d in dirs if d not in ('.git', '.pi', '__pycache__', '.venv'))
                for name in sorted(set(dirs + names)):
                    path = Path(directory) / name
                    relative = str(path.relative_to(self.root / 'work'))
                    try:
                        mode = path.lstat().st_mode
                        if stat.S_ISDIR(mode):
                            continue
                        if not stat.S_ISREG(mode):
                            errors.append('Unsupported filesystem entry: ' + relative)
                            continue
                        if path.suffix == '.pyc':
                            continue
                        raw = path.read_bytes()
                        digest = hashlib.sha256(raw).hexdigest()
                        target = self.root / 'objects' / digest
                        if not target.exists():
                            target.write_bytes(raw)
                        files[relative] = digest
                    except OSError as exc:
                        errors.append(relative + ': ' + str(exc))
            state = (files, errors)
            if state != self.previous:
                self.stream.write(json.dumps(dict(at=utc(), mono_ns=time.monotonic_ns(),
                    trigger=trigger, files=files, errors=errors)) + '\n')
                self.stream.flush()
                self.previous = state


def prepare(root, condition, source, fixture, checker, timeout=900):
    started = time.monotonic()
    if condition not in ('A', 'B', 'C'):
        raise ValueError('Unknown condition')
    root.mkdir(parents=True, exist_ok=False)
    work = root / 'work'
    shutil.copytree(fixture, work, ignore=IGNORE)
    shutil.copy2(checker, root / 'check_contract.py')
    shutil.copy2(checker, work / 'acceptance.py')
    roles = ['solo'] if condition == 'A' else list(ROLES)
    # The task facts and bounded component assignments are identical in B/C.
    # Solo owns all components, without obligations to fictitious peers.
    for role in roles:
        prompt = ((work / 'tasks' / (role + '.txt')).read_text() if role != 'solo' else
                  'Implement the complete migration in OBJECTIVE.md. You own all four components '
                  'in this single-worker project. The component tasks in tasks/ describe the same '
                  'complete requirements. Preserve all required compatibility and validate the '
                  'combined product against acceptance.py. No further task messages will arrive.')
        (root / (role + '.txt')).write_text(prompt)
        profile = root / 'native' / role
        profile.mkdir(parents=True)
        (profile / 'config.toml').write_text('service_tier = "default"\n'
            f'[projects.{json.dumps(str(work))}]\ntrust_level = "trusted"\n')
    (work / 'AGENTS.md').write_text(COMMON)
    pi_manifest = None
    if condition == 'C':
        frozen = root / 'pi-source'
        copy_pi(source, frozen)
        pi_manifest = manifest(frozen, ignore_cache=True)
        context = work / '.pi'
        context.mkdir()
        # Boundaries are copied from a public fixture architecture file, not
        # invented treatment-only clues. Every ordinary worker can read it too.
        boundaries = json.loads((work / 'architecture.json').read_text())['boundaries']
        objective = (work / 'OBJECTIVE.md').read_text()
        records = []
        for role in ROLES:
            task = (work / 'tasks' / (role + '.txt')).read_text()
            records.append(dict(kind='workstream', id=role.upper(), revision='1', state='active',
                statement=role + ' component migration', scope=task, acceptance=[objective],
                boundaries=boundaries[role], readiness={}, source_checkout=str(work)))
        write_json(context / 'snapshot.json', dict(version=1, scope_id=SCOPE,
            source=dict(provider='snapshot', authoritative=False, captured_at=utc(), mode='offline_snapshot'),
            mission='Implement OBJECTIVE.md across the four component tasks.', records=records))
        write_json(context / 'worker.json', {'scopes': {SCOPE: {
            'snapshot': str(context / 'snapshot.json'), 'enrollment_directory': str(context / 'presence'),
            'report_directory': str(context / 'reports')}}})
        prefix = shlex.join(['/usr/bin/python3', '-B', '-I', str(frozen / 'project_intent/_worker_cli.py'),
                            '--worker-config', str(context / 'worker.json'), '--scope', SCOPE])
        (work / 'AGENTS.md').write_text(COMMON + '\n# Project Intent\n\n'
            'This project uses the frozen local PI worker workflow, not production providers.\n'
            f'Configured CLI prefix: `{prefix}`.\n'
            f'Read `{frozen / "skills/project-intent/SKILL.md"}` and the relevant worker guidance.\n'
            'Use your own CODEX_THREAD_ID with --session for local presence.\n\n'
            + (frozen / 'skills/project-intent/assets/worker-instructions.md').read_text())
    (work / '.gitignore').write_text('__pycache__/\n*.pyc\n.pi/presence/\n.pi/reports/\n')
    subprocess.run(['git', 'init', '-q', str(work)], check=True)
    subprocess.run(['git', '-C', str(work), 'add', '.'], check=True)
    subprocess.run(['git', '-C', str(work), '-c', 'user.name=Fixture', '-c',
                    'user.email=fixture@example.invalid', 'commit', '-qm', 'Frozen distributed fixture'], check=True)
    shutil.copytree(work, root / 'before', ignore=shutil.ignore_patterns('.git'))
    write_json(root / 'before.json', manifest(work, ignore_cache=True))
    inputs = [r + '.txt' for r in roles] + ['check_contract.py']
    write_json(root / 'plan.json', dict(version=VERSION, condition=condition, roles=roles,
        model=MODEL, effort=EFFORT, timeout_seconds=timeout, created_at=utc(),
        setup_seconds=time.monotonic() - started, pi_enabled=condition == 'C', pi_commit=PI_COMMIT,
        before_sha256=sha(root / 'before.json'),
        pi_manifest=pi_manifest, input_hashes={n: sha(root / n) for n in inputs},
        fixture_manifest=manifest(fixture, ignore_cache=True),
        own_recorder_sha256=sha(__file__),
        recorder_hashes={Path(m.__file__).name: sha(m.__file__) for m in (common, common.original, native, analysis)},
        profile_hashes={r: sha(root / 'native' / r / 'config.toml') for r in roles}))
    return root


def verify(root, before=False):
    plan = json.loads((root / 'plan.json').read_text())
    assert (plan['version'], plan['model'], plan['effort']) == (VERSION, MODEL, EFFORT)
    assert plan['own_recorder_sha256'] == sha(__file__)
    assert plan['before_sha256'] == sha(root / 'before.json'), 'Prepared baseline changed'
    for module in (common, common.original, native, analysis):
        assert plan['recorder_hashes'][Path(module.__file__).name] == sha(module.__file__)
    for name, digest in plan['input_hashes'].items():
        assert sha(root / name) == digest
    if plan['pi_enabled']:
        assert manifest(root / 'pi-source', ignore_cache=True) == plan['pi_manifest']
    else:
        assert not (root / 'pi-source').exists()
    if before:
        assert manifest(root / 'work', ignore_cache=True) == json.loads((root / 'before.json').read_text())
        for role, digest in plan['profile_hashes'].items():
            profile = root / 'native' / role
            assert list(profile.iterdir()) == [profile / 'config.toml'], 'Native profile is not fresh'
            assert not (profile / 'config.toml').is_symlink(), 'Native profile contains a link'
            assert sha(profile / 'config.toml') == digest
    return plan


def preflight(root, binary):
    plan = verify(root, before=True)
    # Native --version itself creates arg0 helpers. Probe in a disposable profile,
    # never in a model worker's strictly fresh profile.
    (root / 'native/preflight-version').mkdir(exist_ok=True)
    version = subprocess.run(native.sandbox(root, 'preflight-version', [binary, '--version']),
                             capture_output=True, text=True, timeout=30)
    if version.returncode:
        raise RuntimeError('Native executable preflight failed: ' + version.stderr)
    for role in plan['roles']:
        code = ('import pathlib, subprocess, socket; '
            f'assert not pathlib.Path({str(root / "plan.json")!r}).exists(); '
            f'assert not pathlib.Path({str(Path.home() / "sayhi/state")!r}).exists(); '
            'assert not list((pathlib.Path.home()/".codex/sessions").glob("**/*.jsonl")); '
            'assert socket.getaddrinfo("chatgpt.com",443); '
            'subprocess.run(["git","status","--porcelain"],check=True); '
            f'assert pathlib.Path({binary!r}).is_file(); '
            'p=pathlib.Path(".write-probe");p.write_text("probe");p.unlink()')
        result = subprocess.run(native.sandbox(root, role, ['/usr/bin/python3', '-B', '-c', code]),
                                capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise RuntimeError('Isolation preflight failed: ' + result.stderr)
    verify(root, before=True)


def score(source, checker):
    """Post-exit only; candidate code runs in an isolated disposable mount."""
    with tempfile.TemporaryDirectory(prefix='distributed-score-') as temporary:
        root = Path(temporary) / 'trial'
        shutil.copytree(source, root / 'work', symlinks=True,
                        ignore=shutil.ignore_patterns('.git', '.pi', '__pycache__', '*.pyc'))
        if any('link' in item for item in manifest(root / 'work').values()):
            return {'accepted': False, 'evaluation_error': 'Candidate contains symbolic links'}
        # Use observer's frozen checker, never a worker-modified checker.
        shutil.copy2(checker, root / 'work/acceptance.py')
        (root / 'native/evaluator').mkdir(parents=True)
        command = native.sandbox(root, 'evaluator', ['/usr/bin/python3', '-B', '-I',
                                                    str(root / 'work/acceptance.py'), str(root / 'work')])
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=30)
            if result.returncode:
                return {'accepted': False, 'evaluation_error': result.stderr, 'checker_exit': result.returncode}
            value = json.loads(result.stdout)
            if not isinstance(value.get('accepted'), bool):
                raise ValueError('Checker lacks a boolean acceptance result')
            return value
        except (ValueError, subprocess.TimeoutExpired) as exc:
            return {'accepted': False, 'evaluation_error': str(exc)}


def retain_native(root, role):
    stream = analysis.jsonl(root / role / 'stdout.jsonl')
    sessions = [r['thread_id'] for r in stream if r.get('type') == 'thread.started']
    if len(sessions) != 1 or not re.fullmatch(r'[0-9a-f-]{36}', sessions[0]):
        return None
    paths = list((root / 'native' / role / 'sessions').glob('**/*' + sessions[0] + '.jsonl'))
    if len(paths) != 1:
        return None
    target = root / ('native-' + role + '.jsonl')
    shutil.copy2(paths[0], target)
    return target


def run(root, binary):
    plan = verify(root, before=True)
    with (root / 'started.json').open('x') as stream:
        json.dump({'at': utc(), 'plan_sha256': sha(root / 'plan.json')}, stream)
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
            futures = [pool.submit(native.record, root, role, binary, plan, observer) for role in plan['roles']]
            workers = [f.result() for f in futures]
    finally:
        stop.set()
        monitor.join(timeout=30)
        observer.capture('final')
        observer.close()
    window = common.concurrency(workers)
    archive_start = time.monotonic_ns()
    shutil.copytree(root / 'work', root / 'after', symlinks=True, ignore=shutil.ignore_patterns('.git'))
    telemetry = []
    for worker in workers:
        retain_native(root, worker['role'])
        telemetry.append(analysis.worker(root, worker, window))
    write_json(root / 'worker-analysis.json', telemetry)
    verify(root)
    verification_start = time.monotonic_ns()
    result = score(root / 'after', root / 'check_contract.py')
    end = time.monotonic_ns()
    initial = json.loads((root / 'before.json').read_text())
    final = manifest(root / 'after', ignore_cache=True)
    protected = ['acceptance.py', 'OBJECTIVE.md', 'architecture.json'] + [n for n in initial if n.startswith('tasks/')]
    altered = [n for n in protected if final.get(n) != initial.get(n)]
    correct_identity = all(t['native_contexts'] == [(MODEL, EFFORT)] for t in telemetry)
    # Product correctness is not equivalent to successful native process exit.
    # A timeout with correct final source is retained as correct-but-incomplete.
    accepted_source = bool(result.get('accepted')) and not altered
    completed = correct_identity and all(w.get('exit_code') == 0 and not w.get('timed_out')
                                        and w.get('stream_complete') for w in workers)
    value = dict(condition=plan['condition'], workers=workers, concurrency=window, result=result,
        accepted=accepted_source, autonomous_complete=accepted_source and completed,
        native_identity_verified=correct_identity, protected_inputs_changed=altered,
        setup_seconds=plan['setup_seconds'], archive_seconds=(verification_start - archive_start) / 1e9,
        verification_seconds=(end - verification_start) / 1e9,
        project_seconds=(end - window['start_ns']) / 1e9,
        external_repair_seconds=0, human_interventions=0,
        first_accepted_seconds=None,
        timing_note='Final verification after native exit; first accepted sampled state requires post-run replay. '
                    'In-session repairs remain in execution; no evaluator repair phase.')
    write_json(root / 'result.json', value)
    return value


def replay(root):
    """Measure sampled first/durable accepted source without live worker feedback."""
    verify(root)
    data = json.loads((root / 'result.json').read_text())
    origin = data['concurrency']['start_ns']
    observations = analysis.jsonl(root / 'source-history.jsonl')
    initial = json.loads((root / 'before.json').read_text())
    protected = ['acceptance.py', 'OBJECTIVE.md', 'architecture.json'] + [n for n in initial if n.startswith('tasks/')]
    results = []
    previous_signature = None
    previous_result = None
    # Include every executable/source/document byte, not just final patch events.
    with tempfile.TemporaryDirectory(prefix='distributed-replay-') as directory:
        parent = Path(directory)
        for index, row in enumerate(observations):
            signature = row['files']
            if signature == previous_signature:
                outcome = previous_result
            else:
                source = parent / str(index)
                source.mkdir()
                for name, digest in signature.items():
                    relative = Path(name)
                    if relative.is_absolute() or '..' in relative.parts:
                        raise ValueError('Unsafe sampled path')
                    target = source / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    assert sha(root / 'objects' / digest) == digest, 'Sampled object digest mismatch'
                    shutil.copy2(root / 'objects' / digest, target)
                outcome = score(source, root / 'check_contract.py')
            protected_ok = all(signature.get(name) == initial.get(name, {}).get('sha256') for name in protected)
            results.append(dict(seconds=max(0, (row['mono_ns'] - origin) / 1e9),
                accepted=bool(outcome.get('accepted')) and protected_ok and not row.get('errors'),
                failed_contracts=outcome.get('failed_contracts'), evaluation_error=outcome.get('evaluation_error')))
            previous_signature, previous_result = signature, outcome
    first = next((r['seconds'] for r in results if r['accepted']), None)
    last_bad = max((i for i, r in enumerate(results) if not r['accepted']), default=-1)
    durable = results[last_bad + 1]['seconds'] if last_bad + 1 < len(results) else None
    reconciled = not results or results[-1]['accepted'] == data['accepted']
    if not reconciled:
        durable = None
    value = dict(first_accepted_sample_seconds=first, durable_accepted_sample_seconds=durable,
                 final_sample_matches_final_score=reconciled, sampled_states=results,
                 limitation='100ms non-atomic source observations, replayed after all exits.')
    write_json(root / 'replay.json', value)
    return value


@contextmanager
def study_lock(study):
    with (study / 'execution.lock').open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def initialize(study, protocol_batch, binary='/home/meanaverage/.npm-global/bin/codex'):
    """Bind the software budget to the completed, unchanged protocol gate."""
    frozen = json.loads((protocol_batch / 'freeze.json').read_text())
    assert sha(binary) == frozen['codex_entry_sha256'], 'Native executable changed since protocol calibration'
    assert subprocess.check_output([binary, '--version'], text=True).strip() == frozen['codex_version']
    assert len(frozen['trials']) == 9
    passed, failures, evidence = Counter(), Counter(), []
    expected_pi = None
    first_source = None
    for trial in frozen['trials']:
        root = Path(trial['root'])
        plan = json.loads((root / 'plan.json').read_text())
        assert sha(root / 'plan.json') == trial['plan_sha256']
        assert (plan['model'], plan['effort'], plan['pi_commit']) == (MODEL, EFFORT, PI_COMMIT)
        review_path = protocol_batch / (trial['label'] + '-review.json')
        review = json.loads(review_path.read_text())
        for key, name in (('result_sha256', 'result.json'), ('native_sha256', 'native-worker.jsonl'),
                          ('source_history_sha256', 'source-history.jsonl')):
            assert review[key] == sha(root / name)
        assert not review['safety_violation'] and not review['infrastructure_failure']
        assert review['passed'] == (not review['failed_endpoints'])
        passed[plan['scenario']] += int(review['passed'])
        failures.update(review['failed_endpoints'])
        actual = manifest(root / 'pi-source', ignore_cache=True)
        assert actual == plan['pi_manifest']
        if expected_pi is None:
            expected_pi, first_source = actual, root / 'pi-source'
        assert actual == expected_pi
        evidence.append(dict(label=trial['label'], review_sha256=sha(review_path),
                             result_sha256=review['result_sha256'], passed=review['passed']))
    assert sum(passed.values()) >= 8 and all(passed[f] >= 2 for f in ('audit', 'repair-owner', 'repair-peer'))
    assert not failures or max(failures.values()) < 2
    study.mkdir(parents=True, exist_ok=False)
    copy_pi(first_source, study / 'pi-source')
    assert manifest(study / 'pi-source', ignore_cache=True) == expected_pi
    write_json(study / 'study.json', dict(version=VERSION, created_at=utc(),
        protocol_freeze_sha256=sha(protocol_batch / 'freeze.json'), qualification=evidence,
        codex_version=frozen['codex_version'], codex_entry_sha256=frozen['codex_entry_sha256'],
        pi_manifest=expected_pi, batches=[], candidates=[], ceiling=None, evaluation=None,
        recorder_manifest=None))


def reviewed_project(batch, trial):
    root = Path(trial['root'])
    if not (root / 'result.json').exists():
        raise RuntimeError('Project incomplete: ' + trial['label'])
    review_path = batch / (trial['label'] + '-review.json')
    if not review_path.exists():
        raise RuntimeError('Review completed project before next launch: ' + trial['label'])
    review = json.loads(review_path.read_text())
    assert review['result_sha256'] == sha(root / 'result.json')
    assert review['history_sha256'] == sha(root / 'source-history.jsonl')
    assert review['analysis_sha256'] == sha(root / 'worker-analysis.json')
    plan = json.loads((root / 'plan.json').read_text())
    assert review['native_sha256'] == {role: sha(root / ('native-' + role + '.jsonl'))
        if (root / ('native-' + role + '.jsonl')).exists() else None for role in plan['roles']}
    assert isinstance(review['infrastructure_failure'], bool)
    assert isinstance(review['integrity_failure'], bool) and review['rationale'].strip()
    if review['infrastructure_failure'] or review['integrity_failure']:
        raise RuntimeError('Reviewed infrastructure/integrity failure; batch stopped')
    result = json.loads((root / 'result.json').read_text())
    assert result['native_identity_verified'], 'Model identity not verified'
    return result


def reviewed_batch(record):
    batch = Path(record['path'])
    assert sha(batch / 'freeze.json') == record['freeze_sha256']
    frozen = json.loads((batch / 'freeze.json').read_text())
    return [reviewed_project(batch, trial) for trial in frozen['trials']]


def freeze(batch, source, fixture, conditions, stage, binary, study=None):
    if stage not in ('calibration', 'ceiling', 'evaluation'):
        raise ValueError('Invalid stage')
    required = {'calibration': list('BBB'), 'ceiling': list('AA'),
                'evaluation': list('ABCCBABCCBABC')}
    if conditions != required[stage]:
        raise ValueError('Conditions differ from the preregistered bounded stage')
    if study is None:
        raise ValueError('A qualified study registry is required')
    with study_lock(study):
        return freeze_locked(batch, source, fixture, conditions, stage, binary, study)


def freeze_locked(batch, source, fixture, conditions, stage, binary, study):
    registry = json.loads((study / 'study.json').read_text())
    assert registry['version'] == VERSION
    assert sha(binary) == registry['codex_entry_sha256'], 'Native executable changed within study'
    assert subprocess.check_output([binary, '--version'], text=True).strip() == registry['codex_version']
    assert manifest(study / 'pi-source', ignore_cache=True) == registry['pi_manifest']
    fixture_manifest = manifest(fixture, ignore_cache=True)
    checker_hash = sha(fixture / 'acceptance.py')
    if stage == 'calibration':
        if len(registry['candidates']) >= 2 or registry['ceiling'] or registry['evaluation']:
            raise RuntimeError('Bounded calibration budget exhausted or candidate already selected')
        if registry['candidates']:
            prior = reviewed_batch(registry['candidates'][-1])
            if 0 < sum(r['accepted'] for r in prior) < 3:
                raise RuntimeError('Unsaturated candidate already exists; do not silently tune another')
    else:
        if not registry['candidates']:
            raise RuntimeError('Ordinary calibration required before ceiling/evaluation')
        selected = registry['candidates'][-1]
        assert selected['fixture_manifest'] == fixture_manifest and selected['checker_sha256'] == checker_hash
        prior = reviewed_batch(selected)
        if not 0 < sum(r['accepted'] for r in prior) < 3:
            raise RuntimeError('No unsaturated calibrated candidate; stop rather than weaken the model')
        if stage == 'ceiling' and (registry['ceiling'] or registry['evaluation']):
            raise RuntimeError('Ceiling budget already allocated')
        if stage == 'evaluation':
            if registry['evaluation'] or not registry['ceiling']:
                raise RuntimeError('Evaluation already allocated or ceiling missing')
            if not any(r['accepted'] for r in reviewed_batch(registry['ceiling'])):
                raise RuntimeError('Single-worker ceiling failed consistently')
    assert subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip() == PI_COMMIT
    batch.mkdir(parents=True, exist_ok=False)
    code = batch / 'code'
    (code / 'experiments').mkdir(parents=True)
    for module in (common, common.original, native, analysis):
        shutil.copy2(module.__file__, code / 'experiments' / Path(module.__file__).name)
    for name in ('__init__.py', 'distributed_study.py', 'distributed_check.py'):
        shutil.copy2(source / 'experiments' / name, code / 'experiments' / name)
    recorder_manifest = {k: v for k, v in manifest(code, ignore_cache=True).items()
                         if k != 'experiments/distributed_check.py'}
    if registry['recorder_manifest'] is not None:
        assert recorder_manifest == registry['recorder_manifest'], 'Recorder changed between software batches'
    shutil.copytree(fixture, batch / 'fixture', ignore=IGNORE)
    assert manifest(batch / 'fixture', ignore_cache=True) == fixture_manifest
    copy_pi(study / 'pi-source', batch / 'pi-source')
    assert manifest(batch / 'pi-source', ignore_cache=True) == registry['pi_manifest']
    assert sha(batch / 'fixture/acceptance.py') == checker_hash
    shutil.copy2(source / 'docs/CLI_SOL_DISTRIBUTED_SOFTWARE.md', batch / 'protocol.md')
    (batch / 'tests').mkdir()
    for name in ('test_distributed_study.py', 'test_distributed_fixture.py'):
        shutil.copy2(source / 'tests' / name, batch / 'tests' / name)
    trials = []
    counts = {}
    for condition in conditions:
        counts[condition] = counts.get(condition, 0) + 1
        root = Path(tempfile.mkdtemp(prefix='sol-distributed-')) / 'trial'
        prepare(root, condition, batch / 'pi-source', batch / 'fixture', batch / 'fixture/acceptance.py')
        preflight(root, binary)
        plan = json.loads((root / 'plan.json').read_text())
        assert plan['fixture_manifest'] == fixture_manifest
        assert plan['input_hashes']['check_contract.py'] == checker_hash
        assert plan['pi_manifest'] == (registry['pi_manifest'] if condition == 'C' else None)
        trials.append(dict(label=condition + str(counts[condition]), root=str(root), plan_sha256=sha(root / 'plan.json')))
    write_json(batch / 'freeze.json', dict(version=VERSION, stage=stage, study_root=str(study), at=utc(), model=MODEL, effort=EFFORT,
        pi_commit=PI_COMMIT, code_manifest=manifest(code, ignore_cache=True),
        protocol_sha256=sha(batch / 'protocol.md'), fixture_manifest=manifest(batch / 'fixture', ignore_cache=True),
        tests_manifest=manifest(batch / 'tests', ignore_cache=True),
        codex_version=subprocess.check_output([binary, '--version'], text=True).strip(),
        codex_entry_sha256=sha(binary), trials=trials))
    record = dict(path=str(batch), freeze_sha256=sha(batch / 'freeze.json'),
                  fixture_manifest=fixture_manifest, checker_sha256=checker_hash)
    registry['batches'].append(record)
    if stage == 'calibration':
        registry['candidates'].append(record)
    else:
        registry[stage] = record
    registry['recorder_manifest'] = recorder_manifest
    write_json(study / 'study.json', registry)


def run_next(batch, binary):
    frozen = json.loads((batch / 'freeze.json').read_text())
    study = Path(frozen['study_root'])
    with study_lock(study):
        registry = json.loads((study / 'study.json').read_text())
        assert frozen['codex_version'] == registry['codex_version']
        assert frozen['codex_entry_sha256'] == registry['codex_entry_sha256']
        registered = [r for r in registry['batches'] if r['path'] == str(batch)]
        assert len(registered) == 1 and registered[0]['freeze_sha256'] == sha(batch / 'freeze.json')
        return run_next_locked(batch, binary, frozen)


def run_next_locked(batch, binary, frozen):
    assert manifest(batch / 'code', ignore_cache=True) == frozen['code_manifest']
    assert sha(batch / 'protocol.md') == frozen['protocol_sha256']
    assert manifest(batch / 'fixture', ignore_cache=True) == frozen['fixture_manifest']
    assert manifest(batch / 'tests', ignore_cache=True) == frozen['tests_manifest']
    assert sha(binary) == frozen['codex_entry_sha256']
    assert subprocess.check_output([binary, '--version'], text=True).strip() == frozen['codex_version']
    for trial in frozen['trials']:
        root = Path(trial['root'])
        assert sha(root / 'plan.json') == trial['plan_sha256']
        if (root / 'started.json').exists():
            if not (root / 'result.json').exists():
                raise RuntimeError('Started project has no final record; preserve infrastructure interruption')
            reviewed_project(batch, trial)
            continue
        print(json.dumps({'starting': trial['label'], 'stage': frozen['stage']}), flush=True)
        value = run(root, binary)
        replay(root)
        shutil.copytree(root, batch / trial['label'], symlinks=True,
                        ignore=shutil.ignore_patterns('native', '__pycache__', '*.pyc'))
        print(json.dumps({'completed': trial['label'], 'accepted': value['accepted'],
                          'seconds': value['project_seconds'], 'result': value['result']}), flush=True)
        return value
    print(json.dumps({'completed_batch': True}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('initialize', 'freeze', 'run', 'replay'))
    parser.add_argument('--study', type=Path)
    parser.add_argument('--protocol-batch', type=Path)
    parser.add_argument('--batch', type=Path)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--fixture', type=Path)
    parser.add_argument('--conditions', default='BBB')
    parser.add_argument('--stage', choices=('calibration', 'ceiling', 'evaluation'), default='calibration')
    parser.add_argument('--root', type=Path)
    parser.add_argument('--codex', default='/home/meanaverage/.npm-global/bin/codex')
    args = parser.parse_args()
    if args.action == 'initialize':
        initialize(args.study, args.protocol_batch, args.codex)
    elif args.action == 'freeze':
        freeze(args.batch, args.source, args.fixture, list(args.conditions), args.stage, args.codex, args.study)
    elif args.action == 'run':
        run_next(args.batch, args.codex)
    else:
        print(json.dumps(replay(args.root)))
