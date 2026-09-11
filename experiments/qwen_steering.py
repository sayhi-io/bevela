"""Native Qwen steering toggle; independent of the frozen passive studies."""
import argparse
import contextvars
import json
from pathlib import Path
import shlex
import sys

from experiments import qwen_compact_pi_v2 as passive
from experiments import qwen_steering_hook as hook

VERSION = 'qwen-steering/v1'


def hooks(root):
    command = shlex.join(['/usr/bin/python3', '-B', '-I', str(root / 'pi-source/qwen_steering_hook.py')])
    return {event: [{'hooks': [{'type': 'command', 'command': command, 'timeout': 5000}]}]
            for event in hook.EVENTS}


def runner(enabled=False, runs=1):
    if type(enabled) is not bool:
        raise ValueError('Boolean steering toggle required')
    engine = passive.runner(runs)
    engine.VERSION = VERSION
    engine.MODULES = (*engine.MODULES, sys.modules[__name__], hook)
    prepare_base, verify_base, run_base = engine.prepare, engine.verify, engine.run
    record_base, settings_base = engine.adapter.record, engine.adapter.settings
    active = contextvars.ContextVar('steering_checkout', default=None)

    def settings(*args, **kwargs):
        value = settings_base(*args, **kwargs)
        if enabled and active.get() is not None:
            value['hooks'] = hooks(active.get())
        return value

    def record(root, role, plan, observer=None):
        token = active.set(Path(root))
        try:
            return record_base(root, role, plan, observer)
        finally:
            active.reset(token)

    def prepare(*args, **kwargs):
        root = prepare_base(*args, **kwargs)
        plan = json.loads((root / 'plan.json').read_text())
        baseline = {name: value['sha256'] for name, value in plan['fixture_manifest'].items()
                    if Path(name).suffix == '.py' and len(Path(name).parts) == 1}
        if not baseline or len(baseline) > 64:
            raise ValueError('Expected 1–64 bounded source files')
        config = dict(enabled=enabled, checkout=str(root / 'work'), scope=engine.common.SCOPE,
                      sessions={plan['sessions'][role]: role.upper() for role in engine.ROLES}, baseline=baseline)
        if enabled:
            (root / 'pi-source/qwen_steering_hook.py').write_bytes(Path(hook.__file__).read_bytes())
            engine.write_json(root / 'pi-source/steering.json', config)
        plan.update(steering_enabled=enabled, steering_version=VERSION,
                    steering_hooks=hooks(root) if enabled else {},
                    pi_manifest=engine.manifest(root / 'pi-source', ignore_cache=True),
                    limits='Native hooks add bounded context when enabled; no tool denial, stop blocking, evaluator feedback or post-exit resume.')
        engine.write_json(root / 'plan.json', plan)
        return root

    def verify(root, before=False):
        plan = verify_base(root, before)
        if (plan.get('steering_enabled') is not enabled or plan.get('steering_version') != VERSION
                or plan.get('steering_hooks') != (hooks(Path(root)) if enabled else {})):
            raise ValueError('Frozen steering toggle changed')
        return plan

    def run(root):
        result = run_base(root)
        result.update(steering_enabled=enabled, steering_version=VERSION)
        observations = {}
        for role in engine.ROLES:
            journal = Path(root) / 'qwen-home' / role / 'pi-steering/events.jsonl'
            rows = [json.loads(line) for line in journal.read_text().splitlines()] if journal.exists() else []
            observations[role] = {'hook_calls': len(rows), 'emitted_notices': sum(r['emitted'] for r in rows),
                                 'seconds': sum(r['elapsed_seconds'] for r in rows),
                                 'suppressed': max((r['suppressed'] for r in rows), default=0)}
            settings_file = json.loads((Path(root) / 'qwen-home' / role / 'settings.json').read_text())
            if settings_file.get('hooks', {}) != (hooks(Path(root)) if enabled else {}):
                raise ValueError('Native steering settings mismatch')
        result['steering_observations'] = observations
        engine.write_json(Path(root) / 'result.json', result)
        return result

    engine.adapter.settings, engine.adapter.record = settings, record
    engine.prepare, engine.verify, engine.run = prepare, verify, run
    return engine


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=('freeze', 'run'))
    p.add_argument('batch', type=Path)
    p.add_argument('--runtime', type=Path)
    p.add_argument('--endpoint')
    p.add_argument('--runs', type=int, choices=range(1, 6), default=1)
    p.add_argument('--steering', choices=('on', 'off'), default='off')
    args = p.parse_args()
    if args.action == 'freeze':
        if not args.runtime or not args.endpoint:
            p.error('freeze requires --runtime and --endpoint')
        engine = runner(args.steering == 'on', args.runs)
        engine.freeze(args.batch, Path(__file__).resolve().parents[1], args.runtime, args.endpoint)
    else:
        if len(sys.argv) != 3:
            p.error('run accepts only the frozen batch')
        frozen = json.loads((args.batch / 'frozen.json').read_text())
        first = args.batch / frozen['plans'][frozen['order'][0]]['root']
        plan = json.loads((first / 'plan.json').read_text())
        runner(plan['steering_enabled'], len(frozen['order'])).run_all(args.batch)


if __name__ == '__main__':
    main()
