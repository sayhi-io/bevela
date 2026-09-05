# Observatory read contract v1

`project(states, allowed_scopes, selected=None, now=None)` is a pure function shared
by the service and offline CLI. HTTP: authenticated `GET /api/v1/observatory` with
one optional `scope` parameter. Contract ID: `sayhi.project-intent.observatory/v1`.

| Field | Meaning |
| --- | --- |
| observed_at | Projection observation time, not provider mutation time |
| scopes | Authorized selected scopes, provider status, allowlisted captured source provenance, age, independent execution-feed status |
| dependency_sources | Provenance/age/availability for authorized explicitly imported architecture/grouping sources outside the selected scope, without unrelated work or counts |
| workstreams | Intent/scope/acceptance, readiness, evidence/handoff, applicable claims, precedents, declared divergences, environment requirements, source references, worker observations |
| architecture | Explicit scoped invariants/precedents and applicable visible Workstreams |
| sessions | Valid registered leases, status active/inactive/expired; not authenticated infrastructure occupancy |
| convergence | Declared same-scope semantic overlap and currently approaching sessions |
| attention | Scope/Workstream, explainable kind and message; no automatic intervention |
| initiatives | Native grouping plus explicit qualified refs, visible membership only |
| recent_handoffs | Most recent captured handoffs ordered by parsed instants |
| coverage / read_only | Explicit observation limitations and read-only boundary |

Workstream keys are scope-qualified. Core record identifiers are stable local IDs.
Applicable claim entries include invariant key, accepted/captured revision, evidence
revision, source subject, and `revision-current`, `reconciliation-required`, or
`no-bound-evidence`. Independent review references remain evidence, not a score.

`required_environment` is optional declared metadata, falling back to the existing
`environment` field. The read projection wraps it with availability/occupancy unknown.
It does not interpret command text or acquire authority. Native provider raw fields,
tokens, internal access config and API responses are not serialized wholesale.

Failure distinctions:

- Provider reachable: last refresh succeeded; captured source age still visible.
- Provider unavailable: retain last-known scope cache or explicitly show no data.
- Snapshot adapter/offline export: explicitly offline, never live provider authority.
- Execution feed unavailable/partial: durable intent still available, observation
  absence is not a work/environment state.
- Project Intent HTTP unavailable: browser retains its last view with a prominent
  disconnected label; repository offline bootstrap is independently usable.

Refreshing the UI is a read, not a remote PM mutation or an execution action. The
server polls provider reads every 30 seconds. This tranche does not expose operator
refresh-provider, notes, claims, assignment or review mutation APIs.

## Optional measured activity (local dogfood)

Workstreams now carry `activity`, separate from presence and durable records.
No configured source means `not-connected`, never zero. An operator may configure
one explicit `activity_sources` binding per Workstream in a scope: `kind`
(`codex-local-usage`), `session`, `workstream`, `since` (UTC assignment boundary),
and private `path`. Duplicate bindings report ambiguous rather than summing them.
This provisional adapter checks the file's session identity and reads at most the
last 2 MiB. It exports only timestamps, numeric rates, session identity and coverage;
no source paths, prompts, messages, reasoning text or provider secrets.

Rate is the cumulative `output_tokens` difference divided by seconds between usage
reports. Reasoning counters are not added. This is reporting-interval activity,
not instantaneous generation speed or a measure of reasoning effort. First samples,
counter resets and intervals over 120 seconds are gaps. Future reports are ignored.
Reports older than 90 seconds are stale. The chart has a 15-minute window with up to
180 observations and a labeled per-chart scale; it is not a cross-worker ranking.
No metrics are persisted into the PM provider or checked-in snapshot. Offline
bootstrap remains independent. Missing files don't block durable-state reads.

The browser polls its normalized read endpoint every 5 seconds; provider polling
remains 30 seconds. The compact native SVG area/line treatment references SparkOps
Fleet's D3 chart, without importing SparkOps, React, or Highcharts. The first real
binding is the implementation worker's own session to PI-MISSION-01. Other workers
are not auto-discovered or enrolled from unrelated logs. The local rollout format
is an inspected implementation detail, not a promised stable Codex telemetry API.

## Dynamic local worker enrollment

Each observer scope may configure `enrollment_sources: [{directory, telemetry_roots}]`.
This is operator-owned configuration, not a browser or provider-supplied path grant.
Workers atomically register `<session>.json` in that directory with version, exact
scope/workstream/session, claim time, one-hour presence lease, working/approaching/
avoid and an optional telemetry binding. Files are operational state outside Git.
The CLI serializes same-session writes and refuses silent reassignment or replacing
the bound log path. No PM/provider mutation happens.

The observer discovers registrations on each read: no per-worker service restart.
Known snapshot assignment, scope, filename/session, lease and timestamp checks precede
admission. Reads are bounded (128 records/directory, 64 KiB/record), and invalid or
truncated feeds report partial/unavailable coverage. Telemetry reads additionally
require an operator-allowlisted resolved root and matching file session header.
Only numeric activity reaches the API. A bad telemetry source doesn't erase valid
presence. Expired/inactive registrations remain visible as such but no longer read logs.

Several workers may advance one Workstream. `activity.sessions` then carries separate
per-session measurements; the chart does not sum reporting intervals or claim an
aggregate speed. A single registered session retains the existing `activity` shape.
The legacy static `activity_sources` mechanism remains supported, but a discovered
active enrollment takes precedence for that Workstream. Operators should remove
the old binding on migration to avoid stale fallback. Our own static PI-MISSION-01
binding has been removed. Cooperative local-user filesystem trust is explicit:
this is not remote multi-tenant enrollment/authentication or authenticated worker identity.
