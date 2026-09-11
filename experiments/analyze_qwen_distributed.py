"""Post-exit evidence extraction. Never sends feedback to experiment workers."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import shutil
import tempfile

from experiments import qwen_distributed_study as study
from experiments.qwen_code_adapter import usage_fields


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def replay_provenance(root):
    return {**{name: study.sha(root / name) for name in (
        'source-history.jsonl', 'before.json', 'check_contract.py', 'result.json', 'plan.json')},
        'analyzer_sha256': study.sha(__file__)}


def replay(root):
    study.verify(root)
    final = json.loads((root / 'result.json').read_text())
    origin = final['concurrency']['start_ns']
    initial = json.loads((root / 'before.json').read_text())
    protected = ['acceptance.py', 'OBJECTIVE.md', 'architecture.json', 'AGENTS.md'] + [
        name for name in initial if name.startswith('tasks/')]
    observations = []
    with tempfile.TemporaryDirectory(prefix='qwen-replay-') as temporary:
        parent = Path(temporary)
        for index, state in enumerate(rows(root / 'source-history.jsonl')):
            source = parent / str(index)
            source.mkdir()
            for name, digest in state['files'].items():
                relative = Path(name)
                if relative.is_absolute() or '..' in relative.parts:
                    raise ValueError('Unsafe observed path')
                artifact = root / 'objects' / digest
                assert study.sha(artifact) == digest
                target = source / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(artifact, target)
            outcome = study.base.score(source, root / 'check_contract.py')
            changed = [name for name in protected
                       if state['files'].get(name) != initial.get(name, {}).get('sha256')]
            observations.append({'seconds': max(0, (state['mono_ns'] - origin) / 1e9),
                'accepted': bool(outcome.get('accepted')) and not changed and not state.get('errors'),
                'failed_contracts': outcome.get('failed_contracts'),
                'component_checks': outcome.get('component_checks'),
                'protected_inputs_changed': changed, 'observer_errors': state.get('errors', []),
                'evaluation_error': outcome.get('evaluation_error')})
    first = next((r['seconds'] for r in observations if r['accepted']), None)
    last_bad = max((i for i, r in enumerate(observations) if not r['accepted']), default=-1)
    matches = bool(observations) and observations[-1]['accepted'] == final['accepted']
    durable = observations[last_bad + 1]['seconds'] if matches and last_bad + 1 < len(observations) else None
    result = {'first_accepted_sample_seconds': first, 'durable_accepted_sample_seconds': durable,
        'provenance': replay_provenance(root),
        'final_sample_matches_final_score': matches, 'sampled_states': observations,
        'limitation': '100ms non-atomic source observations replayed after exits; not live acceptance feedback or exact continuous first-pass time.'}
    study.write_json(root / 'qwen-replay.json', result)
    return result


def tool_events(root, role, origin):
    calls = {}
    if not (root / role / 'events.jsonl').is_file():
        raise ValueError('Native event log unavailable: ' + role)
    for row in rows(root / role / 'events.jsonl'):
        event = row.get('event', {})
        content = event.get('message', {}).get('content', [])
        if not isinstance(content, list):
            continue
        for item in content:
            seconds = (row['mono_ns'] - origin) / 1e9
            if item.get('type') == 'tool_use':
                inputs = item.get('input') or {}
                command = inputs.get('command', '')
                pi = bool(isinstance(command, str) and ('_worker_cli.py' in command or 'project-intent ' in command
                    or re.search(r'\$(?:PI\b|\{PI\})', command)))
                calls[item['id']] = {'id': item['id'], 'name': item.get('name'), 'seconds': seconds,
                    'file': inputs.get('file_path', inputs.get('path')), 'command': command,
                    'pi_tagged': pi, 'finished_seconds': None, 'is_error': None}
            elif item.get('type') == 'tool_result' and item.get('tool_use_id') in calls:
                call = calls[item['tool_use_id']]
                call.update(finished_seconds=seconds, is_error=item.get('is_error', False),
                            output_summary=item.get('content'))
    return list(calls.values())


def project(root, *, do_replay=False):
    plan = study.verify(root)
    final = json.loads((root / 'result.json').read_text())
    telemetry = json.loads((root / 'worker-analysis.json').read_text())
    expected = {(role, session) for role, session in plan['sessions'].items()}
    for name, records in [('workers', final['workers']), ('telemetry', telemetry)]:
        if len(records) != len(expected) or {(r['role'], r['session']) for r in records} != expected:
            raise ValueError('Missing or duplicate role/session coverage: ' + name)
    telemetry_by_role = {r['role']: r for r in telemetry}
    origin = final['concurrency']['start_ns']
    history = rows(root / 'source-history.jsonl')
    initial = json.loads((root / 'before.json').read_text())
    source_events = []
    previous = {k: v.get('sha256') for k, v in initial.items() if not k.startswith('.pi/')}
    for state in history:
        for name in sorted(previous.keys() | state['files'].keys()):
            if previous.get(name) != state['files'].get(name):
                source_events.append({'seconds': max(0, (state['mono_ns'] - origin) / 1e9),
                    'path': name, 'before': previous.get(name), 'after': state['files'].get(name),
                    'trigger': state['trigger']})
        previous = state['files']
    workers = []
    for row in final['workers']:
        observed = telemetry_by_role[row['role']]
        calls = tool_events(root, row['role'], origin)
        native_events = rows(root / row['role'] / 'events.jsonl')
        transport = rows(root / row['role'] / 'transport.jsonl')
        request_ids = {e['request'] for e in transport if e['event'] == 'request'}
        # Match aggregate usage: the last observation for each actual request,
        # with malformed/missing fields left unknown rather than coerced to zero.
        request_usage = {e['request']: usage_fields(e['usage']) for e in transport
                         if e['event'] == 'usage' and e['request'] in request_ids}
        system_events = [{'seconds': (e['mono_ns'] - origin) / 1e9,
            'subtype': e['event'].get('subtype'), 'data': e['event'].get('data')}
            for e in native_events if e['event'].get('type') == 'system' and e['event'].get('subtype') != 'init']
        tagged = [c for c in calls if c['pi_tagged']]
        operations = Counter()
        for call in tagged:
            operations.update(re.findall(r'(?<![\w-])(onboard|discover|start|enroll|presence|report-status|report|docs|repair-[a-z-]+)(?![\w-])', call['command']))
        workers.append({'role': row['role'], 'session': row['session'],
            'started_at': row['started_at'], 'finished_at': row['finished_at'],
            'start_seconds': (row['start_monotonic_ns'] - origin) / 1e9,
            'end_seconds': (row['end_monotonic_ns'] - origin) / 1e9,
            'duration_seconds': row['elapsed_seconds'], 'exit_code': row['exit_code'],
            'timed_out': row.get('timed_out', False), 'usage': observed['usage'],
            'recorder_stream_complete': row.get('stream_complete'),
            'recorder_stream_eof': row.get('stream_eof'),
            'recorder_stream_error_type': row.get('stream_error_type'),
            'relay_complete': row.get('relay_complete'),
            'native_identity_verified': observed['native_identity_verified'],
            'native_success': observed['native_success'], 'tools': dict(Counter(c['name'] for c in calls)),
            'native_system_events': system_events,
            'native_retry_events': sum(e['subtype'] == 'retry' for e in system_events),
            'response_limit_sized_completions': sum(u.get('output') == 32768 for u in request_usage.values()),
            'max_observed_request_input_tokens': max((u['input'] for u in request_usage.values()
                                                     if 'input' in u), default=None),
            'pi_tagged_calls': len(tagged), 'pi_operation_candidates': dict(operations),
            'pi_tagged_seconds': sum(c['finished_seconds'] - c['seconds'] for c in tagged if c['finished_seconds'] is not None),
            'pi_native_result_bytes': sum(len(json.dumps(c.get('output_summary'), ensure_ascii=False).encode())
                                          for c in tagged if c['finished_seconds'] is not None),
            'pi_tagged_errors': sum(c['is_error'] is True for c in tagged), 'calls': calls})
    checked = replay(root) if do_replay else (json.loads((root / 'qwen-replay.json').read_text())
        if (root / 'qwen-replay.json').exists() else None)
    if checked is not None and checked.get('provenance') != replay_provenance(root):
        raise ValueError('Cached replay provenance mismatch; explicitly recompute')
    value = {'label': root.name, 'condition': plan['condition'], 'pi_behavior': 'v0.05 unchanged' if plan['pi_enabled'] else None,
        'result': final, 'workers': workers, 'source_changes': source_events, 'replay': checked,
        'evidence_sha256': {name: study.sha(root / name) for name in (
            'plan.json', 'result.json', 'worker-analysis.json', 'source-history.jsonl')},
        'native_event_hashes': {r['role']: study.sha(root / r['role'] / 'events.jsonl') for r in workers},
        'replay_sha256': study.sha(root / 'qwen-replay.json') if checked is not None else None,
        'analyzer_sha256': study.sha(__file__),
        'limits': 'PI-tagged seconds are recorder-received native-event spans, not verified tool execution time, and may include non-PI work; native result bytes are observed serialized tool-result content, not attributable prompt tokens or compute. Command token matches are candidates, not verified successful operations. Missing role/log evidence refuses analysis rather than becoming zero. Source changes do not alone prove authorship, useful decomposition, duplication or intent. Private model reasoning is not copied into this report.'}
    study.write_json(root / 'qwen-analysis.json', value)
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--replay', action='store_true')
    args = parser.parse_args()
    result = project(args.root.resolve(), do_replay=args.replay)
    print(json.dumps({'project': result['label'], 'accepted': result['result']['accepted'],
        'source_changes': len(result['source_changes']), 'workers': len(result['workers'])}))
