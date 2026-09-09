"""Bounded local repair coordination, not file locking or PM ownership.

Only cooperating workers sharing a scope feed participate. A lost lease does not
fence filesystem writes, so it never authorizes automatic repair takeover.
"""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import uuid

from .enrollment import SAFE_SESSION
from .model import date, utcnow, valid_presence
from .runtime import write_json
from .worker_context import path_overlap, relative_paths, same_repository

MAX_RECORDS = 128
MEANING = ('Cooperative repair responsibility only, not edit permission, a filesystem lock, '
           'peer liveness or independently verified correctness. No automatic takeover on expiry.')


def _read(path):
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError('Regular repair/registration file required')
        raw = stream.read(65537)
    if len(raw) > 65536:
        raise ValueError('Repair/registration exceeds 64 KiB')
    return json.loads(raw)


def _directory(directory):
    path = Path(directory) / 'repairs'
    if path.is_symlink():
        raise ValueError('Refusing symlink repair directory')
    return path


def _files(directory):
    # Path.glob can silently turn permission errors into an empty inventory.
    # An unreadable existing claim must never become permission for a second one.
    try:
        with os.scandir(directory) as entries:
            return sorted(Path(entry.path) for entry in entries if entry.name.endswith('.json'))
    except FileNotFoundError:
        return []


def _records(directory, scope, checkout):
    files = _files(directory)
    if len(files) > MAX_RECORDS:
        raise ValueError('Repair inventory over limit; reconcile before claiming')
    records = []
    for path in files:
        row = _read(path)
        if (row.get('version') not in (1, 2) or row.get('state') not in ('awaiting-ack', 'claimed', 'open', 'resolved')
                or row.get('key') != path.stem):
            raise ValueError('Invalid repair record; coordination unavailable')
        if row['scope'] == scope and same_repository(row['checkout'], checkout):
            records.append(row)
    return records


def _fingerprints(checkout, paths):
    paths = relative_paths(paths)
    if not paths or len(paths) > 32:
        raise ValueError('Supply 1–32 explicit --check-path files covering producer, consumers and checks')
    root = Path(checkout['root']).resolve(strict=True)
    result = {}
    for name in paths:
        path = root / name
        if name == '.' or any(p.is_symlink() for p in [path, *path.parents] if p != root and p.is_relative_to(root)):
            raise ValueError('Evidence must use regular checkout files, not symlinks/directories')
        if not path.resolve(strict=True).is_relative_to(root):
            raise ValueError('Evidence file escapes checkout')
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
        with os.fdopen(fd, 'rb') as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise ValueError('Regular evidence file required')
            raw = stream.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise ValueError('Evidence source file exceeds 2 MiB')
        result[name] = hashlib.sha256(raw).hexdigest()
    return result


def _check_repair_paths(checkout, paths):
    # Claims compare lexical paths. Refuse aliases that would bypass that
    # comparison and give two repairers the same physical file.
    root = Path(checkout['root']).resolve(strict=True)
    for name in paths:
        path = root / name
        if any(p.is_symlink() for p in [path, *path.parents] if p != root and p.is_relative_to(root)):
            raise ValueError('Repair paths/ancestors cannot be symlinks; use the actual checkout path')
        try:
            info = path.stat()
        except FileNotFoundError:
            continue  # An agreed repair may create a file.
        if stat.S_ISREG(info.st_mode) and info.st_nlink > 1:
            raise ValueError('Hard-linked repair files need alias reconciliation before claiming')


