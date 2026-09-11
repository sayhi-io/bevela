"""Six sequential projects, three independent requests; ordinary vs PI steering.

Only assignment documents change from candidate2. Historical source/checker and
the native recorder, PI backend, compact instructions and steering stay frozen.
"""
import argparse
import contextvars
import fcntl
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from experiments import qwen_distributed_study as original
from experiments import qwen_profiles as profiles
from experiments import qwen_distributed_steering as steering

VERSION = 'qwen-independent-requests/candidate2-v1'
SOURCE = Path(__file__).resolve().parents[1]
FIXTURE = SOURCE / 'experiments/assets/distributed_v2/fixture'
ROLES = ('money', 'recovery', 'returns')
ORDER = ('A1', 'B1', 'B2', 'A2', 'A3', 'B3')
SCOPE = 'experiment/independent-requests-v1'
MODEL = 'qwen38-27b-dflash2'
PROFILE = {**profiles.DEFAULT, 'thinking': False, 'confidence': False}
COMMON = '''# Development environment

Implement your assigned request. Use ordinary shell, Git, source inspection and
tests. README.md describes the project. Product contracts in OBJECTIVE.md are
reference requirements, not an assignment to implement other requests yourself.
You may edit any implementation or test files needed for your request; component
directories are not worker ownership boundaries. Preserve existing behavior.
The integrated checker is `python3 -B acceptance.py .`.
Do not modify acceptance.py, OBJECTIVE.md, README.md, architecture.json, AGENTS.md
or tasks/. Preserve existing tests; you may add tests. No further task messages
will arrive. Report what you implemented, checks performed and remaining issues.
'''
TASKS = {
    'money': '''Migrate money safely.

Move the product from dollar-based money to integer cents while preserving legacy
interfaces and persisted records. Follow OBJECTIVE.md's exact rounding, validation,
public field shapes and migration contracts. Implement integer-minor catalog
pricing/quotes and money conversion in orders, payments and receipts. Preserve
historical recorded totals rather than recomputing them from today's prices.
Migrate all four version-1 stores, retain their existing identities and history,
and keep legacy inputs, old wire money, legacy reads and receipt formatting working.
Validate precision, zero-value behavior, detached returned data, migration/reopen
and legacy compatibility. Malformed/unsupported state must not be silently reset.

Implement this request in the existing product, including changes wherever needed
to make its behavior work. OBJECTIVE.md supplies the complete reference contract;
this request concerns money representation, persistence migration and compatibility,
not an assignment to implement every other product feature. Preserve required
business behavior while changing its representation. Use normal development tools
and decide your implementation approach. Report verified results and unresolved work.
''',
    'recovery': '''Make interrupted purchases recoverable.

Make purchase reservation, order persistence, delivery and payment processing
survive retries, restarts, duplicate events and cancellation arriving out of order.
Follow OBJECTIVE.md's exact APIs and failure boundaries: atomic basket validation,
idempotent reserve/release/place/cancel, interrupted placement recovery, durable
outboxes and acknowledgments, normalized duplicate/conflict validation, deferred
capture and cancellation without recapture or double refund. Preserve original
snapshots and support delayed order/payment joins, correct receipt status/revenue,
zero-priced purchases and legacy behavior. Keep validation failures non-mutating
and persist updates with the required same-directory atomic replacement.

Implement this request in the existing product, including changes wherever needed
to make its behavior work. OBJECTIVE.md supplies the complete reference contract;
this request concerns purchase lifecycle reliability and its observable effects,
not an assignment to implement every other product feature. Use normal development
tools and decide your implementation approach. Report verified results and unresolved work.
''',
    'returns': '''Support partial returns.

Let customers return selected purchased items. Restore inventory exactly once,
retain return identity across retries and restarts, calculate credit from original
purchase snapshots, and reflect actual refunds in receipts and revenue. Follow
OBJECTIVE.md's durable partial-return contract in full, including interrupted
restoration recovery, cumulative historical rounding, cancellation after returns,
out-of-order financial events, zero-value returns and reopening pre-return state.
Implement restore, return_items/returns and return_summary with the exact public
APIs specified there. Document actual new JSON receipts/events in the producing
component's CONTRACT.md and integrate those real representations through consumers.
Preserve no-return behavior and old interfaces; do not use cross-component private
state or shared parsers to bypass the public contracts.

Implement this request in the existing product, including changes wherever needed
to make its behavior work. OBJECTIVE.md supplies the complete reference contract;
this request concerns partial-return behavior, not an assignment to implement every
other product feature. Use normal development tools and decide your implementation
approach. Report verified results and unresolved work.
''',
}

