"""User-authorized continuation after a recorder-only output-clamping false alarm.

Never resumes a native worker, changes a frozen plan, or overwrites old evidence.
The amendment changes post-exit classification only, equally for both arms.
"""
import argparse
import fcntl
import json
from pathlib import Path
from urllib.parse import urlsplit

from experiments import qwen_independent_tasks as study

VERSION = 'qwen-independent-requests/native-output-audit-v1'
REMAINING = study.ORDER[1:]
IDENTITY_ERROR = 'Native model/settings/session identity could not be verified'


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def audit(root, plan):
    """Require all original controls except equality of per-request output budget.

    The frozen native CLI is permitted to reduce (not increase) its configured
    output ceiling to fit context. This is not inferred model correctness.
    """
    result = study.read(root / 'result.json')
    evidence = study.read(root / 'worker-analysis.json')
    expected = {(r, s) for r, s in plan['sessions'].items()}
    for entries in (result['workers'], evidence):
        if len(entries) != len(expected) or {(r['role'], r['session']) for r in entries} != expected:
            raise ValueError('Worker/session coverage changed')
    if result['protected_inputs_changed'] or result['result'].get('evaluation_error'):
        raise ValueError('Protected inputs or evaluation failure')
    by_role = {r['role']: r for r in evidence}
    correction_roles, audits, hashes = [], {}, {}
    for worker in result['workers']:
        role = worker['role']
        native = by_role[role]
        if not (worker.get('relay_complete') and worker.get('stream_complete')
                and worker.get('stream_eof') and not worker.get('stream_error_type')):
            raise ValueError('Incomplete process/relay evidence')
        if not native['initialization_verified'] or native['final_identity_mismatch']:
            raise ValueError('Native identity failure')
        if native['transport_errors']:
            raise ValueError('Transport errors require separate inspection')
        if native['thinking_disabled_verified'] is not True:
            raise ValueError('Thinking-off not verified')
        request_path = root / role / 'transport.jsonl'
        requests = [r for r in rows(request_path) if r.get('event') == 'request']
        if not requests or not all(r.get('model') == plan['model'] and
                r.get('reasoning_effort') == 'medium' and
                r.get('chat_template_kwargs', {}).get('enable_thinking') is False and
                type(r.get('max_tokens')) is int and 1 <= r['max_tokens'] <= 32768 for r in requests):
            raise ValueError('Native request controls exceed permitted profile')
        settings_path = root / 'qwen-home' / role / 'settings.json'
        settings = study.read(settings_path)
        relay = urlsplit(settings['modelProviders']['openai'][0]['baseUrl'])
        if (relay.scheme != 'http' or relay.hostname != '127.0.0.1' or not relay.port
                or relay.path != '/v1' or relay.username or relay.password or relay.query or relay.fragment):
            raise ValueError('Native settings do not target the local recorder relay')
        # Compare every native setting, except the recorder's ephemeral loopback
        # relay port, against the frozen template and original steering hooks.
        expected_settings = study.read(root / 'settings-template.json')
        expected_settings['modelProviders']['openai'][0]['baseUrl'] = settings['modelProviders']['openai'][0]['baseUrl']
        if plan['pi_enabled']:
            expected_settings['hooks'] = study.steering.hooks(root)
        if settings != expected_settings:
            raise ValueError('Effective native settings changed')
        reduced = [dict(request=r['request'], at=r['at'], max_tokens=r['max_tokens'])
                   for r in requests if r['max_tokens'] < 32768]
        if not native['controls_verified']:
            if not reduced:
                raise ValueError('Unexplained original controls failure')
            correction_roles.append(role)
        audits[role] = dict(requests=len(requests), reduced_output_budgets=reduced,
            controls_verified=True, native_success=native['native_success'])
        for path in (request_path, settings_path, root / role / 'command.json'):
            hashes[str(path.relative_to(root))] = study.original.sha(path)
    permitted = [dict(role=role, errors=[IDENTITY_ERROR]) for role in correction_roles]
    if result['infrastructure_errors'] != permitted:
        raise ValueError('Unexpected infrastructure failure')
    for name in ('result.json', 'worker-analysis.json', 'plan.json'):
        hashes[name] = study.original.sha(root / name)
    complete = result['accepted'] and all(n['native_success'] and n['final_identity_verified'] for n in evidence) and all(
        w.get('exit_code') == 0 and not w.get('timed_out') for w in result['workers'])
    return dict(version=VERSION, accepted=result['accepted'],
        original_autonomous_complete=result['autonomous_complete'],
        audited_autonomous_complete=bool(complete), correction_roles=correction_roles,
        workers=audits, evidence_sha256=hashes,
        meaning='Observer correction only: native context-dependent output allowances within frozen ceiling; no worker or outcome modification.')


