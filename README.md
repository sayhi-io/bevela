# SayHi Project Intent · Mission Control

Project Intent is SayHi's independent development-intent and architectural-coherence
service. SparkOps, Verify and Projects participate within explicit scopes; no product
owns its runtime. Mission Control is the read-only human observatory over that state.

This is a bounded provisional service, running alongside the unchanged SparkOps
CLI prototype. It does not migrate that working implementation or its users
silently. The source is committed on `main`; local dogfood and production
qualification remain separate concerns.

## Current status

The canonical repository is `repos/sayhi-project-intent`. The current `main`
branch contains the Mission Control service, scoped worker/session observations,
Workstream Map, workspace inventory, and bounded CLI evaluation harnesses. The
local dogfood instance is a separately managed user service:

```bash
systemctl --user status project-intent-dogfood.service
```

It serves the read-only observatory on `http://127.0.0.1:8290` from a pinned
release under the workspace runtime state. Source changes do not become live
until a separately authorized release activation updates that pinned runtime.
This is still loopback development dogfood: it is not public hosting, a HA
service, or production availability evidence.

## Mission Control views

The authenticated observatory exposes the conventional read-only views plus the
newer presentation experiments:

- `/observatory` — workstreams, architecture, reports, attention, and worker/session detail.
- `/observatory#map` or `/workstream-map` — scoped declared-boundary and convergence map.
- `/observatory?design=plan`, `studio`, or `console` — presentation-only variants.

Worker groups and workspace inventory are projections of explicitly authorized
read-model data. They do not infer agent identity, detect edits, allocate work,
grant permissions, or add provider authority. See [Workstream Map](docs/WORKSTREAM_MAP_EXPERIMENT.md),
[worker groups](docs/WORKER_GROUPS.md), and [design lab](docs/DESIGN_LAB.md) for
the detailed contracts and experimental limits.

## Worker and orchestrator workflow

Use the repo-backed [Project Intent skill](skills/project-intent/SKILL.md) for
assignment discovery, exact-checkout scope, revision-aware evidence, coordination
and successor handoff. Workers select IDs from discovery themselves; humans need
not copy IDs or relay routine continuation commands.

For a consistent start, run the read-only onboarding flow from the actual task
checkout. It discovers candidates and, when given an exact ID, prints the full
orientation plus an explicit enrollment template; it never enrolls or assigns a
worker automatically:

```bash
/home/meanaverage/sayhi/bin/project-intent onboard --query "task keywords"
/home/meanaverage/sayhi/bin/project-intent onboard \
  --scope sayhi/project-intent --workstream SELECTED-ALIAS-OR-NATIVE-ID
```

After reviewing the orientation, run the printed `enroll` command with the
worker's actual access mode, paths, semantic seams and bounded task summary.
`discover` and `start` remain available as lower-level commands.

No candidate fits? Workers can use the opt-in `task-register` command to inspect live
native inventory and record **the task the user already assigned**, then onboard and
enroll. Repository setup does not pre-create every future task. This is synchronous
bookkeeping, not a coordinator queue or new execution authority. See
[task registration](docs/TASK_REGISTRATION.md) for the preview/submit flow, retries
and local scope policy.

Supported interfaces share the normalized context; optional operator commands are
local CLI operations, not browser mutation endpoints:

| Need | Interface |
| --- | --- |
| Worker onboarding, orientation and presence | `onboard`, `discover`, `start`, `enroll` |
| Record an existing user task, refresh onboarding context | `task-register` (opt-in local capability) |
| Immutable local report and publication status | `report`, `report-status` |
| Authorized native publication and metadata reconciliation | `publish-report`, `provider-list`, `reconcile` |
| Explicit existing-session attachment and bounded continuation | `session-attach`, `session-continue` |
| Last-known repository context | `export`, offline `start` |

Read [reporting and reconciliation](docs/REPORTING.md) and the
[optional session connector](docs/SESSION_CONNECTOR.md) before their use. Native
publication does not certify evidence or automatically change provider readiness.
The local connector records delivery; it does not infer execution from a queue
receipt. The [mature SparkOps execution-consumer bridge](docs/SPARKOPS_CONSUMER_BRIDGE.md)
is deferred task 6. [Integration validation](docs/INTEGRATION_GATE.md) records
the post-merge review and the remaining independent-review, CI, release, and
production gates.