# Exact replacements remove historical allocation, not business requirements.
REPLACEMENTS = (
    ('# Depot migration and partial-return contract — candidate2', '# Depot product contracts — independent requests v1'),
    ('Implement the complete contract in this file:', 'Reference contract for the product requests in tasks/:'),
    ('Migrate the working dollar-based product to reliable integer-minor-unit commerce.\nPreserve its legacy entry points while implementing the complete contract below.',
     'The requested product evolution is reliable integer-minor-unit commerce.\nIts legacy entry points and the functional contracts below remain required.'),
    ('Four components\nhave distinct owned roots;', 'Four components\nhave distinct storage roots;'),
    ('Implement only your assigned component root(s); all component contracts are visible.\nYou may add focused tests inside those roots. Preserve existing legacy tests.\nDo not modify this objective, supplied role tasks, or the acceptance checker.\nThe solo task owns all four roots with identical functional requirements.',
     'Implement your assigned request wherever needed in the product. Component roots\nare not worker ownership boundaries. Preserve existing legacy tests; new tests\nare allowed. Do not modify this reference, supplied tasks, or acceptance checker.'),
    ('New shared boundary contracts/partial-returns applies to all four roles, in\naddition to the unchanged v1 boundary map. Source-root ownership remains the same.',
     'The contracts/partial-returns boundary applies to all four components, in\naddition to the unchanged v1 boundary map. Storage remains component-local.'),
)
README_REPLACEMENTS = (
    ('The complete requested migration is in [OBJECTIVE.md](OBJECTIVE.md). All four role\ntasks are visible in `tasks/`. A component assignment bounds source editing, not\naccess to the other components\' requirements or public APIs. No worker allocation,\nrepair sequence, messages, waiting period, or implementation strategy is prescribed.',
     'Product reference requirements are in [OBJECTIVE.md](OBJECTIVE.md). Task records\nare available in `tasks/`. Your request defines your work, not a component directory.'),
    ('role tasks', 'task records'),
)


def read(path):
    return json.loads(Path(path).read_text())


def replace_exact(text, replacements):
    for old, new in replacements:
        if text.count(old) != 1:
            raise ValueError('Historical assignment text changed: ' + old[:70])
        text = text.replace(old, new)
    return text


def make_fixture(target):
    """Copy immutable functional inputs; rewrite only explicitly listed documents."""
    shutil.copytree(FIXTURE, target, ignore=original.base.IGNORE)
    (target / 'tasks').rename(target.parent / 'historical-role-tasks')
    (target / 'tasks').mkdir()
    for role, prompt in TASKS.items():
        (target / 'tasks' / (role + '.txt')).write_text(prompt)
    for name, replacements in (('OBJECTIVE.md', REPLACEMENTS), ('README.md', README_REPLACEMENTS)):
        (target / name).write_text(replace_exact((target / name).read_text(), replacements))


def binding(root, plan):
    # Same 12-file allowlist as the previous distributed adapter; worker task IDs
    # are not component names. No evaluator predictions or task-specific filters.
    baseline = {name: entry['sha256'] for name, entry in plan['fixture_manifest'].items()
                if Path(name).parts[0] in original.base.ROLES and
                (Path(name).suffix == '.py' or Path(name).name == 'CONTRACT.md')}
    return dict(enabled=True, checkout=str(root / 'work'), scope=SCOPE,
        sessions={plan['sessions'][role]: role.upper() for role in ROLES}, baseline=baseline)


