"""Declared conversation references, independent of PI presence and transport authority."""
import re


_IDENTIFIER = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,199}')


def validate_runtime_session(value):
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) - {'runtime', 'id', 'host', 'instance'}:
        raise ValueError('Runtime session requires runtime, id, host and optional instance')
    if value.get('runtime') not in ('codex', 'qwen-code'):
        raise ValueError('Runtime must be codex or qwen-code')
    for key in ('id', 'host'):
        if not isinstance(value.get(key), str) or not _IDENTIFIER.fullmatch(value[key]):
            raise ValueError('Runtime session ' + key + ' must be a bounded identifier')
    instance = value.get('instance')
    if instance is not None and (not isinstance(instance, str) or not _IDENTIFIER.fullmatch(instance)):
        raise ValueError('Runtime instance must be an opaque local identifier, not a URL or credential')
    return {key: value[key] for key in ('runtime', 'id', 'host', 'instance') if value.get(key) is not None}


def runtime_session_ref(record):
    """Project explicit references or unambiguous legacy Codex telemetry bindings.

    Never infer a runtime from the shape of a PI session ID or a model name.
    Legacy projection reads registration metadata only, never a transcript.
    """
    if record.get('runtime_session') is not None:
        return validate_runtime_session(record['runtime_session'])
    telemetry = record.get('telemetry')
    host = (record.get('checkout') or {}).get('host')
    if isinstance(telemetry, dict) and telemetry.get('kind') == 'codex-local-usage' and host:
        return validate_runtime_session({'runtime': 'codex', 'id': record['session'], 'host': host})
    return None