def _view(row, directory, checkout, verify=True):
    result = dict(row)
    result.pop('claim_id', None)  # Only the owner obtains its mutation token.
    result['meaning'] = MEANING
    result['repair_id'] = row['key']
    result['agreement'] = ('legacy-unacknowledged' if row['version'] == 1 else
        'awaiting-peer' if row['state'] == 'awaiting-ack' else
        'acknowledged' if row.get('acknowledgments') else 'not-agreed')
    result['pending_peers'] = sorted(set(row.get('peers', {})) - set(row.get('acknowledgments', {})))
    result['owner_observation'] = 'unknown'
    try:
        owner = _read(Path(directory) / (row['owner_session'] + '.json'))
        if (owner.get('scope'), owner.get('workstream'), owner.get('claimed_at')) == (
                row['scope'], row['owner_workstream'], row['enrollment_claimed_at']):
            result['owner_observation'] = ('active-lease-not-proof-of-running'
                if owner.get('status') == 'active' and date(owner['expires_at']) > utcnow()
                else 'released-or-expired-no-automatic-takeover')
    except (OSError, ValueError, KeyError, TypeError):
        pass
    if row['state'] == 'resolved':
        result['verification'] = 'different-checkout-not-verified-here'
        if row['checkout']['root'] == checkout['root'] and not verify:
            result['verification'] = 'owner-reported-checks-refresh-with-repair-status'
        elif row['checkout']['root'] == checkout['root']:
            try:
                result['verification'] = ('owner-reported-checks-source-unchanged'
                    if _fingerprints(checkout, row['source_hashes']) == row['source_hashes']
                    else 'source-changed-revalidation-required')
            except (OSError, ValueError, KeyError, TypeError):
                result['verification'] = 'source-unavailable-revalidation-required'
    else:
        result['verification'] = 'unresolved'
    return result


def status(directory, scope, checkout, verify=True):
    if not directory or not checkout:
        return {'coverage': 'unavailable', 'repairs': [], 'meaning': MEANING}
    try:
        rows = _records(_directory(directory), scope, checkout)
        return {'coverage': 'local-cooperative', 'repairs': [_view(r, directory, checkout, verify) for r in rows],
                'meaning': MEANING}
    except (OSError, ValueError, KeyError, TypeError):
        return {'coverage': 'unavailable', 'repairs': [], 'meaning': MEANING,
                'next_step': 'Repair inventory unreadable; do not infer no competing repair.'}


def _actor(directory, scope, session, checkout, workstream=None, active=True):
    if not session or not SAFE_SESSION.fullmatch(session):
        raise ValueError('Own safe --session (or --codex) required')
    actor = _read(Path(directory) / (session + '.json'))
    if (actor.get('version') != 1 or actor.get('scope') != scope or actor.get('session') != session
            or (workstream is not None and actor.get('workstream') != workstream)
            or not valid_presence(actor, utcnow()) or not actor.get('checkout')
            or not same_repository(actor['checkout'], checkout)
            or (workstream is not None and actor['checkout']['root'] != checkout['root'])):
        raise ValueError('Repair requires matching scope, session and checkout enrollment')
    if active and (actor['status'] != 'active' or date(actor['expires_at']) <= utcnow()):
        raise ValueError('Repair agreement requires active enrollment; silence is not acknowledgment')
    return actor


def _binding(actor):
    return {k: actor[k] for k in ('session', 'workstream', 'claimed_at', 'checkout')}


def _same_binding(actor, binding):
    return (actor['session'] == binding['session'] and actor['workstream'] == binding['workstream']
        and actor['claimed_at'] == binding['claimed_at']
        and actor['checkout']['root'] == binding['checkout']['root']
        and same_repository(actor['checkout'], binding['checkout']))


def _claim_view(row, directory, checkout, actor):
    out = _view(row, directory, checkout)
    owned = (row['owner_session'] == actor['session'] and row['owner_workstream'] == actor['workstream']
        and row['checkout']['root'] == checkout['root'] and row['enrollment_claimed_at'] == actor['claimed_at'])
    ready = owned and row['version'] == 2 and row['state'] == 'claimed'
    out.update(accepted=owned and row['state'] in ('awaiting-ack', 'claimed'),
               acquired=ready, ready_to_edit=ready)
    if owned and row['state'] in ('awaiting-ack', 'claimed'):
        out['claim_id'] = row['claim_id']
    out['next_step'] = ('Agreed repairer: reread current code, repair only these paths, then validate the agreed files.' if ready else
        'Owner accepted; named peers must repair-ack this repair_id and plan revision before repair edits.' if owned and row['state'] == 'awaiting-ack' else
        'Inspect this specific repair plan. If you are a named peer, explicitly repair-ack its revision; do not duplicate these edits. Unrelated paths remain independent.')
    return out


