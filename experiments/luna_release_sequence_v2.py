"""One explicit launch of the frozen four-arm v2 sequence; no automatic retries."""
import json
from experiments import luna_release_study_v2 as study
from experiments import luna_release_evaluation_v2 as evaluation


def main():
    study.require_preflight()
    study.require_frozen(study.ORDER[0])
    marker = study.ROOT / 'sequence-start.json'
    # Exclusive marker: interrupted/failed attempts require explicit investigation.
    with marker.open('x') as stream:
        json.dump({'at': study.now(), 'order': study.ORDER,
                   'inputs': study.inputs()}, stream, indent=2)
    current = None
    try:
        for current in study.ORDER:
            study.require_frozen(current)
            print(json.dumps({'arm': current, 'stage': 'starting'}), flush=True)
            study.run_arm(current)
            outcome = study.read_json(study.ROOT/'arms'/current/'arm-outcome.json')
            if outcome['state'] == 'harness-or-transport-failure':
                raise RuntimeError('Model transport or metadata failed; preserve without restart')
            study.require_frozen(current)
            evaluation.gates(study, current)
            study.require_frozen(current)
            reviewed = evaluation.review(study, current)
            if not reviewed['valid_review'] or not reviewed['passed']:
                raise RuntimeError('Independent review unavailable; preserve without restart')
            evaluation.summarize(study)
            print(json.dumps({'arm': current, 'stage': 'reviewed',
                              'accepted': reviewed['accepted']}), flush=True)
        study.write_json(study.ROOT/'sequence-complete.json', {'at': study.now()})
    except BaseException as error:
        study.write_json(study.ROOT/'sequence-stopped.json',
                         {'at': study.now(), 'arm': current,
                          'error': type(error).__name__ + ': ' + str(error)})
        evaluation.summarize(study)
        raise


if __name__ == '__main__':
    main()
