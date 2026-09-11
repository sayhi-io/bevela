"""Three sequential ordinary single-worker projects; original combined task."""
import argparse
import json
from pathlib import Path
import sys
import uuid

from experiments import qwen_profiles as profiles
from experiments import qwen_seven_seams as original

VERSION = 'qwen-single-worker/v1'
PROFILE = {**profiles.DEFAULT, 'thinking': False, 'confidence': False, 'pi': False, 'runs': 3}


def runner():
    builder = profiles.runner(PROFILE)
    engine = profiles.private_module(original)
    engine.VERSION, engine.ORDER, engine.ROLES = VERSION, ('A1', 'A2', 'A3'), ('solo',)
    engine.adapter, engine.telemetry = builder.adapter, builder.telemetry
    engine.MODULES = (*original.MODULES, profiles, sys.modules[__name__])
    verify_base, run_base = engine.verify, engine.run

    def prepare(parent, condition, source, runtime, endpoint, timeout=1800):
        if condition != 'A':
            raise ValueError('Single-worker ordinary condition A only')
        root = builder.prepare(parent, 'B', source, runtime, endpoint, timeout)
        # The upstream recorder already creates the complete solo prompt, outside
        # the checkout. Reuse it verbatim; add no solutions, hints or task order.
        (root / 'qwen-home/solo').mkdir()
        plan = json.loads((root / 'plan.json').read_text())
        plan.update(version=VERSION, condition='A', roles=['solo'],
            sessions={'solo': str(uuid.uuid4())},
            module_hashes={Path(m.__file__).name: engine.sha(m.__file__) for m in engine.MODULES},
            single_route_sha256=engine.sha(__file__), worker_count=1,
            information='Complete original producer and consumer prompts in one session; no PI.',
            limits='One native Qwen worker per project, three sequential fresh projects; '
                   'unchanged isolated recorder, observer-only checker and 1800s default deadline.')
        engine.write_json(root / 'plan.json', plan)
        return root

    def verify(root, before=False):
        root = Path(root)
        plan = verify_base(root, before)
        expected_prompt = 'Complete both tasks below in this session.\n\n' + '\n'.join(
            (original.common.original.ASSETS / (role + '.txt')).read_text() for role in original.ROLES)
        if (plan['condition'] != 'A' or plan['pi_enabled'] or plan.get('worker_count') != 1
                or set(plan['sessions']) != {'solo'} or plan['qwen_profile'] != PROFILE
                or plan['single_route_sha256'] != engine.sha(__file__)
                or (root / 'solo.txt').read_text() != expected_prompt
                or json.loads((root / 'settings-template.json').read_text()) !=
                   profiles.settings(PROFILE, engine.MODEL, plan['endpoint'])):
            raise ValueError('Single-worker controls changed')
        return plan

    def run(root):
        result = run_base(root)
        result.update(qwen_profile=PROFILE, worker_count=1)
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
    args = parser.parse_args()
    engine = runner()
    if args.action == 'freeze':
        if not args.runtime or not args.endpoint:
            parser.error('freeze requires --runtime and --endpoint')
        engine.freeze(args.batch, Path(__file__).resolve().parents[1], args.runtime, args.endpoint)
        print(json.dumps({'frozen': str(args.batch), 'order': engine.ORDER,
                          'worker_count': 1, 'profile': PROFILE}))
    else:
        if len(sys.argv) != 3:
            parser.error('run accepts only the frozen batch')
        engine.run_all(args.batch)


if __name__ == '__main__':
    main()
