"""Post-exit exploratory reconstruction of sampled source progress; no feedback."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent


def inspect(root):
    root = Path(root)
    # Never inspect a still-running project with the checker.
    completed = json.loads((root / 'results.json').read_text())
    start = completed['concurrency']['start_ns']
    rows = []
    for event in (json.loads(line) for line in (root / 'source-history.jsonl').read_text().splitlines()):
        with tempfile.TemporaryDirectory(prefix='seam-replay-') as directory:
            target = Path(directory)
            for name, digest in event['files'].items():
                path = target / name
                if Path(name).is_absolute() or '..' in Path(name).parts:
                    raise ValueError('Nonrelative source path')
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((root / 'objects' / digest).read_bytes())
            try:
                process = subprocess.run([sys.executable, '-B', '-I', str(root / 'check_contract.py'), str(target)],
                    cwd=target, capture_output=True, text=True, timeout=20)
                score = json.loads(process.stdout) if process.returncode == 0 else {'error': process.stderr}
            except (ValueError, subprocess.TimeoutExpired) as exc:
                score = {'error': str(exc)}
            rows.append({'seconds': (event['mono_ns'] - start) / 1e9, 'trigger': event['trigger'],
                         'score': score.get('score'), 'result': score, 'files': event['files'],
                         'observation_errors': event['errors']})
    passing = [r['seconds'] for r in rows if r['score'] == 7]
    stable = None
    if completed['accepted']:
        for index, row in enumerate(rows):
            if all(r['score'] == 7 for r in rows[index:]):
                stable = row['seconds']
                break
    return {'root': str(root), 'snapshots': rows,
        'first_sampled_7_seconds': min(passing) if passing else None,
        'stable_sampled_7_seconds': stable,
        'note': 'Retrospective sampled-source timing, NOT online verification or guaranteed first correct instant. '
                '100ms sampling is non-atomic; only observed snapshots assessed. Primary endpoint stays final verification.'}


if __name__ == '__main__':
    trials = json.loads((HERE / 'results.json').read_text())['trials']
    result = [dict(condition=r['condition'], repetition=r['repetition'], **inspect(HERE / (r['condition'] + str(r['repetition'])))) for r in trials]
    with (HERE / 'source-progress.json').open('x') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps([{k:r[k] for k in ('condition','repetition','stable_sampled_7_seconds')} for r in result]))
