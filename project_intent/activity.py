"""Optional local numeric telemetry. Explicit session bindings; no log text export."""
import json
import os
from pathlib import Path
import stat
from datetime import datetime, timezone

TAIL_BYTES = 2 * 1024 * 1024


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Timezone required')
    return parsed.timestamp()


def codex_activity(binding, now=None):
    """Observed output deltas per wall-clock interval, not generation throughput.

    Codex output_tokens is used alone: reasoning counters are NOT added to it.
    This adapter is provisional for the inspected local rollout format.
    """
    now = now if now is not None else datetime.now(timezone.utc).timestamp()
    result = {'session': binding['session'], 'source': 'codex-local-usage',
              'status': 'unavailable', 'unit': 'reported output tokens/s',
              'window_seconds': 900, 'points': [], 'last_report_at': None,
              'meaning': 'Counter delta / reporting interval; not instantaneous inference speed. Missing reports are unknown.'}
    try:
        if binding.get('kind') != 'codex-local-usage':
            return result
        start = timestamp(binding['since'])
        path = Path(binding['path'])
        if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):
            return result
        with path.open('rb') as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                return result
            header = json.loads(stream.readline(1024 * 1024))
            if header.get('type') != 'session_meta' or header.get('payload', {}).get('id') != binding['session']:
                return result
            size = stream.seek(0, 2)
            offset = max(0, size - TAIL_BYTES)
            stream.seek(offset)
            raw = stream.read(TAIL_BYTES)
        # Drop possibly partial first/last records, never parse unbounded lines.
        lines = raw.splitlines(keepends=True)
        if offset and lines:
            lines = lines[1:]
        previous = None
        for line in lines:
            if not line.endswith(b'\n'):
                continue
            try:
                event = json.loads(line)
                payload = event.get('payload', {})
                if not isinstance(payload, dict) or payload.get('type') != 'token_count':
                    continue
                at = timestamp(event['timestamp'])
                count = payload['info']['total_token_usage']['output_tokens']
                if type(count) is not int or not 0 <= count <= 10**15 or not start <= at <= now:
                    continue
                if previous and at <= previous[0]:
                    continue
                rate = None
                if previous and count >= previous[1] and at - previous[0] <= 120:
                    rate = round((count - previous[1]) / (at - previous[0]), 2)
                previous = (at, count)
                result['last_report_at'] = at
                if at >= now - 900:
                    result['points'].append({'at': at, 'value': rate})
            except (ValueError, TypeError, KeyError, AttributeError):
                continue
        result['points'] = result['points'][-180:]
        last = result['last_report_at']
        result['status'] = 'not-observed' if last is None else 'stale' if now-last > 90 else 'recent'
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        pass
    return result
