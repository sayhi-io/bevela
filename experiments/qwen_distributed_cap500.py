"""Fresh candidate-2 trial; only treatment change is explicit 500-call native cap."""
import argparse
import json
from pathlib import Path
import sys
from types import SimpleNamespace

from experiments import qwen_distributed_steering as previous

VERSION = 'qwen-distributed-steering/candidate2-cap500-v1'
CAP = 500


def settings(*args, **kwargs):
    value = previous.profiles.settings(*args, **kwargs)
    value['model']['maxToolCallsPerTurn'] = CAP
    return value


def runner():
    # Private module/proxy: historical modules and frozen source bytes stay intact.
    variant = previous.profiles.private_module(previous)
    variant.VERSION = VERSION
    variant.profiles = SimpleNamespace(**{**vars(previous.profiles), 'settings': settings})
    sys.modules[variant.__name__] = variant
    try:
        engine = variant.runner()
    finally:
        del sys.modules[variant.__name__]
    prepare_base, verify_base, run_base = engine.prepare, engine.verify, engine.run

    def prepare(*args, **kwargs):
        root = prepare_base(*args, **kwargs)
        plan = json.loads((root / 'plan.json').read_text())
        plan.update(max_tool_calls_per_turn=CAP, cap_route_sha256=engine.sha(__file__))
        engine.write_json(root / 'plan.json', plan)
        return root

    def verify(root, before=False):
        plan = verify_base(root, before)
        if plan.get('max_tool_calls_per_turn') != CAP or plan.get('cap_route_sha256') != engine.sha(__file__):
            raise ValueError('Frozen cap profile changed')
        return plan

    def run(root):
        value = run_base(root)
        for role in engine.base.ROLES:
            actual = json.loads((root / 'qwen-home' / role / 'settings.json').read_text())
            if actual['model'].get('maxToolCallsPerTurn') != CAP:
                raise ValueError('Native cap mismatch')
        value['max_tool_calls_per_turn'] = CAP
        engine.write_json(root / 'result.json', value)
        return value

    engine.prepare, engine.verify, engine.run = prepare, verify, run
    return engine


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'run'))
    parser.add_argument('root', type=Path)
    parser.add_argument('--runtime', type=Path)
    parser.add_argument('--endpoint')
    args = parser.parse_args()
    root, engine = args.root.resolve(), runner()
    if args.action == 'freeze':
        if not args.runtime or not args.endpoint:
            parser.error('freeze requires runtime and endpoint')
        engine.prepare(root, Path(__file__).resolve().parents[1], args.runtime, args.endpoint)
        engine.preflight(root)
        engine.write_json(root / 'frozen.json', dict(at=engine.utc(), plan_sha256=engine.sha(root / 'plan.json')))
        print(json.dumps({'frozen': str(root), 'workers': 4, 'cap': CAP}), flush=True)
    else:
        if args.runtime or args.endpoint:
            parser.error('run accepts only frozen project')
        if engine.sha(root / 'plan.json') != json.loads((root / 'frozen.json').read_text())['plan_sha256']:
            raise ValueError('Frozen plan changed')
        result = engine.run(root)
        print(json.dumps({key: result[key] for key in ('accepted', 'autonomous_complete', 'project_seconds', 'result')}), flush=True)


if __name__ == '__main__':
    main()