def change(directory, snapshot, workstream, session, checkout, action, seam=None,
           paths=(), claim_id=None, evidence='', check_paths=(), expected_revision=None,
           repair_id=None, problem='', peer_sessions=()):
    if not directory or not session or not SAFE_SESSION.fullmatch(session):
        raise ValueError('Repair mutation requires enrollment directory and own safe --session (or --codex)')
    work = next(r for r in snapshot['records'] if r['kind'] == 'workstream' and r['id'] == workstream)
    scope = snapshot['scope_id']
    directory = Path(directory)
    target = _directory(directory)
    target.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(target / 'coordination.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    with os.fdopen(fd, 'w') as lock:
        if not stat.S_ISREG(os.fstat(lock.fileno()).st_mode):
            raise ValueError('Regular coordination lock required')
        fcntl.flock(lock, fcntl.LOCK_EX)
        rows = _records(target, scope, checkout)
        row = next((r for r in rows if r['key'] == repair_id), None) if repair_id else None
        if repair_id and not row:
            raise ValueError('Repair absent from this scope/repository')
        if not row and claim_id:
            row = next((r for r in rows if r.get('claim_id') == claim_id), None)
        owner = _actor(directory, scope, session, checkout, workstream, active=action != 'release')
        if action in ('claim', 'complete') and owner.get('access') != 'edit':
            raise ValueError('Edit enrollment required for repair ownership')
        if action == 'claim':
            if seam not in work['boundaries']:
                raise ValueError('Use an exact assignment seam for context, not as a repair lock')
            paths = relative_paths(paths)
            if not paths or '.' in paths or len(paths) > 32 or any(len(p) > 500 for p in paths):
                raise ValueError('Claim explicit affected --repair-path files/directories, not the whole checkout')
            _check_repair_paths(checkout, paths)
            if len(evidence) > 2000:
                raise ValueError('Keep repair evidence/reason within 2000 characters')
            if any(path_overlap(p, q) for p in paths for q in owner.get('avoid_paths', [])):
                raise ValueError('Repair paths intersect your explicit exclusions; resolve authority first')
            conflict = next((r for r in rows if r['state'] in ('awaiting-ack', 'claimed') and
                (r['key'] == repair_id or any(path_overlap(p, q) for p in paths for q in r['paths']))), None)
            if conflict:
                result = _claim_view(conflict, directory, checkout, owner)
                if result['accepted'] and (paths != conflict['paths'] or (problem and problem != conflict.get('problem'))
                        or (check_paths and relative_paths(check_paths) != conflict.get('check_paths'))
                        or (peer_sessions and sorted(set(peer_sessions)) != sorted(conflict.get('peers', {})))):
                    raise ValueError('Accepted plan differs; stop/release before proposing a changed plan')
                return result
            if not row:
                row = next((r for r in rows if r['version'] == 2 and r['paths'] == paths), None)
            if row and row['state'] == 'resolved':
                view = _view(row, directory, checkout)
                if expected_revision is not None:
                    if expected_revision != row['revision'] or not evidence.strip() or len(evidence) > 2000:
                        raise ValueError('Reopen requires the current --expected-revision and bounded --evidence of a new/unresolved failure')
                elif view['verification'] not in ('source-changed-revalidation-required', 'source-unavailable-revalidation-required'):
                    return dict(view, acquired=False, next_step='Inspect the existing repair and evidence; do not apply a second fix. If a real failure remains, reclaim with its --expected-revision and --evidence.')
            elif expected_revision is not None:
                raise ValueError('Explicit reopen requires a resolved repair at the inspected revision')
            if row and row['version'] != 2:
                raise ValueError('Legacy repair has no peer agreement; reconcile with its original CLI before replacing it')
            checks = relative_paths(check_paths)
            peers = sorted(set(peer_sessions))
            if not problem.strip() or len(problem) > 2000:
                raise ValueError('Describe the specific break and expected result with --problem')
            if len(checks) < 2 or len(checks) > 32 or '.' in checks or any(len(p) > 500 for p in checks):
                raise ValueError('Agree on 2–32 --check-path files covering affected producer and consumer')
            if any(not any(path_overlap(p, q) for q in checks) for p in paths):
                raise ValueError('Agreed check paths must cover every repair path')
            if not peers or len(peers) > 8 or session in peers:
                raise ValueError('Name 1–8 other affected workers with --peer-session; you cannot acknowledge yourself')
            bindings = {}
            known = {r['id'] for r in snapshot['records'] if r['kind'] == 'workstream'}
            for peer in peers:
                record = _actor(directory, scope, peer, checkout)
                if record['workstream'] not in known:
                    raise ValueError('Peer workstream absent from scoped inventory')
                bindings[peer] = _binding(record)
            if not row and len(_files(target)) >= MAX_RECORDS:
                raise ValueError('Repair inventory full; reconcile before claiming')
            key = row['key'] if row else uuid.uuid4().hex
            row = {'version': 2, 'key': key, 'scope': scope, 'seam': seam, 'checkout': checkout,
                   'state': 'awaiting-ack', 'owner_session': session, 'owner_workstream': workstream,
                   'enrollment_claimed_at': owner['claimed_at'], 'claim_id': uuid.uuid4().hex,
                   'paths': paths, 'problem': problem, 'check_paths': checks,
                   'peers': bindings, 'acknowledgments': {},
                   'reason': evidence, 'revision': (row or {}).get('revision', 0) + 1,
                   'updated_at': utcnow().isoformat()}
        elif action == 'ack':
            if (not row or row['version'] != 2 or row['state'] not in ('awaiting-ack', 'claimed')
                    or expected_revision != row['revision'] or session not in row['peers']
                    or not _same_binding(owner, row['peers'][session])):
                raise ValueError('Only the named peer may acknowledge the exact current repair_id and plan revision')
            if len(evidence) > 2000:
                raise ValueError('Keep acknowledgment evidence bounded')
            row['acknowledgments'].setdefault(session, {'at': utcnow().isoformat(), 'note': evidence})
            if set(row['acknowledgments']) == set(row['peers']):
                row['state'] = 'claimed'
            row['updated_at'] = utcnow().isoformat()
        elif action in ('complete', 'release'):
            if (not row or row['version'] != 2 or row['state'] not in ('awaiting-ack', 'claimed') or not claim_id or row['claim_id'] != claim_id
                    or row['owner_session'] != session or row['owner_workstream'] != workstream
                    or row['checkout']['root'] != checkout['root']):
                raise ValueError('Only the recorded owner with the current --claim-id may finish/release this repair')
            if action == 'complete':
                _check_repair_paths(checkout, row['paths'])
                if row['seam'] not in work['boundaries']:
                    raise ValueError('Assignment boundary changed; reconcile or release the accepted repair')
                if row['state'] != 'claimed' or set(row['acknowledgments']) != set(row['peers']):
                    raise ValueError('Peer acknowledgment pending; accepting responsibility is not agreement')
                if row['enrollment_claimed_at'] != owner['claimed_at']:
                    raise ValueError('Enrollment lapsed; explicitly release the old repair before reclaiming')
                if not evidence.strip() or len(evidence) > 2000:
                    raise ValueError('Supply bounded --evidence describing actual cross-seam checks and results')
                if check_paths and relative_paths(check_paths) != row['check_paths']:
                    raise ValueError('Completion cannot change the acknowledged validation scope')
                hashes = _fingerprints(checkout, row['check_paths'])
                row.update(state='resolved', evidence=evidence, source_hashes=hashes)
            else:
                row.update(state='open')
            row.update(revision=row['revision'] + 1, updated_at=utcnow().isoformat())
        else:
            raise ValueError('Unknown repair action')
        if len(json.dumps(row).encode()) > 65536:
            raise ValueError('Repair exceeds 64 KiB; keep paths/evidence bounded')
        write_json(target / (row['key'] + '.json'), row)
        result = _view(row, directory, checkout)
        if action == 'claim':
            return _claim_view(row, directory, checkout, owner)
        return result
