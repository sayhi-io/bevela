"""Configurable Qwen-only research lane; frozen historical recorders stay intact.

Private module instances supply settings/prompt hooks to the existing recorder.
They do not modify imported historical modules, PI behavior, or the native loop.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import uuid

from experiments import qwen_code_adapter as native
from experiments import qwen_seven_seams as original

VERSION = 'pi-for-qwen/v1'
CONFIDENCE = 'You are very knowledgeable. An expert. Think and respond with confidence.'
DEFAULT = {'thinking': True, 'confidence': True, 'pi': True, 'runs': 1,
           'effort': 'medium', 'context': 230000}


def validate(profile):
    if set(profile) != set(DEFAULT):
        raise ValueError('Unknown or missing profile controls')
    if any(type(profile[key]) is not bool for key in ('thinking', 'confidence', 'pi')):
        raise ValueError('Feature switches must be booleans')
    if profile['effort'] != 'medium':
        raise ValueError('Only Medium is supported; High/XHigh excluded')
    if type(profile['runs']) is not int or not 1 <= profile['runs'] <= 5:
        raise ValueError('Choose 1 to 5 explicitly bounded projects')
    if type(profile['context']) is not int or not 32768 <= profile['context'] <= 230000:
        raise ValueError('Context must be 32768..230000')
    if profile['confidence'] and not profile['thinking']:
        raise ValueError('Confidence phrase is a thinking-on intervention')
    return dict(profile)


def settings(profile, model, endpoint, context=230000, effort='medium'):
    profile = validate(profile)
    result = native.settings(model, endpoint, profile['context'], profile['effort'])
    result['model']['reasoningEffort'] = 'medium' if profile['thinking'] else 'none'
    result['modelProviders']['openai'][0]['generationConfig']['extra_body'][
        'chat_template_kwargs']['enable_thinking'] = profile['thinking']
    return result


def private_module(module):
    spec = importlib.util.spec_from_file_location('_qwen_profile_' + uuid.uuid4().hex, module.__file__)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def runner(profile):
    profile = validate(profile)
    engine, adapter = private_module(original), private_module(native)
    adapter.settings = lambda *args, **kwargs: settings(profile, *args, **kwargs)
    engine.adapter = adapter
    engine.VERSION = VERSION
    engine.ORDER = tuple(('C' if profile['pi'] else 'B') + str(n + 1) for n in range(profile['runs']))
    engine.MODULES = (*engine.MODULES, original, sys.modules[__name__])
    prepare_base, verify_base, telemetry_base, run_base = engine.prepare, engine.verify, engine.telemetry, engine.run

    def prepare(*args, **kwargs):
        root = prepare_base(*args, **kwargs)
        plan = json.loads((root / 'plan.json').read_text())
        if plan['pi_enabled'] != profile['pi']:
            raise ValueError('Condition disagrees with profile')
        if profile['confidence']:
            for role in engine.ROLES:
                path = root / (role + '.txt')
                path.write_text(path.read_text().rstrip() + '\n\n' + CONFIDENCE + '\n')
                plan['input_hashes'][path.name] = engine.sha(path)
        plan.update(qwen_profile=profile, context_window=profile['context'],
                    profile_route_sha256=engine.sha(__file__))
        engine.write_json(root / 'plan.json', plan)
        return root

    def verify(root, before=False):
        root = Path(root)
        plan = verify_base(root, before)
        if (plan.get('qwen_profile') != profile or plan.get('profile_route_sha256') != engine.sha(__file__)
                or plan['pi_enabled'] != profile['pi'] or plan['context_window'] != profile['context']):
            raise ValueError('Frozen Qwen profile changed')
        expected = settings(profile, engine.MODEL, plan['endpoint'])
        if json.loads((root / 'settings-template.json').read_text()) != expected:
            raise ValueError('Effective settings disagree with profile')
        for role in engine.ROLES:
            text = (original.common.original.ASSETS / (role + '.txt')).read_text()
            if profile['confidence']:
                text = text.rstrip() + '\n\n' + CONFIDENCE + '\n'
            if (root / (role + '.txt')).read_text() != text:
                raise ValueError('Unexpected task prompt change')
        return plan

    def telemetry(root, row, plan):
        evidence = telemetry_base(root, row, plan)
        records = [json.loads(line) for line in (root / row['role'] / 'transport.jsonl').read_text().splitlines()]
        requests = [record for record in records if record.get('event') == 'request']
        evidence['controls_verified'] = bool(requests) and all(
            r.get('model') == engine.MODEL and r.get('reasoning_effort') == 'medium'
            and r.get('chat_template_kwargs', {}).get('enable_thinking') is profile['thinking']
            and r.get('max_tokens') == 32768 for r in requests)
        evidence['thinking_disabled_verified'] = None if profile['thinking'] else (
            not evidence['usage']['reasoning_observed'] and not evidence['usage']['reasoning_tokens'])
        if evidence['thinking_disabled_verified'] is False:
            evidence['controls_verified'] = False
        evidence['qwen_profile'] = profile
        return evidence

    def run(root):
        value = run_base(root)
        value['qwen_profile'] = profile
        engine.write_json(Path(root) / 'result.json', value)
        return value

    engine.prepare, engine.verify, engine.telemetry, engine.run = prepare, verify, telemetry, run
    return engine


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'run'))
    parser.add_argument('batch', type=Path)
    parser.add_argument('--thinking', choices=('on', 'off'), default='on')
    parser.add_argument('--confidence', choices=('on', 'off'), default='on')
    parser.add_argument('--pi', choices=('on', 'off'), default='on')
    parser.add_argument('--runs', type=int, default=1)
    parser.add_argument('--context', type=int, default=230000)
    parser.add_argument('--effort', choices=('medium',), default='medium')
    parser.add_argument('--runtime', type=Path)
    parser.add_argument('--endpoint')
    parser.add_argument('--timeout', type=int, default=1800)
    args = parser.parse_args()
    if args.action == 'run' and len(sys.argv) > 3:
        parser.error('run accepts only its batch; settings are frozen, not overridden')
    if args.action == 'freeze':
        profile = validate({'thinking': args.thinking == 'on', 'confidence': args.confidence == 'on',
            'pi': args.pi == 'on', 'runs': args.runs, 'context': args.context, 'effort': args.effort})
        if not args.runtime or not args.endpoint:
            parser.error('freeze requires --runtime and --endpoint')
        engine = runner(profile)
        engine.freeze(args.batch, Path(__file__).resolve().parents[1], args.runtime, args.endpoint, args.timeout)
        print(json.dumps({'frozen': str(args.batch), 'profile': profile, 'sha256': engine.sha(args.batch / 'frozen.json')}))
    else:
        # Run has no override mechanism: the frozen per-project profile wins.
        frozen = json.loads((args.batch / 'frozen.json').read_text())
        profiles = [json.loads((args.batch / entry['root'] / 'plan.json').read_text())['qwen_profile']
                    for entry in frozen['plans'].values()]
        if not profiles or any(p != profiles[0] for p in profiles):
            raise ValueError('Batch mixes profiles')
        runner(profiles[0]).run_all(args.batch)


if __name__ == '__main__':
    main()
