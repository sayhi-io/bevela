"""Local, opt-in recording of already authorized user tasks; not task assignment."""
from pathlib import Path

from .model import validate_snapshot
from .provider_write import OperatorProvider, reconcile
from .reporting import digest, locked
from .runtime import read_json, write_json
from .worker_context import checkout_identity


def validate_task(task):
    fields = {'title', 'statement', 'scope', 'acceptance', 'boundaries', 'avoid', 'authority_ref'}
    if not isinstance(task, dict) or set(task) != fields:
        raise ValueError('Task requires exactly: ' + ', '.join(sorted(fields)))
    for key in fields - {'acceptance', 'boundaries'}:
        value = task[key]
        if (not isinstance(value, str) or not value.strip() or len(value) > (200 if key == 'title' else 4000)
                or any(ord(c) < 32 and c != '\n' for c in value)):
            raise ValueError('Invalid task ' + key)
    for key in ('acceptance', 'boundaries'):
        values = task[key]
        if (not isinstance(values, list) or not 1 <= len(values) <= 20
                or any(not isinstance(v, str) or not v.strip() or len(v) > 1000
                       or any(ord(c) < 32 for c in v) for v in values)):
            raise ValueError('Invalid task ' + key)
    return task


def configured(config, scope, checkout):
    """Separate from general operator authority. Same-account cooperative policy."""
    policy = config.get('task_registration', {})
    roots = policy.get('checkout_roots', {}).get(scope, [])
    if not roots:
        raise ValueError('Task registration is not configured for this scope')
    root = Path(checkout['root']).resolve()
    if not any(Path(r).is_absolute() and root.is_relative_to(Path(r).resolve()) for r in roots):
        raise ValueError('Checkout is outside this scope\'s registration roots')
    entries = [e for e in config['scopes'] if e['id'] == scope]
    if len(entries) != 1 or entries[0]['provider']['kind'] != 'itsaplan':
        raise ValueError('Exactly one writable provider is required for scope')
    if not policy.get('journal_directory') or not config.get('operator', {}).get('journal_directory'):
        raise ValueError('Registration and reconciliation journal directories required')
    if Path(policy['journal_directory']).resolve() == Path(config['operator']['journal_directory']).resolve():
        raise ValueError('Registration and reconciliation journals must use distinct lock directories')
    return entries[0], OperatorProvider(entries[0]['provider'])


def inventory_digest(scope, task, native_identifier, rows):
    # Bind review to the exact task and target as well as native inventory.
    return digest({'scope': scope, 'task': task, 'native_identifier': native_identifier,
                   'inventory': sorted(rows, key=lambda r: r['identifier'])})


def refresh(entry, provider, identifier, alias):
    try:
        snapshot = validate_snapshot(provider.snapshot())
        if snapshot.get('scope_id', entry['id']) != entry['id']:
            raise ValueError('Snapshot scope binding differs')
        if not any(r['id'] == alias and r.get('provider_identifier') == identifier
                   and r['kind'] == 'workstream' for r in snapshot['records']):
            raise ValueError('Registered task not yet visible in snapshot')
        snapshot['scope_id'] = entry['id']
        write_json(entry['cache'], snapshot)
    except (OSError, ValueError, KeyError, TypeError, StopIteration):
        return {'state': 'registered-refresh-pending', 'identifier': identifier, 'workstream': alias,
                'next_step': 'Retry the same task-register submission to refresh; do not create another task.'}
    return {'state': 'registered', 'scope': entry['id'], 'identifier': identifier, 'workstream': alias,
            'next_step': 'Run onboard with this exact scope/workstream, inspect context, then enroll your own session.',
            'meaning': 'Durable task recorded; no session enrollment, ownership transfer, execution or readiness grant.'}


