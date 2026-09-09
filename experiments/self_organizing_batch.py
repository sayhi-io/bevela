"""Freeze and run the prespecified self-organizing batch, one project at a time."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

ORDER = [('A', 1), ('B', 1), ('C', 1), ('C', 2), ('A', 2), ('B', 2),
         ('B', 3), ('C', 3), ('A', 3), ('D', 1), ('D', 2), ('D', 3)]
PI_HEAD = 'e384223962c55bbb7b4742f7cbced7bf1ae72f94'
CODEX = '/home/meanaverage/.npm-global/bin/codex'


def prepare(batch, source, pi):
    batch.mkdir(mode=0o700)
    assert subprocess.check_output(['git', '-C', str(pi), 'rev-parse', 'HEAD'], text=True).strip() == PI_HEAD
    assert not subprocess.check_output(['git', '-C', str(pi), 'status', '--porcelain'], text=True).strip()
    frozen = batch / 'code'
    (frozen / 'experiments').mkdir(parents=True)
    for name in ('__init__.py', 'seven_seams.py', 'seven_seams_check.py', 'concurrency_study.py',
                 'seven_seams_self_organizing.py', 'self_organizing_batch.py'):
        shutil.copy2(source / 'experiments' / name, frozen / 'experiments' / name)
    shutil.copytree(source / 'experiments/seven_seams', frozen / 'experiments/seven_seams',
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copy2(source / 'docs/CLI_SEVEN_SEAMS_SELF_ORGANIZING.md', batch / 'protocol.md')
    shutil.copy2(source / 'tests/test_seven_seams_self_organizing.py', batch / 'test_self_organizing.py')
    sys.path.insert(0, str(frozen))
    # prepare is normally invoked in a fresh process; ensure imports resolve frozen code.
    from experiments import seven_seams_self_organizing as study
    assert Path(study.__file__).resolve().is_relative_to(frozen)
    started = time.monotonic()
    rows = []
    for condition, repetition in ORDER:
        root = study.prepare(condition, pi)
        study.preflight(root, CODEX)
        plan = json.loads((root / 'plan.json').read_text())
        assert plan['fixture_manifest'] == study.manifest(pi / 'experiments/seven_seams/fixture', ignore_cache=True)
        assert study.sha(root / 'check_contract.py') == study.sha(pi / 'experiments/seven_seams_check.py')
        rows.append({'condition': condition, 'repetition': repetition, 'root': str(root),
                     'plan_sha256': study.sha(root / 'plan.json')})
    study.write_json(batch / 'trials.json', rows)
    study.write_json(batch / 'freeze.json', {'at': study.utc(), 'model': 'gpt-5.6-luna', 'effort': 'medium',
        'pi_commit': PI_HEAD, 'projects': 12, 'native_sessions': 24, 'timeout_seconds': 600,
        'setup_all_seconds': time.monotonic() - started,
        'code_manifest': study.manifest(frozen, ignore_cache=True),
        'protocol_sha256': study.sha(batch / 'protocol.md'), 'tests_sha256': study.sha(batch / 'test_self_organizing.py'),
        'trials_sha256': study.sha(batch / 'trials.json'), 'ordering': ORDER,
        'common_prompt_sha256': study.sha(Path(rows[0]['root']) / 'common.txt')})
    print(json.dumps({'prepared_projects': len(rows), 'batch': str(batch)}), flush=True)


def run(batch):
    sys.path.insert(0, str(batch / 'code'))
    from experiments import seven_seams_self_organizing as study
    assert Path(study.__file__).resolve().is_relative_to(batch / 'code')
    freeze = json.loads((batch / 'freeze.json').read_text())
    assert study.manifest(batch / 'code', ignore_cache=True) == freeze['code_manifest']
    assert study.sha(batch / 'protocol.md') == freeze['protocol_sha256']
    assert study.sha(batch / 'test_self_organizing.py') == freeze['tests_sha256']
    assert study.sha(batch / 'trials.json') == freeze['trials_sha256']
    rows = json.loads((batch / 'trials.json').read_text())
    for row in rows:
        root = Path(row['root'])
        assert study.sha(root / 'plan.json') == row['plan_sha256']
        study.verify(root, json.loads((root / 'plan.json').read_text()))
    with (batch / 'batch-started.json').open('x') as stream:
        json.dump({'at': study.utc(), 'freeze_sha256': study.sha(batch / 'freeze.json')}, stream)
    started = time.monotonic()
    completed = []
    for row in rows:
        root = Path(row['root'])
        label = row['condition'] + str(row['repetition'])
        print(json.dumps({'starting': label, 'root': str(root)}), flush=True)
        with (root / 'observer-stdout.json').open('wb') as out, (root / 'observer-stderr.txt').open('wb') as err:
            result = subprocess.run([sys.executable, '-B', '-m', 'experiments.seven_seams_self_organizing',
                'run', '--root', str(root), '--codex', CODEX], cwd=batch / 'code', stdout=out, stderr=err)
        value = json.loads((root / 'results.json').read_text()) if (root / 'results.json').exists() else None
        finished = dict(row, observer_exit=result.returncode, result=value)
        completed.append(finished)
        study.write_json(batch / 'progress.json', completed)
        print(json.dumps({'completed': label, 'observer_exit': result.returncode,
            'score': value['result'].get('score') if value else None,
            'accepted': value['accepted'] if value else None,
            'seconds': value['project_seconds'] if value else None}), flush=True)
        # Archive evidence, never authentication/profile stores. Session JSONL selected by own exact ID.
        target = batch / label
        shutil.copytree(root, target, symlinks=True, ignore=shutil.ignore_patterns('native', '__pycache__', '*.pyc'))
        if value:
            for worker in value['workers']:
                role = worker['role']
                events = [json.loads(line) for line in (root / role / 'stdout.jsonl').read_text().splitlines()]
                ids = [e['thread_id'] for e in events if e.get('type') == 'thread.started']
                if len(ids) == 1:
                    paths = list((root / 'native' / role / 'sessions').glob('**/*-' + ids[0] + '.jsonl'))
                    if len(paths) == 1:
                        shutil.copy2(paths[0], target / ('native-' + role + '.jsonl'))
        if result.returncode:
            raise RuntimeError('Recorder failed; preserved partial batch; inspect live process state before continuation')
    study.write_json(batch / 'results.json', {'trials': completed,
        'batch_seconds': time.monotonic() - started, 'completed_at': study.utc()})
    print(json.dumps({'batch_complete': str(batch / 'results.json')}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'run'))
    parser.add_argument('--batch', type=Path, required=True)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--pi-source', type=Path)
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare(args.batch, args.source, args.pi_source)
    else:
        run(args.batch)
