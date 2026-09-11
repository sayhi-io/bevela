# Qwen study publication and verification

The September 11 source publication includes the existing Qwen experiment
harnesses, offline regression tests, frozen recorder source snapshots, methods
and September 9 result pages. Their distributed candidate fixtures and shared
recorders depend on the previously published Sol calibration commit `a2af59d`.
These are research tools, not a new production PI backend or a deployed steering service.

The [September 10 independent-request summary](qwen-independent-requests.md)
has a narrower evidence basis: the study owner's existing backlog and method,
without a new audited per-worker export. Source publication must not be mistaken
for repeating the model experiments or verifying every historical artifact.

## Public copies versus original evidence

Four public measurement ledgers (confidence, ordinary thinking-off, compact PI v1
and compact PI v2) contained absolute private evaluation paths in checker errors.
The publication copies replace those prefixes with `<private-evaluation>/source/`.
Scores, error types, module names and failed-contract information are retained.

Each changed ledger has a `publication` object identifying this transformation
and the SHA-256 of the original local ledger. Existing provenance hashes identify
original artifacts, not the edited public copy. Original study files and frozen
recorder snapshots are untouched. No native transcripts, runtime profiles,
credentials, raw evaluation directories or installed model binaries are published.
Historical statements such as "no commit" describe status when a trial report
was written; this note records the later source-publication step.

## Offline validation

Use an environment owned by this checkout:

The full Linux suite requires `bubblewrap` and system Node at `/usr/bin/node`
for sandboxed synthetic-runtime probes (on Ubuntu: `sudo apt-get install bubblewrap nodejs`).
The two Python-only reference checks supply an empty disposable npm prefix for
the historical evaluator; they do not require the developer's npm installation.
A test-only wrapper also mounts the system `/lib64` read-only where present,
because x86 Python needs a loader path absent on the original ARM host.
These compatibility checks do not establish unmodified historical-launcher
portability. The frozen/executable experiment sources are not rewritten.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m unittest discover -s tests -v
node --test tests/*.test.cjs
```

The ordinary unit suite uses synthetic fixtures and fake transports; it does not
launch Qwen inference. One optional native hook transport test is skipped unless
`QWEN_STEERING_TEST_RUNTIME` is explicitly supplied. That test's scripted provider
is distinct from a real model canary. Live model studies require their own frozen
inputs, runtime configuration and explicit execution authorization; do not run
the experiment launchers merely to reproduce the offline test suite.
