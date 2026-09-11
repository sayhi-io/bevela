"""Continue four untouched projects after verified predetermined timeout cleanup.

No model retries, changed inputs, longer deadlines or rewritten old results.
"""
import argparse
import copy
import fcntl
import json
from pathlib import Path
from types import SimpleNamespace

from experiments import qwen_independent_resume as previous

study = previous.study
VERSION = 'qwen-independent-requests/native-timeout-audit-v2'
REMAINING = ('B2', 'A2', 'A3', 'B3')


def timeout_errors(worker, plan, transport):
    """Only successful in-flight responses severed at a proven native deadline."""
    errors = [r for r in transport if r.get('event') in ('transport_error', 'handler_error')
              or (r.get('event') == 'response' and r.get('status', 200) >= 400)]
    if not worker.get('timed_out'):
        if errors:
            raise ValueError('Non-timeout transport failure')
        return []
    duration = (worker['end_monotonic_ns'] - worker['start_monotonic_ns']) / 1e9
    if (worker.get('exit_code') not in (-15, -9) or
            not plan['timeout_seconds'] <= duration <= plan['timeout_seconds'] + 30 or
            abs(duration - worker['elapsed_seconds']) > .01):
        raise ValueError('Timeout termination boundary not verified')
    cutoff = worker['start_monotonic_ns'] + plan['timeout_seconds'] * 1e9
    for error in errors:
        if (error.get('event') != 'transport_error' or
                error.get('type') not in ('ConnectionResetError', 'BrokenPipeError', 'IncompleteRead') or
                not cutoff <= error.get('mono_ns', 0) <= worker['end_monotonic_ns'] + 15e9):
            raise ValueError('Error is outside permitted timeout cleanup')
        requests = [r for r in transport if r.get('event') == 'request' and r.get('request') == error.get('request')]
        responses = [r for r in transport if r.get('event') == 'response' and r.get('request') == error.get('request')]
        if (len(requests) != 1 or len(responses) != 1 or responses[0].get('status') != 200 or
                not requests[0]['mono_ns'] <= responses[0]['mono_ns'] < cutoff):
            raise ValueError('No matching successful response before deadline')
        if any(r.get('event') == 'usage' and r.get('request') == error.get('request')
               and r['mono_ns'] < cutoff for r in transport):
            raise ValueError('Request was already complete before timeout')
    return errors


def audit(root, plan):
    raw_result = study.read(root / 'result.json')
    raw_evidence = study.read(root / 'worker-analysis.json')
    result, evidence = copy.deepcopy(raw_result), copy.deepcopy(raw_evidence)
    by_role = {r['role']: r for r in evidence}
    cleanup = {}
    for worker in result['workers']:
        role = worker['role']
        errors = timeout_errors(worker, plan, previous.rows(root / role / 'transport.jsonl'))
        if by_role[role]['transport_errors'] != errors:
            raise ValueError('Native transport error coverage differs')
        by_role[role]['transport_errors'] = []
        if worker.get('timed_out'):
            cleanup[role] = dict(deadline_seconds=plan['timeout_seconds'],
                exit_code=worker['exit_code'], elapsed_seconds=worker['elapsed_seconds'], errors=errors)
        if errors:
            entry = dict(role=role, errors=errors)
            if result['infrastructure_errors'].count(entry) != 1:
                raise ValueError('Unexpected infrastructure error attribution')
            result['infrastructure_errors'].remove(entry)
    # Reuse all v1 settings/identity/output checks. Only these two in-memory
    # projections omit corroborated cleanup errors; original files never change.
    variant = study.profiles.private_module(previous)
    def read(path):
        if Path(path) == root / 'result.json':
            return copy.deepcopy(result)
        if Path(path) == root / 'worker-analysis.json':
            return copy.deepcopy(evidence)
        return study.read(path)
    variant.study = SimpleNamespace(**{**vars(study), 'read': read})
    reviewed = variant.audit(root, plan)
    reviewed.update(version=VERSION, timeout_cleanup=cleanup,
        meaning='Observer-only output-budget and corroborated timeout-cleanup audit. Timeouts remain unsuccessful workers, source score unchanged.')
    return reviewed


