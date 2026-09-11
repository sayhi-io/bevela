"""Read-only, allowlisted posthoc export; never imports/runs the study or candidate.

Only registered freezes and completed JSON records are read. Native profiles,
native logs, source history, candidate code and rejected unregistered directories
are never opened. Print JSON to stdout; publication is a separate reviewed step.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re


ROLES = ('solo', 'catalog', 'orders', 'settlement', 'reporting')
STAGES = ('calibration', 'ceiling', 'evaluation')
TOKEN_KEYS = ('input_tokens', 'cached_input_tokens', 'cache_write_input_tokens',
              'output_tokens', 'reasoning_output_tokens', 'total_tokens')
OPERATIONS = ('onboard', 'discover', 'enroll', 'start', 'repair-status',
              'repair-claim', 'repair-ack', 'repair-complete', 'repair-release',
              'report-status', 'report', 'docs')
NOTES = {
    'scope': 'Registered software batches only; no invented rows for unallocated stages. '
             'Unregistered prelaunch rejections need a separate curated report.',
    'unfinished': 'Started without complete result and analysis is unfinished, not a '
                  'verified live process or a failure. Only marker existence is checked.',
    'privacy': 'Free-form details, commands, messages, session IDs and raw logs are omitted. '
               'Output paths are filtered lexical checkout-relative names, not resolved files.',
    'tokens': 'Cached input is a subset of input; reasoning output is a subset of output. '
              'Missing fields remain null. Totals require every planned worker field. '
              'Last cumulative samples include post-probe work; timeout usage is partial.',
    'pi': 'PI tags and operation names are textual candidates, not successful invocations '
          'or causal influence. Native paired call time includes mixed work and excludes '
          'intervening reasoning. Command output bytes and native output bytes are distinct; '
          'neither is an exact PI token counter. Onboarding span includes intervening work.',
    'edits': 'Patch-call candidates and file-change events are recorded attempts, not '
             'retained contributions or all shell writes. Relative paths do not establish '
             'ownership. No duplication, rework or efficiency score is inferred.',
    'timing': 'Worker/process window, final project verification and sampled first/durable '
              'source acceptance are separate. Replay is non-atomic and already recorded; '
              'this exporter never runs it. Active intervals count processes, not useful work.',
    'provenance': 'Registry/freeze/plan/result/analysis/replay/review JSON digests are computed '
                  'from read bytes. Code/fixture manifests and history/native digests are '
                  'copied declarations, not independently rehashed source or logs. Review '
                  'result/analysis bindings are checked; qualitative review text is omitted.',
}


class ExportError(ValueError):
    """Messages must be safe for public stderr: no paths or source content."""


def digest(value, length=64):
    return value if isinstance(value, str) and re.fullmatch('[0-9a-f]{%d}' % length, value) else None


def number(value, integer=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(value) or (integer and not isinstance(value, int)):
        return None
    return value


def count(value):
    n = number(value, integer=True)
    return n if n is not None and n >= 0 else None


def boolean(value):
    return value if isinstance(value, bool) else None


def timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
        return parsed.astimezone(timezone.utc).isoformat() if parsed.tzinfo is not None else None
    except ValueError:
        return None


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,63}', value):
        return None
    return None if re.search(r'[0-9a-f]{24,}', value) else value


def relative_path(value, checkout=None):
    if not isinstance(value, str) or '\\' in value or any(ord(c) < 32 for c in value):
        return None
    path = PurePosixPath(value)
    if path.is_absolute():
        if checkout is None:
            return None
        try:
            path = path.relative_to(PurePosixPath(str(checkout)))
        except ValueError:
            return None
    if not path.parts or '..' in path.parts:
        return None
    forbidden = {'.git', '.pi', '.codex', '.env', 'auth.json', 'sessions', 'credentials',
                 'cookies', 'secrets', 'tokens', '__pycache__'}
    if any(p.lower() in forbidden or p.lower().startswith('.env.') for p in path.parts):
        return None
    text = str(path)
    if not re.fullmatch(r'[A-Za-z0-9_./ -]{1,240}', text):
        return None
    if re.search(r'[0-9a-f]{24,}|[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', text, re.I):
        return None
    return text


def read_json(path):
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def optional_json(path):
    try:
        return read_json(path)
    except (OSError, ValueError):
        return None, None


def manifest_hashes(value):
    return {name: digest(meta.get('sha256')) for name, meta in (value or {}).items()
            if relative_path(name) == name and isinstance(meta, dict)
            and digest(meta.get('sha256')) is not None}


def token_fields(value):
    value = value if isinstance(value, dict) else {}
    return {k: count(value.get(k)) for k in TOKEN_KEYS}


def known_sum(values):
    return sum(values) if values and all(v is not None for v in values) else None


def named_outcomes(value, components=False):
    rows = []
    for name, item in (value or {}).items():
        if not isinstance(item, dict):
            continue
        safe = name if components and name in ROLES else identifier(name) if not components else None
        rows.append({'name': safe, 'passed': boolean(item.get('passed')),
                     'tests_run': count(item.get('tests_run')),
                     'failures': count(item.get('failures')), 'errors': count(item.get('errors')),
                     'details_omitted': any(k not in ('passed', 'tests_run', 'failures', 'errors')
                                            for k in item)})
    return rows


def worker_row(role, process, telemetry, checkout):
    process, telemetry = process or {}, telemetry or {}
    edits = telemetry.get('edits')
    edits = edits if isinstance(edits, list) else None
    patches = telemetry.get('patch_calls')
    pi_calls = telemetry.get('pi_native_calls')
    paths, omitted = set(), 0
    for edit in edits or []:
        if edit.get('status') != 'completed':
            continue
        for change in edit.get('changes', []):
            safe = relative_path(change.get('path'), checkout)
            if safe is None:
                omitted += 1
            else:
                paths.add(safe)
    contexts = telemetry.get('native_contexts')
    expected = [['gpt-5.6-sol', 'medium']]
    tokens = token_fields(telemetry.get('tokens'))
    timeout = boolean(process.get('timed_out'))
    usage = 'unknown' if all(v is None for v in tokens.values()) else (
        'partial_timeout' if timeout else 'last_observed_cumulative')
    ops = telemetry.get('pi_operation_candidate_counts')
    return {
        'role': role, 'started_at': timestamp(process.get('started_at')),
        'finished_at': timestamp(process.get('finished_at')),
        'duration_seconds': number(process.get('elapsed_seconds')),
        'start_seconds': number(telemetry.get('start_seconds')),
        'end_seconds': number(telemetry.get('end_seconds')),
        'exit_code': number(process.get('exit_code'), integer=True),
        'timed_out': timeout if timeout is not None else (False if process else None),
        'stream_complete': boolean(process.get('stream_complete')),
        'native_identity_verified': contexts == expected if isinstance(contexts, list) else None,
        'tokens': tokens, 'token_usage_status': usage,
        'tools': {
            'native_paired_call_count': count(telemetry.get('native_tool_call_count')),
            'pi_tagged_native_call_count': len(pi_calls) if isinstance(pi_calls, list) else None,
            'pi_tagged_command_count': count(telemetry.get('pi_command_candidates')),
            'pi_tagged_native_seconds': number(telemetry.get('pi_native_tool_seconds')),
            'pi_tagged_command_output_bytes': count(telemetry.get('pi_output_bytes')),
            'pi_tagged_native_output_bytes': (sum(c['output_bytes'] for c in pi_calls)
                if isinstance(pi_calls, list) and all(count(c.get('output_bytes')) is not None for c in pi_calls)
                else None),
            'enrollment_completed_seconds': number(telemetry.get('enrollment_completed_seconds')),
            'onboarding_observed_span_seconds': number(telemetry.get('onboarding_observed_span_seconds')),
            'pi_failed_commands': count(telemetry.get('pi_failed_commands')),
            'pi_operation_candidates': {k: count(ops[k]) for k in OPERATIONS if k in ops}
                if isinstance(ops, dict) else None,
        },
        'edits': {'patch_call_candidates': len(patches) if isinstance(patches, list) else None,
                  'file_change_events': len(edits) if edits is not None else None,
                  'completed_file_change_events': sum(e.get('status') == 'completed' for e in edits)
                      if edits is not None else None,
                  'failed_file_change_events': sum(e.get('status') == 'failed' for e in edits)
                      if edits is not None else None,
                  'reported_relative_paths': sorted(paths), 'omitted_path_entries': omitted},
        'native_sha256_declared_by_analysis': digest(telemetry.get('native_sha256')),
    }


def project(trial, batch):
    label = trial.get('label')
    if not isinstance(label, str) or not re.fullmatch(r'[ABC][1-9][0-9]*', label):
        raise ExportError('Invalid trial label')
    root = Path(trial['root'])
    base = {'label': label, 'condition': label[0], 'status': 'not_run',
            'accepted': None, 'autonomous_complete': None, 'native_identity_verified': None,
            'workers': [], 'provenance': {'plan_sha256': digest(trial.get('plan_sha256'))}}
    # Do not open even the plan of an unfinished trial, let alone its live logs.
    if not (root / 'result.json').is_file() or not (root / 'worker-analysis.json').is_file():
        if (root / 'started.json').exists() or (root / 'result.json').exists():
            base['status'] = 'unfinished'
        return base
    result, result_sha = optional_json(root / 'result.json')
    telemetry, analysis_sha = optional_json(root / 'worker-analysis.json')
    if not isinstance(result, dict) or not isinstance(telemetry, list):
        base['status'] = 'recording_incomplete'
        return base
    plan, plan_sha = read_json(root / 'plan.json')
    if plan_sha != trial.get('plan_sha256'):
        raise ExportError('Completed plan digest mismatch')
    roles = plan.get('roles', [])
    if not roles or len(set(roles)) != len(roles) or any(r not in ROLES for r in roles):
        raise ExportError('Invalid completed worker roles')
    if plan.get('condition') != label[0] or result.get('condition') != label[0]:
        raise ExportError('Condition binding mismatch')
    processes = {r['role']: r for r in result.get('workers', []) if r.get('role') in roles}
    analyzed = {r['role']: r for r in telemetry if r.get('role') in roles}
    workers = [worker_row(role, processes.get(role), analyzed.get(role), root / 'work') for role in roles]
    review, review_sha = optional_json(batch / (label + '-review.json'))
    review = review if isinstance(review, dict) else None
    if isinstance(review, dict):
        if review.get('result_sha256') != result_sha or review.get('analysis_sha256') != analysis_sha:
            raise ExportError('Completed review binding mismatch')
        native_hashes = review.get('native_sha256')
        if isinstance(native_hashes, dict):
            for role in roles:
                declared = digest(native_hashes.get(role))
                observed = digest(analyzed.get(role, {}).get('native_sha256'))
                if declared is not None and observed is not None and declared != observed:
                    raise ExportError('Native digest declarations disagree')
    replay, replay_sha = optional_json(root / 'replay.json')
    replay = replay if isinstance(replay, dict) else {}
    sampled = replay.get('sampled_states', [])
    concurrency = result.get('concurrency') or {}
    timeline = [{'seconds': number(r.get('seconds')), 'active': count(r.get('active'))}
                for r in concurrency.get('active_timeline', [])]
    intervals = [{'start_seconds': a['seconds'], 'end_seconds': b['seconds'], 'active': a['active']}
                 for a, b in zip(timeline, timeline[1:])
                 if a['seconds'] is not None and b['seconds'] is not None and a['active'] is not None]
    outcome = result.get('result') or {}
    starts = [w['started_at'] for w in workers if w['started_at']]
    ends = [w['finished_at'] for w in workers if w['finished_at']]
    base.update({
        'status': 'completed_reviewed' if isinstance(review, dict) else 'completed_unreviewed',
        'accepted': boolean(result.get('accepted')),
        'autonomous_complete': boolean(result.get('autonomous_complete')),
        'native_identity_verified': boolean(result.get('native_identity_verified')),
        'model': plan.get('model') if plan.get('model') == 'gpt-5.6-sol' else None,
        'effort': plan.get('effort') if plan.get('effort') == 'medium' else None,
        'pi_enabled': boolean(plan.get('pi_enabled')),
        'started_at': min(starts) if len(starts) == len(roles) else None,
        'finished_at': max(ends) if len(ends) == len(roles) else None,
        'outcomes': {'groups': named_outcomes(outcome.get('groups')),
                     'components': named_outcomes(outcome.get('component_checks'), True),
                     'failed_contracts': [identifier(n) for n in outcome.get('failed_contracts', [])],
                     'evaluation_error_present': bool(outcome.get('evaluation_error'))},
        'timing': {k: number(result.get(k)) for k in
                   ('setup_seconds', 'archive_seconds', 'verification_seconds', 'project_seconds')},
        'concurrency': {k: number(concurrency.get(k)) for k in
                        ('worker_interval_seconds', 'worker_seconds', 'factor', 'max_simultaneous')},
        'replay': {'first_accepted_sample_seconds': number(replay.get('first_accepted_sample_seconds')),
                   'durable_accepted_sample_seconds': number(replay.get('durable_accepted_sample_seconds')),
                   'final_sample_matches_final_score': boolean(replay.get('final_sample_matches_final_score')),
                   'sampled_state_count': len(sampled) if replay else None,
                   'evaluation_error_state_count': sum(bool(s.get('evaluation_error')) for s in sampled)
                       if replay else None},
        'review': {'available': isinstance(review, dict),
                   'infrastructure_failure': boolean((review or {}).get('infrastructure_failure')),
                   'integrity_failure': boolean((review or {}).get('integrity_failure'))},
        'workers': workers,
        'tokens_last_observed_sum': {k: known_sum([w['tokens'][k] for w in workers]) for k in TOKEN_KEYS},
        'token_totals_include_partial_timeout': any(w['token_usage_status'] == 'partial_timeout' for w in workers),
    })
    base['concurrency']['active_intervals'] = intervals
    base['provenance'].update({
        'result_sha256': result_sha, 'worker_analysis_sha256': analysis_sha,
        'replay_sha256': replay_sha, 'review_sha256': review_sha,
        'history_sha256_declared_by_review': digest((review or {}).get('history_sha256')),
        'native_sha256_declared_by_review': {role: digest(((review or {}).get('native_sha256') or {}).get(role))
                                            for role in roles},
        'before_sha256_declared_by_plan': digest(plan.get('before_sha256')),
        'recorder_sha256_declared_by_plan': digest(plan.get('own_recorder_sha256')),
        'pi_commit': digest(plan.get('pi_commit'), 40),
        'input_hashes_declared_by_plan': {n: digest(v) for n, v in plan.get('input_hashes', {}).items()
                                        if relative_path(n) == n and digest(v)},
    })
    return base


def collect(study):
    """Return sanitized JSON-compatible data; no writes, subprocesses or log reads."""
    study = Path(study)
    registry, registry_sha = read_json(study / 'study.json')
    batches = []
    candidates = registry.get('candidates', [])
    for record in registry.get('batches', []):
        batch = Path(record['path'])
        frozen, freeze_sha = read_json(batch / 'freeze.json')
        if freeze_sha != record.get('freeze_sha256'):
            raise ExportError('Registered freeze digest mismatch')
        stage = frozen.get('stage')
        if stage not in STAGES:
            raise ExportError('Invalid stage')
        matches = [i + 1 for i, c in enumerate(candidates)
                   if (stage == 'calibration' and c.get('path') == record['path']) or
                   (stage != 'calibration' and c.get('fixture_manifest') == record.get('fixture_manifest')
                    and c.get('checker_sha256') == record.get('checker_sha256'))]
        candidate = matches[0] if len(matches) == 1 else None
        projects = [project(t, batch) for t in frozen.get('trials', [])]
        batches.append({'stage': stage, 'candidate': candidate,
            'frozen_at': timestamp(frozen.get('at')), 'projects': projects,
            'status_counts': dict(Counter(p['status'] for p in projects)),
            'provenance': {'freeze_sha256': freeze_sha,
                'protocol_sha256_declared': digest(frozen.get('protocol_sha256')),
                'code_sha256_declared': manifest_hashes(frozen.get('code_manifest')),
                'fixture_sha256_declared': manifest_hashes(frozen.get('fixture_manifest')),
                'tests_sha256_declared': manifest_hashes(frozen.get('tests_manifest'))}})
    return {'schema_version': 1, 'study_kind': 'sol_distributed_software',
        'stages_allocated': {stage: any(b['stage'] == stage for b in batches) for stage in STAGES},
        'batches': batches, 'limitations': NOTES,
        'provenance': {'registry_sha256': registry_sha,
            'protocol_freeze_sha256_declared': digest(registry.get('protocol_freeze_sha256')),
            'native_version_declared': registry.get('codex_version') if isinstance(registry.get('codex_version'), str)
                and re.fullmatch(r'codex-cli [0-9]+\.[0-9]+\.[0-9]+', registry['codex_version']) else None,
            'native_entry_sha256_declared': digest(registry.get('codex_entry_sha256')),
            'pi_sha256_declared': manifest_hashes(registry.get('pi_manifest'))}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        value = collect(args.study)
        print(json.dumps(value, indent=2, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        parser.error(str(exc) if isinstance(exc, ExportError) else 'Incomplete or invalid study JSON')


if __name__ == '__main__':
    main()
