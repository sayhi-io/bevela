# Observatory read contract v1

## Optional operator workspace inventory

The HTTP projection may additionally include `workspace_inventory`. It is an
operational observation, not a PM source or a new scope. A principal must explicitly
have `workspace_inventory: true`; product readers receive no repository names,
paths, counts or filesystem scan. Config supplies one absolute `root` and exact
`scope_by_repository` mappings. Only immediate real directories with a `.git`
marker are considered, at most200 root entries; symlinks and non-repositories are
excluded. No Git commands, code reads, credential reads or other-session discovery.

Configured scoped observations are correlated by explicit mapping. Unmapped entries
are visible as `not-mapped`, with unknown remote PM state and worker activity—not
zero work or an assertion that no provider project exists. Explicit mappings to
unauthorized scopes are omitted before counts. A selected scope excludes unmapped
and other-scope repositories. Root access failure is `unavailable`; enumeration
limits are `partial-limit`, never a successful full inventory. The source root is
the canonical `repos/` inventory, not runtime/vendor/archive or every nested path
under the workspace. New canonical repositories appear automatically on reads.

Repository inventory does not enroll Workstreams or expand provider credentials.
Full inventory coverage and complete intent/agent observation remain distinct.
The two existing provider connections continue unchanged. Offline snapshots retain
their existing durable intent contract; this live filesystem inventory is not
silently promoted into offline PM truth.

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
| recently_rested / rested_coverage | Latest explicit inactive registrations in the last24hours, newest first, capped12. Timestamp is the inactive registration heartbeat, not an exact stopping time. Expired active leases are excluded. Multiple sessions may rest while another works on the same Workstream. |
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

The opt-in `/observatory` presentation uses the same API and existing card/detail
components. Home summarizes fresh observations, explicitly reported inactive
sessions and attention; hash navigation exposes the [Developers Board and work
calendar](ACTIVITY_VIEWS.md), all work (including completed and deferred
declarations), architecture, environments, handoffs and coverage. `/` remains the
classic rollback view. No PM datastore or session history is added.
`workstreams[].local_reports` are rendered with their local/pending/uncertain/
published state and full evidence/receipt detail, independently of provider
readiness/handoffs. Recent report cards are bounded24; all available reports remain
in Workstream detail. Listing coverage is shown, not inferred as complete history.

## Explicit pull request references

Workstream provider metadata may carry `pull_requests` (at most20). Each reference
has `repository` (canonical HTTPS repository URL), `number` (positive integer),
`url` (exact repository `/pull/N` or `/-/merge_requests/N` link), and `relationship`
(`implementation`, `dependency`, or `integration`). Nested repository groups are
allowed; these are link formats, not a claim of full Git-provider integration.
No credentials, query, fragment, port, traversal, duplicate repository/number, or
unknown fields are accepted. Each workstream can reference several repositories;
several workstreams may reference the same PR. No links are inferred from prose.

Optional `observation` requires timezone-aware `observed_at` and short `source`.
Optional fields: `head` (full40/64hex object ID), `state` (`open`, `closed`, `merged`),
`draft` (boolean), `review` (`approved`, `changes-requested`, `review-required`,
`unknown`), and `required_checks` (`passed`, `failed`, `pending`, `unknown`). Review
and check observations require an exact head. They do not establish checks for a
later head or current architecture. No observation means unknown, never green.

Projection adds `observation_status` (`not-observed`, `last-known`, or
`future-timestamp`) and `age_seconds` relative to the projection. It never labels
these observations live. Future timestamps retain provenance but do not present
their states as usable evidence. Provider refresh time does not refresh a PR's own
observation time. Offline snapshot preserves references and original observations.
Scope filtering precedes projection. Invalid metadata rejects a provider refresh
under the existing validated-snapshot/cache fallback, not partial trusted data.

Both UI views show repository-qualified PR chips and a detail Integration section.
Git provider remains authoritative; merged never implies deployed or production
authorized. No GitHub polling, credential service, automatic PR inference, provider
write from the browser, or stale-observation attention automation is introduced.

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

The observer retains already observed numeric points in process memory, bounded to
15 minutes/180 points per execution source and 2048 sources overall. Bounded log-tail
turnover, missing telemetry files, and an inactive/expired lease do not erase points
already seen. Current `status` still comes from the current observation/lease, never
from retained points; historical values cannot make a worker live. No ended lease's
log is reopened to reconstruct history. Scope, Workstream, session, exact checkout,
branch and telemetry source distinguish histories. A new lease on the same execution
source preserves earlier points but starts a separate attribution interval; optional
point `break_before: true` prevents the chart connecting across those intervals.
Unregistered intervals stay unknown, not zero or interpolated. The existing first
sample, counter-reset and long-report-interval gaps also remain unknown.

`activity.history_coverage` states this bounded process-local coverage and is shown
in Workstream telemetry detail. Service restart clears the observation cache;
unobserved history outside the permitted parser tail is not recoverable. Browser
reloads share the running observer's retained history. Removed/invalid registrations
do not surface a historical series; a changed execution identity starts separately.
For local rollback, `retain_activity_history: false` in the service config selects
the previous stateless adapter projection. Neither mode is a PM history datastore.

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