def register(config, scope, task, checkout_path=None, submit=False, reviewed_digest=None,
             native_identifier=None):
    task = validate_task(task)
    checkout = checkout_identity(checkout_path or Path.cwd())
    entry, provider = configured(config, scope, checkout)
    key = digest({'scope': scope, 'title': ' '.join(task['title'].casefold().split())})
    alias = 'TASK-' + key[:20].upper()
    if not submit:
        rows = provider.inventory()
        return {'state': 'preview', 'scope': scope, 'checkout': checkout, 'inventory': rows,
               'inventory_digest': inventory_digest(scope, task, native_identifier, rows),
               'proposed_workstream': alias,
               'next_step': 'Review all native candidates against the user task and owners. If one fits, set --native-identifier and preview again. Otherwise submit with --inventory-digest from this preview.',
               'meaning': 'Read-only preview. authority_ref is a worker assertion of existing user authorization, not proof or new authority.'}
    journal = Path(config['task_registration']['journal_directory'])
    request = {'scope': scope, 'task': task, 'native_identifier': native_identifier}
    # Serialize local registrations across checkouts/sessions. Reconcile separately
    # shares the existing operator journal lock. This is not distributed CAS.
    with locked(journal):
        file = journal / (key + '.json')
        if file.is_symlink():
            raise ValueError('Symlink task receipt refused')
        prior = read_json(file) if file.exists() else None
        if prior:
            if prior['request'] != request:
                raise ValueError('This title has a prior registration request; inspect/retry its original packet or use operator reconciliation')
            receipt = prior.get('result')
            if receipt:
                return refresh(entry, provider, receipt['identifier'], receipt['workstream'])
            packet = prior['packet']
            # A crash can occur after reconcile publishes its receipt but before
            # this wrapper saves its result. Recover that receipt, never replay a
            # successful metadata operation or recreate a now-hidden/deleted issue.
            native_receipt = Path(config['operator']['journal_directory']) / (digest(packet) + '.json')
            if native_receipt.is_symlink():
                raise ValueError('Symlink reconciliation receipt refused')
            outcome = read_json(native_receipt) if native_receipt.exists() else {}
            if outcome.get('state') == 'published':
                receipt = {'identifier': outcome['identifier'], 'workstream': packet['record']['id']}
                write_json(file, {**prior, 'result': receipt})
                return refresh(entry, provider, receipt['identifier'], receipt['workstream'])
        rows = provider.inventory()
        if reviewed_digest != inventory_digest(scope, task, native_identifier, rows):
            raise ValueError('Native inventory/task changed or review missing; preview and inspect again')
        if not prior:
            matches = [r for r in rows if r['identifier'] == native_identifier] if native_identifier else [
                r for r in rows if ' '.join(r['title'].casefold().split()) == ' '.join(task['title'].casefold().split())
                or (r['record'] or {}).get('id') == alias]
            if native_identifier and len(matches) != 1:
                raise ValueError('Selected native issue absent or ambiguous')
            if not native_identifier and matches:
                raise ValueError('Existing native candidate found; preview with its --native-identifier before submission')
            record = {'id': alias, 'kind': 'workstream', 'revision': '1', 'state': 'active',
                      **{k: task[k] for k in ('statement', 'scope', 'acceptance', 'boundaries', 'avoid')},
                      'authority_ref': task['authority_ref'], 'source_checkout': checkout['root'],
                      'branch': checkout['branch'],
                      'readiness': {k: 'unknown' for k in ('implementation', 'review', 'ci', 'merge', 'production')}}
            packet = {'scope': scope, 'confirmed': True, 'title': task['title'],
                      'expected_digest': digest(None), 'record': record}
            if native_identifier:
                selected = matches[0]
                if selected['record'] is not None:
                    if selected['record'].get('kind') != 'workstream':
                        raise ValueError('Selected native record is not a workstream')
                    # Reuse without replacing scope, evidence, owners or readiness.
                    write_json(file, {'request': request, 'result': {
                        'identifier': selected['identifier'], 'workstream': selected['record']['id']}})
                    return refresh(entry, provider, selected['identifier'], selected['record']['id'])
                packet['native_identifier'] = native_identifier
            # Persist exact original bytes before any provider mutation. Retries
            # from a new branch/HEAD/session must not generate a new operation.
            write_json(file, {'request': request, 'packet': packet})
        result = reconcile(provider, scope, packet, config['operator']['journal_directory'],
                           expected_inventory_digest=digest(sorted(rows, key=lambda r: r['identifier'])))
        if result['state'] != 'published':
            return {**result, 'next_step': 'Preview fresh inventory with the identical task packet/target before retry. If still uncertain, reconcile the native receipt through the operator; do not rename/recreate the task.'}
        write_json(file, {'request': request, 'packet': packet, 'result': {
            'identifier': result['identifier'], 'workstream': packet['record']['id']}})
        return refresh(entry, provider, result['identifier'], packet['record']['id'])
