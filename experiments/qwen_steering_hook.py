"""Opt-in native Qwen hook: bounded observations, never assignments or repairs."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time

EVENTS = ('UserPromptSubmit', 'PostToolUse', 'PostToolUseFailure')
MAX_NOTICES = 12


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def file_digest(root, name):
    path = root / name
    if Path(name).is_absolute() or '..' in Path(name).parts or path.resolve().parent != root:
        raise ValueError('Only frozen checkout-root source files are observed')
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return 'missing'
    with os.fdopen(fd, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError('Regular source file required')
        raw = stream.read(1048577)
    if len(raw) > 1048576:
        raise ValueError('Source file exceeds observation bound')
    return hashlib.sha256(raw).hexdigest()


def context(config, session):
    result = subprocess.run([
        '/usr/bin/python3', '-B', '-I', str(Path(__file__).parent / 'project_intent/_worker_cli.py'),
        '--worker-config', '.pi/worker.json', '--scope', config['scope'],
        'start', '--workstream', config['sessions'][session], '--session', session],
        cwd=config['checkout'], capture_output=True, text=True, timeout=4)
    if result.returncode:
        raise ValueError('PI context unavailable')
    value = json.loads(result.stdout)['integration_context']
    return {
        'related_tasks': [{
            'id': row['id'], 'statement': (row.get('statement') or '')[:400],
            'shared_seams': row.get('shared_seams', [])[:12]
        } for row in value['related_work'][:4]],
        'workers': [{key: row.get(key) for key in ('session', 'workstream', 'observation')}
                    | {'working': (row.get('working') or '')[:240]}
                    for row in value['last_known_workers'][:4]],
        'omitted_tasks': max(0, len(value['related_work']) - 4),
        'omitted_workers': max(0, len(value['last_known_workers']) - 4)}


def notice(state, current, declared):
    changed = sorted(name for name, value in current.items() if state['files'].get(name) != value)
    context_changed = state.get('context') != digest(declared)
    initial = not state.get('initialized')
    state.update(files=current, context=digest(declared), initialized=True)
    if not (initial or changed or context_changed):
        return None
    if state.get('notices', 0) >= MAX_NOTICES:
        state['suppressed'] = state.get('suppressed', 0) + 1
        return None
    state['notices'] = state.get('notices', 0) + 1
    packet = {'source': 'PI steering observation/v1', 'source_changes': changed[:16],
              'omitted_paths': max(0, len(changed) - 16),
              'attribution': 'Observed checkout differences; author and semantic impact unverified.'}
    if initial or context_changed:
        packet['declarations'] = declared
    message = ('PI update: inspect changed source and affected callers; validate combined behavior. '
               'Related assignments are not edit prohibitions. Follow existing scope and repair agreement; '
               'this notice grants no authority and is not an acceptance result. Data follows:\n'
               + json.dumps(packet, ensure_ascii=True))
    if len(message) > 6000:
        raise ValueError('Notice exceeds context bound')
    return message


def handle(config, event, directory, context_reader=context):
    if not config.get('enabled'):
        return {}
    session = event.get('session_id')
    root = Path(config['checkout']).resolve(strict=True)
    if (session not in config['sessions'] or event.get('hook_event_name') not in EVENTS
            or Path(event.get('cwd', '')).resolve() != root
            or os.environ.get('QWEN_SESSION_ID') != session):
        raise ValueError('Hook session/checkout/event binding mismatch')
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    if directory.is_symlink():
        raise ValueError('Regular hook state directory required')
    lock = os.open(directory / 'lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    started = time.monotonic()
    with os.fdopen(lock, 'w') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        path = directory / 'state.json'
        if path.is_symlink() or (directory / 'events.jsonl').is_symlink():
            raise ValueError('Regular hook state files required')
        state = json.loads(path.read_text()) if path.exists() else {'files': config['baseline']}
        if state.get('session', session) != session:
            raise ValueError('Hook state belongs to another session')
        state['session'] = session
        current = {name: file_digest(root, name) for name in config['baseline']}
        # Never read evaluator outputs, transcripts, task-role text files, or tool output.
        declared = context_reader(config, session)
        message = notice(state, current, declared)
        path.write_text(json.dumps(state))
        with (directory / 'events.jsonl').open('a') as journal:
            journal.write(json.dumps({'at': time.time(), 'session': session,
                'event': event['hook_event_name'], 'tool_use_id': event.get('tool_use_id'),
                'emitted': message is not None, 'message': message,
                'suppressed': state.get('suppressed', 0),
                'elapsed_seconds': time.monotonic() - started}) + '\n')
    return {'hookSpecificOutput': {'hookEventName': event['hook_event_name'],
                                  'additionalContext': message}} if message else {}


def main():
    try:
        config = json.loads(Path(__file__).with_name('steering.json').read_text())
        raw = sys.stdin.buffer.read(2097153)
        if len(raw) > 2097152:
            raise ValueError('Hook input exceeds bound')
        event = json.loads(raw)
        result = handle(config, event, Path.home() / '.qwen/pi-steering')
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        # Fail open without blocking native work, but leave diagnostic evidence.
        print('PI steering unavailable: ' + type(error).__name__, file=sys.stderr)
        result = {}
    print(json.dumps(result))


if __name__ == '__main__':
    main()