def install_pi(root, source):
    frozen, work = root / 'pi-source', root / 'work'
    original.base.copy_pi(source, frozen)
    (frozen / 'project_intent/_worker_cli.py').write_bytes(Path(steering.worker_cli.__file__).read_bytes())
    for module in (steering.hook, steering.nested):
        shutil.copy2(module.__file__, frozen / Path(module.__file__).name)
    context = work / '.pi'
    context.mkdir()
    # All three cross-product requests have product-wide architectural scope.
    # The broad union comes from the unchanged public architecture, not guessed
    # worker paths or a hidden collision map. Workers declare their actual edits.
    boundaries = sorted({b for bs in read(work / 'architecture.json')['boundaries'].values() for b in bs})
    records = [dict(kind='workstream', id=role.upper(), revision='1', state='active',
        statement=TASKS[role].splitlines()[0], scope=TASKS[role],
        acceptance=[TASKS[role]], boundaries=boundaries, readiness={},
        source_checkout=str(work)) for role in ROLES]
    original.write_json(context / 'snapshot.json', dict(version=1, scope_id=SCOPE,
        source=dict(provider='snapshot', authoritative=False, captured_at=original.utc(), mode='offline_snapshot'),
        mission='Product development requests recorded in tasks/.', records=records))
    original.write_json(context / 'worker.json', {'scopes': {SCOPE: dict(
        snapshot=str(context / 'snapshot.json'), enrollment_directory=str(context / 'presence'),
        report_directory=str(context / 'reports'))}})
    (work / 'AGENTS.md').write_text(COMMON + '\n' + steering.compact.instructions(SCOPE))