def verify_cohort(batch, fresh=True):
    frozen = study.read(batch / 'frozen.json')
    if (frozen['version'] != study.VERSION or frozen['order'] != list(study.ORDER)
            or frozen['source_sha256'] != study.original.sha(study.__file__)):
        raise ValueError('Original frozen study changed')
    for label in study.ORDER:
        root = batch / label
        if study.original.sha(root / 'plan.json') != frozen['plans'][label]:
            raise ValueError('Frozen plan changed')
        study.runner(label.startswith('B')).verify(root, before=fresh and label in REMAINING)
        if fresh and label in REMAINING and (root / 'started.json').exists():
            raise ValueError('Remaining project already started; no retry')
    stopped = study.read(batch / 'stopped.json')
    if stopped['label'] != 'A1' or (batch / 'completed.json').exists():
        raise ValueError('Unexpected continuation boundary')
    return frozen


def freeze(batch):
    with (batch / '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        verify_cohort(batch)
        corrected = audit(batch / 'A1', study.read(batch / 'A1/plan.json'))
        target = batch / 'continuation-v1'
        target.mkdir(exist_ok=False)
        study.original.write_json(target / 'A1-audit.json', corrected)
        study.original.write_json(target / 'frozen.json', dict(version=VERSION,
            at=study.original.utc(), order=REMAINING, source_sha256=study.original.sha(__file__),
            cohort_sha256=study.original.sha(batch / 'frozen.json'),
            stop_sha256=study.original.sha(batch / 'stopped.json'),
            a1_audit_sha256=study.original.sha(target / 'A1-audit.json'),
            authorization='User: start the other projects / queue them now; preserve completed A1, only five untouched projects.'))
        print(json.dumps({'continuation_frozen': list(REMAINING),
            'a1_accepted': corrected['accepted'], 'a1_audited_complete': corrected['audited_autonomous_complete']}), flush=True)


def run(batch):
    with (batch / '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        target = batch / 'continuation-v1'
        amendment = study.read(target / 'frozen.json')
        if (amendment['version'] != VERSION or amendment['order'] != list(REMAINING)
                or amendment['source_sha256'] != study.original.sha(__file__)
                or amendment['cohort_sha256'] != study.original.sha(batch / 'frozen.json')
                or amendment['stop_sha256'] != study.original.sha(batch / 'stopped.json')
                or amendment['a1_audit_sha256'] != study.original.sha(target / 'A1-audit.json')):
            raise ValueError('Continuation audit changed')
        verify_cohort(batch)
        if audit(batch / 'A1', study.read(batch / 'A1/plan.json')) != study.read(target / 'A1-audit.json'):
            raise ValueError('A1 evidence changed')
        with (target / 'started.json').open('x') as stream:
            json.dump({'at': study.original.utc(), 'amendment_sha256': study.original.sha(target / 'frozen.json')}, stream)
        for label in REMAINING:
            print(json.dumps({'launch': label, 'at': study.original.utc()}), flush=True)
            try:
                value = study.runner(label.startswith('B')).run(batch / label)
                reviewed = audit(batch / label, study.read(batch / label / 'plan.json'))
                study.original.write_json(target / (label + '-audit.json'), reviewed)
                print(json.dumps({'finished': label, 'accepted': value['accepted'],
                    'score': sum(g['passed'] for g in value['result'].get('groups', {}).values()),
                    'seconds': value['project_seconds'],
                    'audited_autonomous_complete': reviewed['audited_autonomous_complete']}), flush=True)
            except Exception as exc:
                study.original.write_json(target / 'stopped.json', dict(label=label,
                    at=study.original.utc(), error=type(exc).__name__ + ': ' + str(exc)))
                raise
        study.original.write_json(target / 'completed.json', dict(at=study.original.utc(),
            projects=5, total_projects_including_original_A1=6))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'run'))
    parser.add_argument('batch', type=Path)
    args = parser.parse_args()
    (freeze if args.action == 'freeze' else run)(args.batch.resolve())
