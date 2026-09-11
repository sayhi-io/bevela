"""Ten sequential fresh repeats; no changes to the frozen steering treatment."""
import argparse
import fcntl
import hashlib
import json
from pathlib import Path

from experiments.qwen_steering import runner

VERSION = 'qwen-steering-repeat/v1'
COUNT = 10


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def identity(plan):
    keys = ('fixture_manifest', 'input_hashes', 'runtime_manifest', 'settings_sha256',
            'module_hashes', 'recorder_hashes', 'compact_template_sha256', 'qwen_cli_sha256',
            'qwen_profile', 'model', 'effort', 'server_effort', 'context_window',
            'endpoint', 'timeout_seconds', 'roles', 'steering_enabled', 'steering_version')
    value = {key: plan[key] for key in keys}
    value['pi_manifest'] = {key: entry for key, entry in plan['pi_manifest'].items()
                            if key != 'steering.json'}
    return value


def project(batch):
    frozen = read(batch / 'frozen.json')
    if frozen['order'] != ['C1']:
        raise ValueError('Exactly one PI project per inner batch required')
    root = batch / frozen['plans']['C1']['root']
    if sha(root / 'plan.json') != frozen['plans']['C1']['sha256']:
        raise ValueError('Plan changed')
    return root


def verify_config(root, plan):
    expected = dict(enabled=True, checkout=str(root / 'work'),
                    scope=runner(True, 1).common.SCOPE,
                    sessions={plan['sessions'][role]: role.upper() for role in plan['roles']},
                    baseline={name: value['sha256'] for name, value in plan['fixture_manifest'].items()
                              if Path(name).suffix == '.py' and len(Path(name).parts) == 1})
    if read(root / 'pi-source/steering.json') != expected:
        raise ValueError('Generated steering bindings changed')


def freeze(batch, source, runtime, endpoint, pilot):
    batch.mkdir(parents=True, exist_ok=False)
    reference = read(pilot / 'plan.json')
    if not reference['steering_enabled']:
        raise ValueError('Steering-on pilot required')
    entries, sessions = [], set(reference['sessions'].values())
    for number in range(1, COUNT + 1):
        name = f'T{number:02d}'
        engine = runner(True, 1)
        engine.freeze(batch / name, source, runtime, endpoint, reference['timeout_seconds'])
        root = project(batch / name)
        plan = engine.verify(root, before=True)
        if identity(plan) != identity(reference):
            raise ValueError('Repeat differs from pilot treatment')
        verify_config(root, plan)
        fresh = set(plan['sessions'].values())
        if len(fresh) != 2 or sessions & fresh:
            raise ValueError('Sessions not fresh')
        sessions.update(fresh)
        entries.append(dict(name=name, sha256=sha(batch / name / 'frozen.json')))
        print(json.dumps({'frozen': name}), flush=True)
    engine.write_json(batch / 'cohort.json', dict(version=VERSION, at=engine.utc(),
        source_sha256=sha(__file__), pilot_plan_sha256=sha(pilot / 'plan.json'),
        identity=identity(reference), entries=entries))


def run_all(batch):
    with (batch / '.cohort.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        cohort = read(batch / 'cohort.json')
        if (cohort['version'] != VERSION or cohort['source_sha256'] != sha(__file__)
                or [e['name'] for e in cohort['entries']] != [f'T{i:02d}' for i in range(1, COUNT + 1)]):
            raise ValueError('Cohort changed')
        if (batch / 'started.json').exists():
            raise ValueError('No automatic replay or replacement')
        for entry in cohort['entries']:
            inner = batch / entry['name']
            if sha(inner / 'frozen.json') != entry['sha256'] or (inner / 'started.json').exists():
                raise ValueError('Inner batch changed or started')
            root = project(inner)
            plan = runner(True, 1).verify(root, before=True)
            if identity(plan) != cohort['identity']:
                raise ValueError('Treatment changed')
            verify_config(root, plan)
        engine = runner(True, 1)
        with (batch / 'started.json').open('x') as stream:
            json.dump(dict(at=engine.utc(), cohort_sha256=sha(batch / 'cohort.json')), stream)
        for entry in cohort['entries']:
            print(json.dumps({'repeat': entry['name'], 'at': engine.utc()}), flush=True)
            runner(True, 1).run_all(batch / entry['name'])
        engine.write_json(batch / 'completed.json', dict(at=engine.utc(), projects=COUNT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'run'))
    parser.add_argument('batch', type=Path)
    parser.add_argument('--runtime', type=Path)
    parser.add_argument('--endpoint')
    parser.add_argument('--pilot', type=Path)
    args = parser.parse_args()
    if args.action == 'freeze':
        if not all((args.runtime, args.endpoint, args.pilot)):
            parser.error('freeze requires runtime, endpoint and pilot project')
        freeze(args.batch.resolve(), Path(__file__).resolve().parents[1], args.runtime, args.endpoint, args.pilot)
    else:
        if any((args.runtime, args.endpoint, args.pilot)):
            parser.error('run accepts only frozen cohort')
        run_all(args.batch.resolve())


if __name__ == '__main__':
    main()
