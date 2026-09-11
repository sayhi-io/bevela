"""One unchanged candidate-2 project: four Qwen workers, thinking off, PI/steering on."""
import argparse
import contextvars
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

from experiments import qwen_distributed_study as original
from experiments import qwen_profiles as profiles
from experiments import qwen_compact_pi as compact
from experiments import qwen_worker_cli as worker_cli
from experiments import qwen_steering_hook as hook
from experiments import qwen_nested_steering_hook as nested

VERSION = 'qwen-distributed-steering/candidate2-v1'
MODEL = 'qwen38-27b-dflash2'
PROFILE = {**profiles.DEFAULT, 'thinking': False, 'confidence': False, 'pi': True}


def hooks(root):
    command = shlex.join(['/usr/bin/python3', '-B', '-I', str(root / 'pi-source/qwen_nested_steering_hook.py')])
    return {event: [{'hooks': [{'type': 'command', 'command': command, 'timeout': 5000}]}]
            for event in hook.EVENTS}


def bindings(root, plan, scope):
    baseline = {name: entry['sha256'] for name, entry in plan['fixture_manifest'].items()
                if Path(name).parts[0] in plan['roles'] and
                (Path(name).suffix == '.py' or Path(name).name == 'CONTRACT.md')}
    if not 1 <= len(baseline) <= 64:
        raise ValueError('Bounded component source list required')
    return dict(enabled=True, checkout=str(root / 'work'), scope=scope,
                sessions={plan['sessions'][role]: role.upper() for role in plan['roles']}, baseline=baseline)


