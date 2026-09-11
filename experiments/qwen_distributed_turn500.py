"""Fresh cap500 trial with session turns raised from 150 to 500; no other changes."""
import json

from experiments import qwen_distributed_cap500 as previous

VERSION = 'qwen-distributed-steering/candidate2-cap500-turn500-v1'
TURNS = 500


def settings(*args, **kwargs):
    value = previous.settings(*args, **kwargs)
    value['model']['maxSessionTurns'] = TURNS
    return value


def variant():
    module = previous.previous.profiles.private_module(previous)
    module.VERSION, module.settings = VERSION, settings
    return module


def runner():
    engine = variant().runner()
    prepare_base, verify_base, run_base = engine.prepare, engine.verify, engine.run

    def prepare(*args, **kwargs):
        root = prepare_base(*args, **kwargs)
        plan = json.loads((root / 'plan.json').read_text())
        plan.update(max_session_turns=TURNS, turn_route_sha256=engine.sha(__file__))
        engine.write_json(root / 'plan.json', plan)
        return root

    def verify(root, before=False):
        plan = verify_base(root, before)
        if plan.get('max_session_turns') != TURNS or plan.get('turn_route_sha256') != engine.sha(__file__):
            raise ValueError('Frozen session-turn profile changed')
        return plan

    def run(root):
        result = run_base(root)
        for role in engine.base.ROLES:
            actual = json.loads((root / 'qwen-home' / role / 'settings.json').read_text())
            if actual['model'].get('maxSessionTurns') != TURNS:
                raise ValueError('Native session-turn setting mismatch')
        result['max_session_turns'] = TURNS
        engine.write_json(root / 'result.json', result)
        return result

    engine.prepare, engine.verify, engine.run = prepare, verify, run
    return engine


if __name__ == '__main__':
    cli = variant()
    cli.runner = runner
    cli.main()