The skill's canonical source is this repository's `skills/project-intent/` directory.
For this workspace it is made discoverable at
`/home/meanaverage/.codex/skills/project-intent` by a symlink to that directory; it is
not bundled into the Python runtime distribution. Check an existing target before
installation and preserve a different installed skill. A new session can discover
the installation; already-running workers should explicitly read the linked SKILL.md
when asked to use it. The managed workspace installation follows the pinned release
through `state/project-intent/current`, not an arbitrary development branch. Report
the resolved source and skill hash/source seal when claiming a reviewed version.

## Run and orient

Python 3.11+; no runtime dependencies outside the standard library:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/project-intent start --snapshot .project-intent/snapshot.json --workstream PI-MISSION-01
.venv/bin/project-intent serve --config /private/project-intent/config.json --port 8290
```

The `serve` command is useful for an explicitly configured development process.
For the managed local dogfood instance, inspect the user service above rather
than starting a second process on port 8290.

Open `http://127.0.0.1:8290`. Every page/API request requires independent Basic
credentials: a principal name and a randomly generated high-entropy token. This
loopback service is not a public internet server. Do not reuse a product password,
put credentials in a URL, or bind a public proxy without a separately reviewed TLS
and identity boundary. Use a private SSH tunnel if accessing another machine.

The service reads `GET /api/v1/observatory?scope=sayhi%2Fsparkops`. Omit `scope`
for all scopes granted to the authenticated principal, not all SayHi data. The UI
uses only this normalized API. Refresh view re-reads the projection; background
provider polling is independent and read-only. No provider credentials reach the UI.

Real local dogfood configuration and cache are under
`/home/meanaverage/sayhi/state/project-intent/`, outside Git. The private
`operator-access.json` contains the operator login; `sparkops-reader-access.json`
demonstrates a product-only principal. The local scope map now covers 20 configured
SayHi project scopes, including Project Intent, SparkOps, Verify and Projects. Scope
configuration alone does not establish task inventory, worker enrollment or write
permission; inspect the current scope map and discovery results for actual coverage.

Use explicit scoped export for repository fallback:

```bash
.venv/bin/project-intent export --config /private/project-intent/config.json \
  --scope sayhi/project-intent --output .project-intent
```

`snapshot.json` and `PROJECT.md` are replaceable, last-known projections. Offline
`start` never contacts the provider, reads another repository, or authorizes a PM
mutation. Export is an operator/local-process operation; keep its config private.

Live cooperative presence has a separate one-hour lease:

```bash
.venv/bin/project-intent presence --snapshot .project-intent/snapshot.json \
  --workstream PI-MISSION-01 --directory /private/project-intent/presence/platform \
  --session UNIQUE_SESSION --working "bounded task" --approaching intent/projection
```

Renew at meaningful transitions; add `--inactive` at handoff. Directory access is
local cooperative authority, not authenticated fleet identity or a lock. The server
only reads explicitly configured feeds, never shells out to Git or SparkOps.

See [architecture](docs/ARCHITECTURE.md), [read model](docs/READ_MODEL.md), and
[operations](docs/OPERATIONS.md) for authority, recovery and production limits.

The repository also contains bounded, non-runtime evaluation material under
`experiments/` and `docs/CLI_AB_*.md`. These studies test worker isolation,
handoffs, and whether structured Project Intent context helps execution; they do
not turn Project Intent into a mandatory execution graph or prove productivity
benefits.

## Enroll a real worker

Workers should navigate onboarding themselves; the operator need not supply IDs.
From their actual task checkout:

```bash
/home/meanaverage/sayhi/bin/project-intent discover --query "task keywords"
/home/meanaverage/sayhi/bin/project-intent start --workstream SELECTED-ALIAS-OR-NATIVE-ID
/home/meanaverage/sayhi/bin/project-intent enroll --workstream SELECTED-ALIAS-OR-NATIVE-ID \
  --codex --access edit --touching-path relative/file.py \
  --touching-seam your/current-boundary --approaching your/next-boundary \
  --avoid-path unrelated/directory --working "actual bounded task"
```

