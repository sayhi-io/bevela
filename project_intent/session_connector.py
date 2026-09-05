"""Provisional local operator adapter. No scheduler, fleet admission, or HTTP writes."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from datetime import timedelta
from typing import Protocol
from uuid import UUID

from .model import utcnow, date
from .worker_context import checkout_identity


class Backend(Protocol):
    def deliver(self, session: str, checkout: str, message: str, mode: str) -> dict: ...


class CodexBackend:
    def deliver(self, session, checkout, message, mode):
        argv = (['codex', 'queue', '--thread', session, '--message', message] if mode == 'queue'
                else ['codex', 'exec', 'resume', '--json', session, '-'])
        try:
            # Child output may contain conversation text: private temporary storage,
            # bounded reads, no raw output persisted in receipts or printed to users.
            with tempfile.TemporaryFile(mode='w+b') as output, tempfile.TemporaryFile(mode='w+b') as errors:
                result = subprocess.run(argv, cwd=checkout, input=message if mode == 'resume' else None,
                                        stdout=output, stderr=errors, text=True,
                                        timeout=45 if mode == 'queue' else 300)
                output.seek(0)
                captured = output.read(65537)
                if len(captured) > 65536:
                    return {'status': 'uncertain', 'execution': 'unknown', 'reason': 'Output exceeds receipt bound; inspect target'}
                # Mock backends may provide stdout directly; real run writes output.
                result.stdout = captured.decode('utf-8', errors='replace') or getattr(result, 'stdout', '') or ''
        except FileNotFoundError:
            return {'status': 'unavailable', 'execution': 'not-started'}
        except (subprocess.TimeoutExpired, OSError):
            return {'status': 'uncertain', 'execution': 'unknown', 'reason': 'Transport interrupted; inspect target before any new request'}
        if mode == 'queue':
            match = re.fullmatch(r'Queued message ([0-9a-f-]{36}) for thread ' + re.escape(session) + r'\.', result.stdout.strip())
            if result.returncode == 0 and match:
                return {'status': 'queued', 'message_id': match[1], 'execution': 'unconfirmed'}
        else:
            events = []
            for line in result.stdout.splitlines():
                try: events.append(json.loads(line))
                except ValueError: pass
            exact = any(e.get('type') == 'thread.started' and e.get('thread_id') == session for e in events if isinstance(e, dict))
            completed = any(e.get('type') == 'turn.completed' for e in events if isinstance(e, dict))
            if exact and result.returncode == 0 and completed:
                return {'status': 'turn-completed', 'execution': 'observed-complete', 'acceptance': 'not-assessed'}
        return {'status': 'uncertain', 'execution': 'unknown', 'exit_code': result.returncode,
                'reason': 'No exact delivery receipt; inspect target. No automatic resume/queue fallback.'}


def private_json(path):
    path = Path(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd) as stream:
        stat = os.fstat(stream.fileno())
        if stat.st_uid != os.getuid() or stat.st_mode & 0o077:
            raise ValueError('Connector state/config must be private and owned by the local operator')
        return json.load(stream)


def save(path, data):
    temporary = path.with_suffix('.tmp')
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(data, stream, sort_keys=True, indent=2)
        stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)


def authority(config_path, scope, workstream, session, checkout):
    session = str(UUID(session))
    cfg = private_json(config_path)
    root = checkout_identity(checkout)['root']
    target = {'scope': scope, 'workstream': workstream, 'session': session, 'checkout': root}
    matches = [t for t in cfg.get('allowed_targets', []) if all(t.get(k) == v for k, v in target.items())]
    if len(matches) != 1 or not cfg.get('authority_ref') or not cfg.get('operator'):
        raise ValueError('Exact target is not authorized in private local operator configuration')
    cfg['target_origin_cwd'] = matches[0].get('session_origin_cwd', root)
    directory = Path(cfg['state_directory'])
    if not directory.is_absolute() or directory.is_symlink(): raise ValueError('Use an absolute private state directory')
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    stat = directory.stat()
    if stat.st_uid != os.getuid() or stat.st_mode & 0o077: raise ValueError('Connector directory must be private')
    return cfg, target, directory


def attach(config_path, scope, workstream, session, checkout, rollout):
    cfg, target, directory = authority(config_path, scope, workstream, session, checkout)
    # Read only the explicitly supplied session header, never its conversation.
    fd = os.open(rollout, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd) as stream:
        line = stream.readline(65537)
    if len(line) > 65536: raise ValueError('Oversized session header')
    header = json.loads(line)
    metadata = header.get('payload', {})
    if header.get('type') != 'session_meta' or metadata.get('id') != target['session']:
        raise ValueError('Explicit rollout does not identify the exact target session')
    if Path(metadata.get('cwd', '')).resolve() != Path(cfg['target_origin_cwd']).resolve():
        raise ValueError('Session header checkout differs; reconcile explicitly before attachment')
    record = dict(target, session_origin_cwd=str(Path(metadata['cwd']).resolve()), checkout_identity=checkout_identity(checkout), operator=cfg['operator'], authority_ref=cfg['authority_ref'], attached_at=utcnow().isoformat(), expires_at=(utcnow()+timedelta(hours=1)).isoformat(),
                  meaning='Local operator attachment only; no PM ownership or live lease grant')
    save(directory / (target['session'] + '.attachment.json'), record)
    return record


def continue_session(config_path, scope, workstream, session, checkout, request_id, message, mode='queue', backend=None):
    cfg, target, directory = authority(config_path, scope, workstream, session, checkout)
    if mode not in ('queue', 'resume'): raise ValueError('Choose explicit queue or resume delivery')
    if mode == 'resume' and session == os.environ.get('CODEX_THREAD_ID'):
        raise ValueError('Cannot recursively resume the current session; use queue for an authorized existing writer')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}', request_id or ''): raise ValueError('Invalid request ID')
    if not isinstance(message, str) or not message.strip() or len(message.encode()) > 32768: raise ValueError('Message must be nonempty and at most 32 KiB')
    attachment = private_json(directory / (target['session'] + '.attachment.json'))
    if any(attachment.get(k) != v for k, v in target.items()) or attachment.get('authority_ref') != cfg['authority_ref']:
        raise ValueError('Attachment does not match authorized scope/workstream/checkout; attach explicitly')
    if date(attachment.get('expires_at')) <= utcnow() or attachment.get('session_origin_cwd') != str(Path(cfg['target_origin_cwd']).resolve()):
        raise ValueError('Attachment expired or origin changed; attach explicitly')
    current = checkout_identity(checkout)
    if any(attachment.get('checkout_identity', {}).get(k) != current[k] for k in ('root', 'host', 'repository_common_dir')):
        raise ValueError('Execution checkout identity changed; attach explicitly')
    digest = hashlib.sha256(json.dumps(dict(target, message=message, mode=mode), sort_keys=True).encode()).hexdigest()
    receipt_path = directory / (request_id + '.receipt.json')
    fd = os.open(directory / '.dispatch.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if receipt_path.exists():
            receipt = private_json(receipt_path)
            if receipt.get('request_digest') != digest: raise ValueError('Request ID already used for different content/target')
            return dict(receipt, duplicate=True)
        receipt = dict(target, request_id=request_id, request_digest=digest, status='uncertain', execution='unknown',
                       requested_at=utcnow().isoformat(), authority_ref=cfg['authority_ref'])
        # Persist before launch: crash/timeout never authorizes automatic redelivery.
        save(receipt_path, receipt)
        receipt.update((backend or CodexBackend()).deliver(session, target['checkout'], message, mode))
        receipt['observed_at'] = utcnow().isoformat()
        save(receipt_path, receipt)
        return receipt


def add_arguments(parser):
    parser.add_argument('--connector-config', help='Private local operator target allowlist')
    parser.add_argument('--rollout', help='Explicit target rollout: attachment reads its header only')
    parser.add_argument('--request-id', help='Stable idempotency key; reuse for retries')
    parser.add_argument('--message-file', help='UTF-8 bounded continuation; do not put credentials here')
    parser.add_argument('--delivery', choices=['queue', 'resume'], default='queue')


def dispatch(args):
    # CLI must resolve the selected enrolled assignment before calling this adapter.
    if not all((args.connector_config, args.scope, args.workstream, args.session, args.checkout)):
        raise ValueError('--connector-config --scope --workstream --session --checkout required')
    common = (args.connector_config, args.scope, args.workstream, args.session, args.checkout)
    if args.command == 'session-attach':
        if not args.rollout: raise ValueError('--rollout required')
        return attach(*common, args.rollout)
    if not args.message_file: raise ValueError('--message-file required')
    with open(args.message_file) as stream: message = stream.read(32769)
    context = getattr(args, 'intent_context', None)
    if context:
        bounded = {k: context.get(k) for k in ('id', 'revision', 'scope', 'avoid', 'acceptance', 'boundaries', 'claims', 'environment')}
        message = ('Project Intent last-known assignment context (not an authority grant):\n'
                   + json.dumps(bounded, sort_keys=True) + '\n\nBounded continuation:\n' + message)
    message = 'Designated task checkout: ' + args.checkout + '\nQueue delivery does not change the existing session working directory.\n' + message
    return continue_session(*common, args.request_id, message, args.delivery)
