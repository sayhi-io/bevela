"""Export completed ten-repeat evidence, excluding raw model conversations."""
import argparse
import json
from pathlib import Path
import statistics

from experiments import qwen_steering_repeat as study


def export(batch):
    if study.read(batch / 'completed.json')['projects'] != 10:
        raise ValueError('Ten completed trials required')
    cohort = study.read(batch / 'cohort.json')
    rows = []
    for entry in cohort['entries']:
        inner = batch / entry['name']
        root = study.project(inner)
        result = study.read(root / 'result.json')
        plan = study.read(root / 'plan.json')
        value = {key: data for key, data in result.items() if key != 'telemetry'}
        value['trial'] = entry['name']
        value['telemetry'] = [{key: item.get(key) for key in ('role', 'usage',
            'controls_verified', 'thinking_disabled_verified', 'initialization_verified',
            'final_identity_verified', 'native_success')} for item in result['telemetry']]
        value['hook_events'] = {role: [json.loads(line) for line in
            (root / 'qwen-home' / role / 'pi-steering/events.jsonl').read_text().splitlines()]
            for role in plan['roles']}
        value['native_loop_guard'] = {role: any('Loop detected' in line or
            'loop detected' in line.lower() for line in (root / role / 'events.jsonl').read_text().splitlines())
            for role in plan['roles']}
        value['provenance'] = dict(project=str(root.relative_to(batch)),
            plan_sha256=study.sha(root / 'plan.json'), result_sha256=study.sha(root / 'result.json'),
            frozen_sha256=entry['sha256'])
        rows.append(value)
    return dict(schema='qwen-steering-repeat-public/v1', cohort=cohort,
        cohort_sha256=study.sha(batch / 'cohort.json'), batch=batch.name,
        completed=study.read(batch / 'completed.json'), backend='v0.05 unchanged',
        qwen_code_version='0.23.2', trials=rows,
        limitations=['Ten steering-on repeats, no new matched off/control runs; not a causal A/B result.',
            'Independent acceptance measured after worker exit, not continuous first-pass timing.',
            'Hook emission is not proof of model attention. Hook-body seconds overlap across workers.',
            'Input includes repeated cached context; it is not unique-context or PI-only token cost.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('batch', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    value = export(args.batch)
    with args.output.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
    for row in value['trials']:
        print(json.dumps(dict(trial=row['trial'], score=row['result']['score'],
            accepted=row['accepted'], seconds=row['project_seconds'],
            tokens=sum(t['usage']['input_tokens'] + t['usage']['output_tokens'] for t in row['telemetry']),
            notices=sum(s['emitted_notices'] for s in row['steering_observations'].values()),
            failed=[k for k, v in row['result']['problems'].items() if not v['both_preserved']])))
    print(json.dumps(dict(accepted=sum(r['accepted'] for r in value['trials']),
        median_seconds=statistics.median(r['project_seconds'] for r in value['trials']))))


if __name__ == '__main__':
    main()