def runner(pi):
    engine = profiles.private_module(original)
    base = profiles.private_module(original.base)
    adapter = profiles.private_module(original.adapter)
    engine.base, engine.adapter, engine.VERSION = base, adapter, VERSION
    base.ROLES, base.COMMON = ROLES, COMMON
    profile = {**PROFILE, 'pi': pi}
    active = contextvars.ContextVar('independent_request_root', default=None)
    base_prepare, prepare_base, verify_base = base.prepare, engine.prepare, engine.verify
    run_base, preflight_base, record_base = engine.run, engine.preflight, adapter.record
    telemetry = profiles.runner(profile).telemetry

    def settings(*args, **kwargs):
        value = profiles.settings(profile, *args, **kwargs)
        value['model'].update(maxSessionTurns=500, maxToolCallsPerTurn=500)
        if pi and active.get() is not None:
            value['hooks'] = steering.hooks(active.get())
        return value

    def record(root, role, plan, observer=None):
        token = active.set(root)
        try:
            return record_base(root, role, plan, observer)
        finally:
            active.reset(token)

    def prepare_source(root, condition, source, fixture, checker, timeout):
        with tempfile.TemporaryDirectory(prefix='independent-request-inputs-') as directory:
            actual = Path(directory) / 'fixture'
            make_fixture(actual)
            # Build ordinary baseline first; original component PI assignments must
            # never enter these workers' source or Git history.
            base_prepare(root, 'B', source, actual, checker, timeout)
        plan = read(root / 'plan.json')
        plan.update(condition=condition, pi_enabled=pi)
        if pi:
            install_pi(root, source)
            subprocess.run(['git', '-C', str(root / 'work'), 'add', '.'], check=True)
            subprocess.run(['git', '-C', str(root / 'work'), '-c', 'user.name=Fixture',
                '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'Frozen PI integration'], check=True)
            (root / 'before').rename(root / 'ordinary-before')
            shutil.copytree(root / 'work', root / 'before', ignore=shutil.ignore_patterns('.git'))
        engine.write_json(root / 'plan.json', plan)

    modules = (steering, profiles, steering.compact, steering.worker_cli, steering.hook, steering.nested,
               profiles.original)

    def prepare(root, source, runtime, endpoint):
        prepare_base(root, 'C' if pi else 'B', source, runtime, endpoint, MODEL, 1800)
        plan = read(root / 'plan.json')
        if pi:
            engine.write_json(root / 'pi-source/steering.json', binding(root, plan))
        plan.update(condition='B' if pi else 'A', worker_count=3, effort='thinking-off',
            server_effort='medium', qwen_profile=profile, max_session_turns=500,
            max_tool_calls_per_turn=500, steering_enabled=pi,
            pi_manifest=engine.manifest(root / 'pi-source', ignore_cache=True) if pi else None,
            compact_template_sha256=engine.sha(steering.compact.TEMPLATE),
            study_route_sha256=engine.sha(__file__),
            treatment_hashes={Path(m.__file__).name: engine.sha(m.__file__) for m in modules},
            historical_fixture_manifest=engine.manifest(FIXTURE, ignore_cache=True),
            pi_commit=subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip() if pi else None,
            limits='Three independent task workers; six sequential projects. No evaluator feedback, retries, role ownership or post-exit resumption.')
        engine.write_json(root / 'plan.json', plan)
        return root

    def verify(root, before=False):
        plan = verify_base(root, before)
        if (plan['study_route_sha256'] != engine.sha(__file__) or
                plan['qwen_profile'] != profile or plan['steering_enabled'] != pi or
                plan['worker_count'] != 3 or plan['roles'] != list(ROLES) or
                plan['timeout_seconds'] != 1800 or plan['server_effort'] != 'medium' or
                plan['condition'] != ('B' if pi else 'A') or
                plan['historical_fixture_manifest'] != engine.manifest(FIXTURE, ignore_cache=True) or
                plan['compact_template_sha256'] != engine.sha(steering.compact.TEMPLATE) or
                any(plan['treatment_hashes'][Path(m.__file__).name] != engine.sha(m.__file__) for m in modules)):
            raise ValueError('Frozen independent-task profile changed')
        if read(root / 'settings-template.json') != settings(MODEL, plan['endpoint']):
            raise ValueError('Native settings changed')
        if pi and read(root / 'pi-source/steering.json') != binding(root, plan):
            raise ValueError('Steering bindings changed')
        return plan

    def worker_analysis(root, row):
        value = telemetry(root, row, read(root / 'plan.json'))
        value['native_identity_verified'] = all(value[k] for k in
            ('controls_verified', 'initialization_verified', 'final_identity_verified'))
        return value

    def preflight(root):
        preflight_base(root)
        plan = verify(root, before=True)
        for role in ROLES:
            result = subprocess.run(adapter.sandbox(root, role,
                ['/usr/bin/node', str(root / 'runtime/bin/qwen'), '--version'],
                plan['sessions'][role], pi=pi), capture_output=True, text=True, timeout=30)
            if result.returncode or result.stdout.strip() != '0.23.2':
                raise ValueError('Expected isolated Qwen Code 0.23.2')
        verify(root, before=True)

    def run(root):
        value = run_base(root)
        for evidence in read(root / 'worker-analysis.json'):
            if (not evidence['controls_verified'] or not evidence['initialization_verified']
                    or evidence.get('final_identity_mismatch')):
                value['infrastructure_errors'].append(dict(role=evidence['role'],
                    errors=['Native model/settings/session identity could not be verified']))
        initial = read(root / 'before.json')
        final = engine.manifest(root / 'after', ignore_cache=True)
        extra = ['README.md'] + (['.pi/snapshot.json', '.pi/worker.json'] if pi else [])
        value['protected_inputs_changed'] += [n for n in extra if initial.get(n) != final.get(n)]
        value['accepted'] = bool(value['accepted'] and not value['protected_inputs_changed'])
        value.update(qwen_profile=profile, steering_enabled=pi, steering_observations={})
        value['autonomous_complete'] = bool(value['accepted'] and value['autonomous_complete'] and
            not value['infrastructure_errors'] and all(w.get('relay_complete') for w in value['workers']))
        for role in ROLES:
            actual = read(root / 'qwen-home' / role / 'settings.json')
            if actual['model']['maxSessionTurns'] != 500 or actual['model']['maxToolCallsPerTurn'] != 500:
                raise ValueError('Native limits differ')
            if actual.get('hooks', {}) != (steering.hooks(root) if pi else {}):
                raise ValueError('Native steering setting differs')
            path = root / 'qwen-home' / role / 'pi-steering/events.jsonl'
            rows = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
            value['steering_observations'][role] = dict(hook_calls=len(rows),
                notices=sum(r['emitted'] for r in rows), seconds=sum(r['elapsed_seconds'] for r in rows),
                suppressed=max((r['suppressed'] for r in rows), default=0))
        engine.write_json(root / 'result.json', value)
        return value

    base.prepare, adapter.settings, adapter.record = prepare_source, settings, record
    engine.prepare, engine.verify, engine.preflight = prepare, verify, preflight
    engine.run, engine.worker_analysis = run, worker_analysis
    return engine


def freeze(batch, runtime, endpoint):
    batch.mkdir(parents=True, exist_ok=False)
    plans, sessions, signature = {}, set(), None
    for label in ORDER:
        engine = runner(label.startswith('B'))
        root = engine.prepare(batch / label, SOURCE, runtime, endpoint)
        engine.preflight(root)
        plan = engine.verify(root, before=True)
        comparable = {k: plan[k] for k in ('fixture_manifest', 'input_hashes', 'runtime_manifest', 'settings_sha256')}
        if signature is not None and comparable != signature:
            raise ValueError('Arms differ in common inputs')
        signature = comparable
        fresh = set(plan['sessions'].values())
        if len(fresh) != 3 or fresh & sessions:
            raise ValueError('Session reuse')
        sessions.update(fresh)
        plans[label] = engine.sha(root / 'plan.json')
        print(json.dumps({'frozen': label}), flush=True)
    original.write_json(batch / 'frozen.json', dict(version=VERSION, at=original.utc(),
        order=ORDER, plans=plans, common_inputs=signature, source_sha256=original.sha(__file__)))


def run_all(batch):
    with (batch / '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        frozen = read(batch / 'frozen.json')
        if frozen['version'] != VERSION or frozen['order'] != list(ORDER) or frozen['source_sha256'] != original.sha(__file__):
            raise ValueError('Frozen cohort changed')
        for label in ORDER:
            root = batch / label
            if original.sha(root / 'plan.json') != frozen['plans'][label] or (root / 'started.json').exists():
                raise ValueError('Changed or already started project; no replay')
            runner(label.startswith('B')).verify(root, before=True)
        with (batch / 'started.json').open('x') as stream:
            json.dump({'at': original.utc(), 'frozen_sha256': original.sha(batch / 'frozen.json')}, stream)
        for label in ORDER:
            print(json.dumps({'launch': label, 'at': original.utc()}), flush=True)
            try:
                value = runner(label.startswith('B')).run(batch / label)
                print(json.dumps({'finished': label, 'accepted': value['accepted'],
                    'score': sum(g['passed'] for g in value['result'].get('groups', {}).values()),
                    'seconds': value['project_seconds']}), flush=True)
                if (value['infrastructure_errors'] or value['protected_inputs_changed'] or value['result'].get('evaluation_error')
                        or not all(w.get('relay_complete') and w.get('stream_complete') for w in value['workers'])):
                    raise RuntimeError('Infrastructure or protected-input failure; cohort stopped without replacement')
            except Exception as exc:
                original.write_json(batch / 'stopped.json', dict(at=original.utc(), label=label,
                    error=type(exc).__name__ + ': ' + str(exc)))
                raise
        original.write_json(batch / 'completed.json', dict(at=original.utc(), projects=6))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'run'))
    parser.add_argument('batch', type=Path)
    parser.add_argument('--runtime', type=Path)
    parser.add_argument('--endpoint')
    args = parser.parse_args()
    if args.action == 'freeze':
        if not args.runtime or not args.endpoint:
            parser.error('freeze requires runtime and endpoint')
        freeze(args.batch.resolve(), args.runtime, args.endpoint)
    else:
        if args.runtime or args.endpoint:
            parser.error('run accepts frozen batch only')
        run_all(args.batch.resolve())


if __name__ == '__main__':
    main()
