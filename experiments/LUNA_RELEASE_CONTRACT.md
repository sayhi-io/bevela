# Incident Investigation Release: common product contract

This is an isolated feature exercise, not a production assignment. Every condition
receives the same contract, source baseline, ordinary notes, tools and acceptance.
Internal interfaces and implementation are the team's decisions.

## Shared source and ownership

Status baseline is Study02 accepted control commit
`782f969409079d743f6b43fb562df79b76b7d21a`. It already has legacy history and a browser.
The separate support-tools repository starts with package metadata and a help-only
CLI scaffold. Both are source-only clones with no remotes or earlier transcripts.

Four owners work concurrently: storage (new snapshot persistence modules/migrations
and storage tests), api (src/worker.mjs, API integration/validation and tests), browser
(src/ui.mjs, src/history-browser.mjs and browser tests), export (support-tools).
The legacy src/state.mjs belongs to storage; API must coordinate changes through
that owner. Ordinary per-role notes and read-only peer checkouts are available.
Do not edit peer files or wait indefinitely for a response; document compatible
interfaces and proceed within ownership. Integration can resolve actual conflicts.

## API revision 1

Preserve the existing `/api/incidents` default response and its validation, along
with `/api/status`, report submission, summary and existing fixtures/tests.
New clients opt into `GET /api/incidents?view=history-v2`. Component/state/limit
retain legacy meanings: default limit10, integer1..50, exact canonical components,
states investigating/resolved. Invalid/duplicate query values receive400.

The response is `{incidents,nextCursor,snapshot:{id,createdAt,expiresAt}}`, timestamps
ISO8601. Snapshot IDs and cursors are opaque; never depend on evaluator encodings.
Ordering is startedAt descending then id descending. Initial request without
cursor/snapshot materializes the entire matching incident set and public displayed
values, including empty sets. Later inserts (including backdated), state/summary
updates and deletions do not change that snapshot. Fresh initial requests see new
data. Persistence is SQLite/D1 through env.DB, not only process memory; reopening
the database preserves unexpired snapshots. Apply new migrations after existing data.

Supplying `snapshot=ID` without cursor reads that snapshot from its beginning.
Continuation uses its nextCursor and the same filters/page size; both snapshot ID
and cursor may be supplied together and must agree. Cross-filter reuse or malformed
cursors receive400. Missing/expired snapshot references receive410 with
`{error:"history_snapshot_expired"}`; never silently start another snapshot.
Continuation preserves snapshot id and creation time, and explicitly reports expiry.
The configured retention is env.HISTORY_RETENTION_MINUTES (default30); revision1
uses retention at creation. Fixed-time tests replace global Date; no wall-clock sleeps.

## Browser

Retain accessible Incident component/Incident state selects, #incidents rows with
data-incident-id, Load more, Retry, and live #historyStatus. Use history-v2.
Expose current snapshot in #historySnapshot with data-snapshot-id and display expiry.
Add an accessible Refresh history button. Refresh explicitly begins a new snapshot.
On410, display an expired state and offer refresh; do not silently mix/restart data.
Network failure is distinct and retry preserves filters/snapshot/cursor.
New-filter selections clear old rows and traversal. Out-of-order old responses and
repeated load-more clicks cannot overwrite or duplicate the current results.
URL component/state/snapshot parameters are shareable. Filter changes push history;
binding a newly created snapshot replaces that entry. Back/forward restore filters
and that snapshot's first page, or show expiry if unavailable. Literal incident text,
keyboard/focus, narrow layout and existing summary remain correct.

## Separate export client

CLI: `node bin/export-history.mjs --origin URL --output FILE --checkpoint FILE`
with optional `--component ID --state STATE --snapshot ID --limit N --max-pages N`.
`--max-pages` cleanly pauses after N successful pages in this invocation. Repeating
the command with the same output/checkpoint resumes, never duplicates successful
pages, and stays on the original snapshot. A supplied snapshot starts at its first
page and must agree with checkpoint filters/snapshot. Reject conflicting arguments.
Output is UTF-8 JSONL of public incident objects in API order. Checkpoint includes
snapshot metadata, filters, limit, nextCursor and complete boolean; internal
durability fields are allowed. Completed re-invocation does not append duplicate rows.
Persist only fully obtained pages; failed responses must not corrupt accepted output.
Retry transient network/5xx failures with a bounded policy, at most3 attempts/page.
On410, exit3 and emit JSON error history_snapshot_expired on stderr, leaving output
and checkpoint unchanged. Other unrecoverable errors are nonzero with a clear error.
Never silently restart against newer data. CLI and browser sharing a snapshot must
agree on full public values and incident ordering. No runtime third-party dependencies.

## Scheduled revision 2

Delivered after the first-stage owner checkpoint, equally in both conditions:
retention becomes10 minutes and MUST apply retroactively to already-issued snapshots.
Effective expiry is min(stored expiry, createdAt + current configured retention).
It never extends an earlier expiry. At/after expiry, return410; before it, advertise
effective expiry. Both clients must recover truthfully and preserve already-exported
output. Earlier revision1 evidence alone does not establish revision2 acceptance.
All other requirements remain unchanged. Record which evidence is current.

## Evidence and exclusions

Run existing regression/syntax tests and common API/browser/export acceptance.
Report failures as failures, not as unavailable tools when the tools actually ran.
Leave a detailed handoff with commits, interface decisions, real commands/results,
incomplete work and next action. No production, schedules, monitored endpoints,
external Git, provider credentials, other trial arms, host skills or previous chats.
No stronger-model repair or task-specific coaching. Local disposable Git commits
are authorized. Do not stage trial instructions, notes, handoffs or generated evidence.
