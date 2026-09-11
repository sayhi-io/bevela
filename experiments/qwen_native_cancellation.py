"""Recognize only corroborated native Qwen 15-minute stream cancellations.

Read-only evidence classification, never request retrying or worker feedback.
"""
from datetime import datetime
import json
import re

from experiments import qwen_distributed_study as study


def seconds(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()


def match(error, transport, telemetry, events, session, model):
    if error.get('type') not in ('BrokenPipeError', 'ConnectionResetError'):
        return None
    request = error['request']
    response = next((r for r in transport if r['event'] == 'response'
        and r['request'] == request and r.get('status') == 200), None)
    start = next((r for r in transport if r['event'] == 'request' and r['request'] == request), None)
    if not response or not start:
        return None
    ended = seconds(error['at'])
    # An overlapping or unclosed prior request makes attribution ambiguous.
    for other in transport:
        if other['event'] != 'request' or other['request'] == request or seconds(other['at']) >= ended:
            continue
        finished_before = any(r['event'] in ('usage', 'transport_error')
            and r['request'] == other['request'] and seconds(r['at']) <= seconds(start['at'])
            for r in transport)
        if not finished_before:
            return None
    candidates = []
    for row in telemetry:
        event = row.get('systemPayload', {}).get('uiEvent', {})
        if (row.get('sessionId') != session or row.get('type') != 'system'
                or row.get('subtype') != 'ui_telemetry'
                or event.get('event.name') != 'qwen-code.api_error'
                or event.get('error_type') != 'StreamLifetimeExceededError'
                or event.get('model') != model
                or not event.get('prompt_id', '').startswith(session + '########')
                or not re.match(r'^Stream exceeded its 900000ms upstream-wait cap after [1-9][0-9]* chunks ', event.get('error_message', ''))):
            continue
        failed = seconds(event['event.timestamp'])
        duration = event.get('duration_ms', 0) / 1000
        if not (0 <= ended - failed <= 2 and 900 <= duration <= 1800
                and abs(failed - seconds(start['at']) - duration) <= 5
                and seconds(response['at']) < failed):
            continue
        retry = [r for r in events if r.get('event', {}).get('type') == 'system'
            and r['event'].get('subtype') == 'retry' and r['event'].get('session_id') == session
            and 0 <= seconds(r['at']) - failed <= 2]
        live = any(r['event'] == 'reasoning_observed' and r['request'] == request
            and 0 <= failed - seconds(r['at']) <= 2 for r in transport)
        if len(retry) != 1:
            continue
        followups = [r for r in transport if r['event'] == 'request' and r['request'] == request + 1
            and seconds(retry[0]['at']) <= seconds(r['at']) <= failed + 30]
        recovered = any(r['event'] == 'response' and r.get('status') == 200
            and any(r['request'] == follow['request'] for follow in followups)
            and seconds(r['at']) > failed for r in transport)
        if live and len(followups) == 1 and recovered:
            candidates.append({'request': request, 'native_error_at': event['event.timestamp'],
                'native_error_type': event['error_type'], 'duration_ms': event['duration_ms'],
                'transport_error_at': error['at'], 'transport_error_type': error['type'], 'native_retry_at': retry[0]['at'],
                'followup_request': followups[0]['request']})
    return candidates[0] if len(candidates) == 1 else None


def inspect(root, role, session, model, transport):
    paths = list((root / 'qwen-home' / role / 'projects').glob('*/chats/' + session + '.jsonl'))
    if len(paths) != 1:
        return {'matches': [], 'profile_sha256': None}
    telemetry = [json.loads(line) for line in paths[0].read_text().splitlines()]
    events_path = root / role / 'events.jsonl'
    events = [json.loads(line) for line in events_path.read_text().splitlines()]
    matches = [found for error in transport if error['event'] == 'transport_error'
               if (found := match(error, transport, telemetry, events, session, model))]
    for key in ('native_error_at', 'native_retry_at', 'followup_request', 'request'):
        if len({row[key] for row in matches}) != len(matches):
            matches = []
            break
    return {'matches': matches, 'profile_sha256': study.sha(paths[0]),
        'native_events_sha256': study.sha(events_path), 'classifier_sha256': study.sha(__file__)}
