"""Read-only, allowlisted publication of completed seven-seam measurements.

Prints a curated JSON summary; never launches workers or changes frozen evidence.
Raw streams, conversations, credentials, host paths and session IDs are not exports.
Older studies with different schemas are documented separately, not silently pooled.
"""
import argparse
import hashlib
import json
from pathlib import Path


BATCHES = (
    '20260909-seven-seams-luna-spark-v1',
    '20260909-seven-seams-luna-spark-v2',
    '20260909-seven-seams-spark-xhigh-v1',
    '20260909-seven-seams-luna-low-v1',
    '20260909-seven-seams-luna-low-control-v1',
    '20260909-seven-seams-sol-low-control-v1',
    '20260909-seven-seams-sol-medium-high-control-v1',
    '20260909-torture-refunds-luna-high-control-v1',
    '20260909-torture-refunds-luna-medium-control-v1',
    '20260909-torture-refunds-luna-medium-pi-v1',
    '20260909-seven-seams-concurrency-luna-medium-v2',
    '20260909-seven-seams-self-organizing-luna-medium-v4',
)
TOKEN_KEYS = ('input_tokens', 'cached_input_tokens', 'output_tokens',
              'reasoning_output_tokens', 'total_tokens')


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint(manifest, prefix):
    subset = {k: v['sha256'] for k, v in manifest.items()
              if k.startswith(prefix) and 'sha256' in v
              and (k.endswith('.py') if prefix == 'project_intent/' else True)}
    return hashlib.sha256(json.dumps(subset, sort_keys=True).encode()).hexdigest() if subset else None


def tokens(source):
    return {k: source.get(k) for k in TOKEN_KEYS} if source else None


def project(row, plan, analysis=None):
    outer = row['result']
    scored = outer.get('result', outer)
    process = outer.get('process_results', outer)
    workers = process['workers']
    start = min(w['start_monotonic_ns'] for w in workers)
    end = max(w['end_monotonic_ns'] for w in workers)
    interval = (end - start) / 1e9
    worker_seconds = sum(w['elapsed_seconds'] for w in workers)
    problems = scored['problems']
    migrated = 'producer' in next(iter(problems.values()))
    passed = lambda p: p['both_preserved'] if migrated else p['passed']
    manifest = plan.get('pi_manifest', plan.get('pi_source_manifest', {})) or {}
    analyzed = {w['role']: w for w in (analysis or {}).get('workers', [])}
    timings = []
    for worker in workers:
        a = analyzed.get(worker['role'], {})
        timings.append({
            'role': worker['role'],
            'start_seconds': (worker['start_monotonic_ns'] - start) / 1e9,
            'end_seconds': (worker['end_monotonic_ns'] - start) / 1e9,
            'duration_seconds': worker['elapsed_seconds'],
            'exit_code': worker['exit_code'],
            'tokens': tokens(a.get('tokens')),
            'tool_calls': a.get('native_tool_call_count'),
            'enrollment_completed_seconds': a.get('enrollment_completed_seconds'),
            'pi_tagged_tool_seconds': a.get('pi_native_tool_seconds'),
            'pi_tagged_output_bytes': a.get('pi_output_bytes'),
        })
    # Per-trial frozen plan, not a batch marker whose labels may be stale.
    model, effort = plan['model'], plan['effort']
    for a in analyzed.values():
        assert a['native_contexts'] == [[model, effort]], 'Native model/effort differs from frozen plan'
    return {
        'run': str(row.get('condition', row.get('label', 'trial'))) + str(row.get('repetition', row.get('trial', 1))),
        'started_at': min(w['started_at'] for w in workers),
        'finished_at': max(w['finished_at'] for w in workers),
        'condition': row.get('condition'), 'model': model, 'effort': effort,
        'fixture_version': plan['version'],
        'pi_enabled': bool(manifest),
        'pi_backend_sha256': fingerprint(manifest, 'project_intent/'),
        'pi_workflow_sha256': fingerprint(manifest, 'skills/project-intent/'),
        'plan_sha256': None,  # Set from the original bytes by collect().
        'input_hashes': plan.get('input_hashes', {}),
        'score': scored['score'], 'out_of': scored['out_of'],
        'producer_seams': sum(p['producer']['passed'] for p in problems.values()) if migrated else None,
        'consumer_seams': sum(p['consumer']['passed'] for p in problems.values()) if migrated else None,
        'failed_seams': [k for k, v in problems.items() if not passed(v)],
        'accepted': scored['score'] == scored['out_of'] and all(w['exit_code'] == 0 for w in workers),
        'worker_window_seconds': interval, 'aggregate_worker_seconds': worker_seconds,
        'project_seconds': outer.get('project_seconds'),
        'setup_seconds': outer.get('setup_seconds'),
        'archive_seconds': outer.get('archive_seconds'),
        'verification_seconds': outer.get('verification_seconds'),
        'human_interventions': outer.get('human_interventions'),
        'concurrency_factor': worker_seconds / interval,
        'aggregate_tokens': tokens((analysis or {}).get('tokens')),
        'workers': timings,
    }


def collect(evidence):
    groups = []
    for name in BATCHES:
        directory = evidence / name
        raw = read(directory / 'results.json')
        analyses = read(directory / 'analysis.json') if (directory / 'analysis.json').exists() else []
        indexed = {(a['condition'], a['repetition']): a for a in analyses}
        rows = []
        for original in raw.get('trials', [raw]):
            root = Path(original['root'])
            plan_path = root / 'plan.json'
            if not plan_path.is_file():
                raise ValueError('Missing frozen trial plan; do not infer model or timing from batch name')
            p = project(original, read(plan_path), indexed.get((original.get('condition'), original.get('repetition'))))
            p['plan_sha256'] = sha(plan_path)
            rows.append(p)
        rows.sort(key=lambda p: p['started_at'], reverse=True)
        sources = {file: sha(directory / file) for file in
                   ('results.json', 'analysis.json', 'native-verification.json', 'REPORT.md', 'observations.json')
                   if (directory / file).is_file()}
        groups.append({'id': name, 'started_at': min(r['started_at'] for r in rows),
                       'last_trial_started_at': max(r['started_at'] for r in rows),
                       'sources_sha256': sources, 'trials': rows})
    groups.sort(key=lambda g: g['last_trial_started_at'], reverse=True)
    return {'schema': 'project-intent/public-results/v1',
            'scope': 'Completed original-seven-seam and refund studies; older/infrastructure attempts are catalogued separately.',
            'timing': 'project_seconds is post-exit verified time where recorded; historical worker_window_seconds excludes final verification. Null means unavailable, never zero.',
            'tokens': 'Final cumulative native counters where analyzed. Cache is a subset of input; reasoning is a subset of output. Mixed PI-tagged time is not pure PI latency.',
            'groups': groups}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(collect(args.evidence), indent=2))


if __name__ == '__main__':
    main()
