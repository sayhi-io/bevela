"""Preserve source-bound handoffs for blind review without exposing arm labels."""
import hashlib
import json
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def export(destination, artifacts, replacements=()):
    """artifacts: {neutral_name: (source_path, exact_source_head)}.

    Original hashes and substitutions remain evaluator-only in returned manifest.
    Reviewer receives redacted bytes and a separate manifest; originals are untouched.
    This is explicit redaction, not a claim of perfect blinding.
    """
    destination = Path(destination)
    if destination.exists():
        raise ValueError('Review bundle must be new; no overwrite')
    records, payloads = {}, {}
    for name, (path, head) in artifacts.items():
        if not name or Path(name).name != name or name in ('.', '..', 'manifest.json'):
            raise ValueError('Expected a neutral artifact filename')
        if len(head) != 40 or any(c not in '0123456789abcdef' for c in head):
            raise ValueError('Expected an exact Git revision')
        original = Path(path).read_bytes()  # Fail closed on missing handoffs.
        rendered = original.decode('utf-8')
        for old, new in replacements:
            if not old:
                raise ValueError('Empty redaction match')
            rendered = rendered.replace(old, new)
        payloads[name] = rendered.encode('utf-8')
        records[name] = {'source_path': str(path), 'source_head': head,
                         'original_sha256': sha(original),
                         'review_sha256': sha(payloads[name])}
    if not records:
        raise ValueError('No handoff evidence supplied')
    destination.mkdir(parents=True, exist_ok=False)
    for name, payload in payloads.items():
        (destination / name).write_bytes(payload)
    public = {name: {'source_head': r['source_head'], 'sha256': r['review_sha256']}
              for name, r in records.items()}
    (destination / 'manifest.json').write_text(json.dumps(public, indent=2) + '\n')
    return {'artifacts': records, 'replacements': list(replacements),
            'limitation': 'Content may reveal treatment; reviewer must report blinding clues.'}
