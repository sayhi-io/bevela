"""Compact Qwen PI route v2: hide legacy presence; preserve frozen v1 inputs."""
import argparse
import json
from pathlib import Path
import sys

from experiments import qwen_compact_pi as compact
from experiments import qwen_worker_cli as worker_cli

VERSION = 'qwen-compact-pi/v2'


def runner(runs=3):
    variant = compact.profiles.private_module(compact)
    variant.PROFILE = {**compact.PROFILE, 'runs': runs}
    sys.modules[variant.__name__] = variant
    try:
        engine = variant.runner()
    finally:
        del sys.modules[variant.__name__]
    engine.VERSION = VERSION
    engine.MODULES = (*engine.MODULES, sys.modules[__name__], worker_cli)
    prepare_base, verify_base, run_base = engine.prepare, engine.verify, engine.run

    def prepare(*args, **kwargs):
        root = prepare_base(*args, **kwargs)
        target = root / 'pi-source/project_intent/_worker_cli.py'
        target.write_bytes(Path(worker_cli.__file__).read_bytes())
        plan = json.loads((root / 'plan.json').read_text())
        plan.update(pi_manifest=engine.manifest(root / 'pi-source', ignore_cache=True),
                    qwen_cli_profile=VERSION, qwen_cli_sha256=engine.sha(target))
        engine.write_json(root / 'plan.json', plan)
        return root

    def verify(root, before=False):
        plan = verify_base(root, before)
        if (plan.get('qwen_cli_profile') != VERSION or
                plan.get('qwen_cli_sha256') != engine.sha(worker_cli.__file__)):
            raise ValueError('Qwen CLI profile changed')
        return plan

    def run(root):
        result = run_base(root)
        result['qwen_cli_profile'] = VERSION
        engine.write_json(Path(root) / 'result.json', result)
        return result

    engine.prepare, engine.verify, engine.run = prepare, verify, run
    return engine


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'run'))
    parser.add_argument('batch', type=Path)
    parser.add_argument('--runtime', type=Path)
    parser.add_argument('--endpoint')
    parser.add_argument('--runs', type=int, choices=range(1, 6), default=3)
    args = parser.parse_args()
    if args.action == 'freeze':
        engine = runner(args.runs)
        if not args.runtime or not args.endpoint:
            parser.error('freeze requires --runtime and --endpoint')
        engine.freeze(args.batch, Path(__file__).resolve().parents[1], args.runtime, args.endpoint)
        print(json.dumps({'frozen': str(args.batch), 'profile': VERSION}))
    else:
        if len(sys.argv) != 3:
            parser.error('run accepts only its frozen batch')
        frozen = json.loads((args.batch / 'frozen.json').read_text())
        runner(len(frozen['order'])).run_all(args.batch)


if __name__ == '__main__':
    main()