def runner():
    engine = profiles.private_module(original)
    adapter = profiles.private_module(original.adapter)
    engine.adapter = adapter
    engine.VERSION = VERSION
    active = contextvars.ContextVar('distributed_steering_root', default=None)
    record_base = adapter.record
    def settings(*args, **kwargs):
        value = profiles.settings(PROFILE, *args, **kwargs)
        if active.get() is not None:
            value['hooks'] = hooks(active.get())
        return value
    def record(root, role, plan, observer=None):
        token = active.set(root)
        try:
            return record_base(root, role, plan, observer)
        finally:
            active.reset(token)
    adapter.settings, adapter.record = settings, record
    prepare_base, verify_base, run_base, preflight_base = engine.prepare, engine.verify, engine.run, engine.preflight
    telemetry = profiles.runner(PROFILE).telemetry
    modules = (original, profiles, compact, worker_cli, hook, nested, sys.modules[__name__],
               profiles.original)
    def prepare(root, source, runtime, endpoint):
        root = prepare_base(root, 'C', source, runtime, endpoint, MODEL, 1800)
        plan = json.loads((root / 'plan.json').read_text())
        work = root / 'work'
        # Retain all ordinary execution/acceptance instructions plus compact PI.
        (work / 'AGENTS.md').write_text(engine.base.COMMON + '\n' + compact.instructions(engine.base.SCOPE))
        (work / '.git').rename(root / 'precompact-git')
        subprocess.run(['git', 'init', '-q', str(work)], check=True)
        subprocess.run(['git', '-C', str(work), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(work), '-c', 'user.name=Fixture', '-c',
            'user.email=fixture@example.invalid', 'commit', '-qm', 'Frozen distributed compact PI'], check=True)
        (root / 'before').rename(root / 'precompact-before')
        shutil.copytree(work, root / 'before', ignore=shutil.ignore_patterns('.git'))
        engine.write_json(root / 'before.json', engine.manifest(work, ignore_cache=True))
        (root / 'pi-source/project_intent/_worker_cli.py').write_bytes(Path(worker_cli.__file__).read_bytes())
        for module in (hook, nested):
            shutil.copy2(module.__file__, root / 'pi-source' / Path(module.__file__).name)
        engine.write_json(root / 'pi-source/steering.json', bindings(root, plan, engine.base.SCOPE))
        plan.update(effort='thinking-off', server_effort='medium', qwen_profile=PROFILE,
            before_sha256=engine.sha(root / 'before.json'), steering_enabled=True,
            steering_version='qwen-steering/v1+nested-source-v1', steering_hooks=hooks(root),
            compact_template_sha256=engine.sha(compact.TEMPLATE),
            treatment_hashes={Path(m.__file__).name: engine.sha(m.__file__) for m in modules},
            pi_manifest=engine.manifest(root / 'pi-source', ignore_cache=True),
            limits='One project/four workers; native thinking off; compact PI; bounded nested source hooks. No evaluator feedback, retries or post-exit resume.')
        engine.write_json(root / 'plan.json', plan)
        return root
    def verify(root, before=False):
        plan = verify_base(root, before)
        if (plan['model'] != MODEL or plan['qwen_profile'] != PROFILE or
                plan['server_effort'] != 'medium' or plan['steering_enabled'] is not True or
                plan['steering_hooks'] != hooks(root) or
                plan['compact_template_sha256'] != engine.sha(compact.TEMPLATE) or
                any(plan['treatment_hashes'][Path(m.__file__).name] != engine.sha(m.__file__) for m in modules)):
            raise ValueError('Frozen treatment changed')
        if json.loads((root / 'pi-source/steering.json').read_text()) != bindings(root, plan, engine.base.SCOPE):
            raise ValueError('Steering bindings changed')
        if json.loads((root / 'settings-template.json').read_text()) != settings(MODEL, plan['endpoint']):
            raise ValueError('Settings changed')
        return plan
    def worker_analysis(root, row):
        value = telemetry(root, row, json.loads((root / 'plan.json').read_text()))
        value['native_identity_verified'] = all(value[k] for k in
            ('controls_verified', 'initialization_verified', 'final_identity_verified'))
        return value
    def preflight(root):
        preflight_base(root)
        plan = verify(root, before=True)
        for role in engine.base.ROLES:
            result = subprocess.run(adapter.sandbox(root, role,
                ['/usr/bin/node', str(root / 'runtime/bin/qwen'), '--version'],
                plan['sessions'][role], pi=True), capture_output=True, text=True, timeout=30)
            if result.returncode or result.stdout.strip() != '0.23.2':
                raise ValueError('Expected isolated Qwen Code 0.23.2')
        # Version check may create home state; never hand it to real workers.
        verify(root, before=True)
    def run(root):
        value = run_base(root)
        value['autonomous_complete'] = bool(value['autonomous_complete'] and
            not value['infrastructure_errors'] and all(w.get('relay_complete') for w in value['workers']))
        value.update(qwen_profile=PROFILE, steering_enabled=True, steering_observations={})
        for role in engine.base.ROLES:
            actual = json.loads((root / 'qwen-home' / role / 'settings.json').read_text())
            if actual.get('hooks') != hooks(root):
                raise ValueError('Native hooks missing')
            journal = root / 'qwen-home' / role / 'pi-steering/events.jsonl'
            rows = [json.loads(line) for line in journal.read_text().splitlines()] if journal.exists() else []
            value['steering_observations'][role] = dict(hook_calls=len(rows),
                notices=sum(r['emitted'] for r in rows),
                seconds=sum(r['elapsed_seconds'] for r in rows),
                suppressed=max((r['suppressed'] for r in rows), default=0))
        engine.write_json(root / 'result.json', value)
        return value
    engine.prepare, engine.verify, engine.run, engine.worker_analysis = prepare, verify, run, worker_analysis
    engine.preflight = preflight
    return engine


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=('freeze', 'run'))
    p.add_argument('root', type=Path)
    p.add_argument('--runtime', type=Path)
    p.add_argument('--endpoint')
    args = p.parse_args()
    root = args.root.resolve()
    engine = runner()
    if args.action == 'freeze':
        if not args.runtime or not args.endpoint:
            p.error('freeze requires runtime and endpoint')
        engine.prepare(root, Path(__file__).resolve().parents[1], args.runtime, args.endpoint)
        engine.preflight(root)
        engine.write_json(root / 'frozen.json', dict(at=engine.utc(), plan_sha256=engine.sha(root / 'plan.json')))
        print(json.dumps({'frozen': str(root), 'workers': 4, 'profile': PROFILE}), flush=True)
    else:
        if args.runtime or args.endpoint:
            p.error('run accepts only frozen root')
        if engine.sha(root / 'plan.json') != json.loads((root / 'frozen.json').read_text())['plan_sha256']:
            raise ValueError('Frozen plan changed')
        result = engine.run(root)
        print(json.dumps({key: result[key] for key in ('accepted', 'autonomous_complete', 'project_seconds', 'result')}), flush=True)


if __name__ == '__main__':
    main()