def verify(batch):
    previous.verify_cohort(batch, fresh=False)
    old = study.read(batch / 'continuation-v1/frozen.json')
    if (old['source_sha256'] != study.original.sha(previous.__file__) or
            old['cohort_sha256'] != study.original.sha(batch / 'frozen.json') or
            old['stop_sha256'] != study.original.sha(batch / 'stopped.json') or
            old['a1_audit_sha256'] != study.original.sha(batch / 'continuation-v1/A1-audit.json') or
            study.read(batch / 'continuation-v1/stopped.json')['label'] != 'B1'):
        raise ValueError('Prior continuation boundary changed')
    if previous.audit(batch / 'A1', study.read(batch / 'A1/plan.json')) != study.read(batch / 'continuation-v1/A1-audit.json'):
        raise ValueError('A1 evidence changed')
    for label in REMAINING:
        if (batch / label / 'started.json').exists():
            raise ValueError('Remaining project already started; no replay')
        study.runner(label.startswith('B')).verify(batch / label, before=True)


def freeze(batch):
    with (batch / '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        verify(batch)
        target = batch / 'continuation-v2'
        reviewed = audit(batch / 'B1', study.read(batch / 'B1/plan.json'))
        target.mkdir(exist_ok=False)
        study.original.write_json(target / 'B1-audit.json', reviewed)
        study.original.write_json(target / 'frozen.json', dict(version=VERSION, at=study.original.utc(),
            order=REMAINING, source_sha256=study.original.sha(__file__),
            previous_source_sha256=study.original.sha(previous.__file__),
            cohort_sha256=study.original.sha(batch / 'frozen.json'),
            prior_stop_sha256=study.original.sha(batch / 'continuation-v1/stopped.json'),
            b1_audit_sha256=study.original.sha(target / 'B1-audit.json'),
            authorization='User: continue the test if you can; preserve B1 timeout and launch only four untouched projects.'))
        print(json.dumps({'queued': REMAINING, 'b1_accepted': reviewed['accepted'],
            'timed_out_workers': list(reviewed['timeout_cleanup'])}), flush=True)


def run(batch):
    with (batch / '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        target = batch / 'continuation-v2'
        frozen = study.read(target / 'frozen.json')
        if (frozen['version'] != VERSION or frozen['order'] != list(REMAINING) or
                frozen['source_sha256'] != study.original.sha(__file__) or
                frozen['previous_source_sha256'] != study.original.sha(previous.__file__) or
                frozen['cohort_sha256'] != study.original.sha(batch / 'frozen.json') or
                frozen['prior_stop_sha256'] != study.original.sha(batch / 'continuation-v1/stopped.json') or
                frozen['b1_audit_sha256'] != study.original.sha(target / 'B1-audit.json')):
            raise ValueError('Timeout continuation changed')
        verify(batch)
        if audit(batch / 'B1', study.read(batch / 'B1/plan.json')) != study.read(target / 'B1-audit.json'):
            raise ValueError('B1 evidence changed')
        with (target / 'started.json').open('x') as stream:
            json.dump({'at': study.original.utc(), 'frozen_sha256': study.original.sha(target / 'frozen.json')}, stream)
        for label in REMAINING:
            print(json.dumps({'launch': label, 'at': study.original.utc()}), flush=True)
            try:
                value = study.runner(label.startswith('B')).run(batch / label)
                reviewed = audit(batch / label, study.read(batch / label / 'plan.json'))
                study.original.write_json(target / (label + '-audit.json'), reviewed)
                print(json.dumps({'finished': label, 'accepted': value['accepted'],
                    'score': sum(g['passed'] for g in value['result'].get('groups', {}).values()),
                    'seconds': value['project_seconds'], 'timed_out_workers': list(reviewed['timeout_cleanup'])}), flush=True)
            except Exception as exc:
                study.original.write_json(target / 'stopped.json', dict(label=label, at=study.original.utc(),
                    error=type(exc).__name__ + ': ' + str(exc)))
                raise
        study.original.write_json(target / 'completed.json', dict(at=study.original.utc(),
            projects=4, total_projects_including_original_A1_B1=6))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'run'))
    parser.add_argument('batch', type=Path)
    args = parser.parse_args()
    (freeze if args.action == 'freeze' else run)(args.batch.resolve())
