"""Three PI two-worker thinking-off projects with compact startup instructions."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

from experiments import qwen_profiles as profiles

VERSION = 'qwen-compact-pi/v1'
TEMPLATE = Path(__file__).with_suffix('.md')
PROFILE = {**profiles.DEFAULT, 'thinking': False, 'confidence': False, 'pi': True, 'runs': 3}


def instructions(scope):
    return TEMPLATE.read_text().replace('{{SCOPE}}', scope)


def runner():
    engine = profiles.runner(PROFILE)
    engine.VERSION = VERSION
    engine.MODULES = (*engine.MODULES, sys.modules[__name__])
    prepare_base, verify_base, run_base = engine.prepare, engine.verify, engine.run

    def prepare(*args, **kwargs):
        root = prepare_base(*args, **kwargs)
        plan = json.loads((root / 'plan.json').read_text())
        work = root / 'work'
        previous = (work / 'AGENTS.md').read_text()
        (work / 'AGENTS.md').write_text(instructions(engine.common.SCOPE))
        # Preserve generated pre-treatment inputs outside the worker namespace.
        # Recreate only this disposable fixture's Git history, so old instructions
        # cannot reappear via normal Git inspection.
        (work / '.git').rename(root / 'precompact-git')
        subprocess.run(['git', 'init', '-q', str(work)], check=True)
        subprocess.run(['git', '-C', str(work), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(work), '-c', 'user.name=Fixture', '-c',
                        'user.email=fixture@example.invalid', 'commit', '-qm', 'Frozen compact PI fixture'], check=True)
        (root / 'before').rename(root / 'precompact-before')
        shutil.copytree(work, root / 'before', ignore=shutil.ignore_patterns('.git'))
        engine.write_json(root / 'before.json', engine.manifest(work, ignore_cache=True))
        plan.update(before_sha256=engine.sha(root / 'before.json'),
            compact_template_sha256=engine.sha(TEMPLATE), compact_route_sha256=engine.sha(__file__),
            instruction_profile=VERSION, instruction_words=len(instructions(engine.common.SCOPE).split()),
            previous_instruction_words=len(previous.split()),
            instruction_change='Compact AGENTS only; backend, skill, docs, task inventory and role prompts unchanged.')
        engine.write_json(root / 'plan.json', plan)
        return root

    def verify(root, before=False):
        root = Path(root)
        plan = verify_base(root, before)
        if (plan.get('compact_template_sha256') != engine.sha(TEMPLATE)
                or plan.get('compact_route_sha256') != engine.sha(__file__)
                or plan.get('instruction_profile') != VERSION
                or (root / 'before/AGENTS.md').read_text() != instructions(engine.common.SCOPE)):
            raise ValueError('Compact instructions changed')
        return plan

    def run(root):
        result = run_base(root)
        result['instruction_profile'] = VERSION
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
                          'profile': PROFILE, 'instruction_words': len(instructions(engine.common.SCOPE).split())}))
    else:
        if len(sys.argv) != 3:
            parser.error('run accepts only its frozen batch')
        engine.run_all(args.batch)


if __name__ == '__main__':
    main()