These commands are for the worker to choose and execute, not instructions for the
human to fill in. Discovery returns task descriptions, aliases, provider-native
identifiers, native delegate/assignee names, reference checkouts and registered
workers. Exact current-checkout reference matches sort first, but are never automatic
assignments. Both `PI-MISSION-01` and its native `SAYINT-5` resolve to the same intent;
cross-scope ambiguity fails and requires explicit `--scope`. Read the assignment's
constraints, environment and acceptance from `start` before enrolling. If no existing
record fits, inspect live native inventory with the configured `task-register` route
and record the already assigned task as described above. Do not invent work, borrow
an unrelated workstream, or interpret a similar title as authority. If registration
is unavailable, report the exact tracking gap rather than claiming enrollment.

Enrollment observes **only the worker's own checkout**, defaulting to the current
directory (`--checkout` overrides). It records host, exact Git worktree root, shared
Git directory, branch, HEAD and observation timestamp. No remote URL, status/diff,
or other worktree is scanned. Detached/unborn HEAD remains explicit. A workstream's
`source_checkout` is merely a reference; it may be another owner's inspection source.
It is never substituted for the executing worker's checkout.

Edit intent requires explicit relative paths (files/directories, no globs or `..`);
`.` means an explicitly whole-checkout task. `--access inspect` declares inspection
instead. Unspecified legacy scope is displayed as unknown, not narrow or safe.
`--touching-seam` and `--approaching` describe architectural boundaries, not just
paths. `--avoid-path` and `--avoid` preserve exclusions. Renew enrollment when these
change. A still-active session cannot silently switch checkouts: release first.
Branch/HEAD changes inside the same checkout are refreshed at enrollment transitions.

`start` and `enroll` show nearby fresh local registrations: same-repository worktrees,
declared path overlap and same-scope semantic overlap. Different checkouts in the same
repository can converge; identical path spellings in unrelated repos do not. These
are advisory declarations, not detected edits, conflict proofs or edit permissions.
The CLI reads cached durable state and local leases without provider credentials;
missing/stale snapshots are explicit. Existing unannotated provider issues remain
outside this enrolled subset until a separate provider-enrollment step supplies scope.

From this workspace, a Codex worker can orient and opt into observation:

```bash
/home/meanaverage/sayhi/bin/project-intent start \
  --scope sayhi/sparkops --workstream ENV-SUBSTRATE-01
/home/meanaverage/sayhi/bin/project-intent enroll \
  --scope sayhi/sparkops --workstream ENV-SUBSTRATE-01 --codex \
  --working "Your actual current bounded task" --approaching "your/actual-seam"
```

Choose your actual assigned Workstream; this example does not assign the Environment
owner's work to a new worker. `--codex` uses your `CODEX_THREAD_ID`, matches only that
session's filename, and verifies its header. It does not search other conversations
or infer ownership. Alternatively provide `--session ID --telemetry-file /path/to/own-rollout.jsonl`.
For another runner, use `--session ID` without a telemetry file: presence works,
but inference remains unconnected. Only the inspected Codex numeric adapter ships now.

The workspace launcher selects a credential-free `worker-scopes.json` map outside
Git. Standalone installations use `--worker-config /path/to/map --scope SCOPE`, or
explicit `--snapshot FILE --directory DIRECTORY`. No provider/admin credential is
needed. Observer and worker must share the local registration directory; an
arbitrary directory is not automatically added to the observer.

Repeat **enroll** at meaningful transitions and before its one-hour lease expires.
It renews presence without resetting the telemetry attribution boundary while the
lease is continuous; omitted working/approaching/avoid fields retain prior values.
After expiry or release, re-enrollment starts a new attribution boundary so work
done during a gap is not silently attributed. First rate needs two new usage reports.
Do not use the older `presence` command to overwrite enrollment files.

At handoff, release your registration:

```bash
/home/meanaverage/sayhi/bin/project-intent enroll \
  --scope sayhi/sparkops --workstream ENV-SUBSTRATE-01 --codex --inactive
```

No process is launched or session controlled. Release/expiry stops telemetry reads;
crashed workers need no manual cleanup for correctness. Registration does not create
PM work, grant authority, prove liveness, or override scope. Here registration means
session enrollment; the separate `task-register` command records durable user tasks.
Offline snapshots remain
last-known intent, and telemetry/presence stay separate operational observations.
