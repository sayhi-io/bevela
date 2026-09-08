# Study 03: incident-history continuity under concurrent changes

Status: design in progress; NOT frozen, launched, or efficacy evidence.
Studies 01/02 and their frozen harnesses/results remain unchanged.

Draft shared source baseline: the accepted Study02 A-control integration commit
`782f969409079d743f6b43fb562df79b76b7d21a`, supplied identically to every condition.
Use source-only disposable clones, not the original trial worktrees or their
transcripts/provider state. This lets Study03 extend an existing accepted feature
and test compatibility, rather than retest implementing the original missing route.
Baseline selection is fixed before new runs; inherited code provenance is common
to all conditions and must be disclosed in the report.

## Shared product request

Extend the disposable SayHi Status incident-history feature to support reliable
investigation while incidents continue changing. A visitor should share a filtered
history URL, page backward without duplicate or missing entries when newer incidents
arrive, refresh deliberately, and return to the same view using browser navigation.
Preserve the existing public summary, incident reporting, and legacy API clients.

This adds cross-layer semantics to Study 02 rather than arbitrary puzzle difficulty:

- Stable page membership across concurrent inserts, including equal timestamps;
  keyset cursors bind component/state filters and a snapshot watermark. Changing
  filters resets traversal. Reusing a cursor with different filters is rejected.
- State transitions during pagination have an explicit shared contract: the first
  page captures membership for traversal; a refresh starts a new view. Storage,
  API and browser must agree. No claim of unlimited historical snapshots: define
  a bounded retention window and a truthful expiration response before freezing.
- Legacy clients retain their original default response contract. New clients
  opt into the richer pagination response. Unknown/deleted components and expired
  cursors produce a useful recoverable UI, not silently broadened queries.
- Back/forward navigation restores filters and traversal consistently. Out-of-order
  responses from prior filters cannot overwrite the current selection. Loading,
  recoverable expiration, empty results and actual failures remain distinct.
- Existing behavior remains covered by unchanged regression tests. No live
  monitoring, schedules, production data, remote Git, or product deployment.

## Work allocation and interruption

Draft common API contract (must be frozen with browser contract before launch):
`GET /api/incidents?view=history-v2&component=...&state=...&limit=...&cursor=...`.
The opt-in response has `incidents`, `nextCursor` (string or null), and
`snapshot: {id, expiresAt}`. Cursor continuation retains first-page membership,
ordering and displayed incident values, including after state updates and late
backdated inserts. A fresh request without cursor creates a new snapshot. Retention
is 30 minutes; expired cursors return 410 with `error: history_snapshot_expired`.
Cross-filter cursor reuse returns 400. The unchanged default route retains the
pre-feature API contract. `continuity_acceptance.mjs` currently covers snapshot
continuity, filter rebinding and expiration; browser and legacy tests are still to
be completed and verified before any study launch.

Use storage/API and browser owners plus a fresh integration successor. Both owners
receive the entire identical request, constraints, acceptance interface and ordinary
coordination notes. Integration is not a secret third feature assignment.

Introduce one deterministic ownership interruption at a named implementation
checkpoint, not a timed kill chosen after seeing results. A fresh owner successor
continues from exact source, detailed handoff, notes and tests without the original
conversation. Freeze the checkpoint and required handoff contents before trials;
count checkpoint administration in both arms. Do not manufacture reviewer findings.

PI-aware workers additionally have only their arm's enrolled PI context and local
presence/reporting. No extra requirements, hidden precedents or evaluator hints are
exclusive to PI. Ordinary workers retain the same underlying facts and peer notes.
Missing context is reported separately from missing PI capability.

## Repair gates required before collecting results

1. Outer filesystem allowlist: only own checkout, read-only peer checkouts,
   explicit notes/coordination and pinned tooling. No host skills, previous trial
   arms, global snapshots, private provider config or original conversations.
   New `experiments/isolation_v2.py` is separate from the preserved v1 launcher.
   Shared host networking is a stated limitation, not hostile-tenant isolation.
2. Actual worker preflight for EACH model and condition: local HTTP server,
   Chromium navigation, local Git commit, detailed handoff, separate final output,
   failed read of unrelated context, and real scoped PI commands in aware condition.
   A deterministic external preflight alone does not satisfy this gate.
3. Review source clone PLUS a source-bound handoff bundle. `review_bundle.py`
   preserves originals and hashes, exports neutral names with explicit redactions,
   and fails on missing artifacts. Evaluator retains original-to-review mapping;
   reviewer receives redacted artifacts/manifest and reports blinding clues.
   Perfect blinding cannot be guaranteed from content.
4. Same frozen common API/browser acceptance in all arms, verified to fail against
   the feature-less base for expected reasons. Negative tests must include races,
   cursor/filter mismatch, expiration and legacy compatibility before freezing.

## Models, budget and ordering

Report Codex and Qwen as separate model strata; do not pool them into one effect.
Hold model, reasoning, context, harness, concurrency and time limits equal between
baseline and PI-aware conditions WITHIN a stratum. Counterbalance treatment order
and publish failed/preflight/timed-out attempts rather than silently replacing them.

Qwen must expose at least 100,000 context tokens, verified from the running service
configuration and a bounded large-context probe, not just recipe configuration.
Enable thinking. Use high/xhigh only if the actual serving/harness interface supports
it; preserve evidence of accepted settings and returned reasoning telemetry where
available. Do not use the old review helper's default `enable_thinking=false`.
The current canonical recipe requests 262,144 tokens; deployment verification is
still pending. More context capacity is not a requirement to pad every task prompt.

Allow a generous renewable execution budget (initial target 60 minutes per worker,
not the old 10-minute correction cutoff). Output/reasoning budgets must leave room
for real implementation and final evidence; record truncation distinctly. Extend
for ongoing useful progress consistently in both arms, recording the extension.
No silent infinite retry loops or relabeling harness failures as model failures.

A second admitted two-host Qwen replica may enable two owners in parallel. Verify
the controller supports simultaneous bindings/placements for this capability before
assuming a second ensure creates an independent service. Isolate arm folders and
record per-endpoint placement, contention, warmup and actual concurrency.

Primary measures: effort to accepted integration including setup, model and human
time, intervention count, concrete defects, duplicated work, successor recovery,
correction/re-verification and coordination overhead. Both succeeding remains a
valid result. Do not tune acceptance after unblinding to force a PI advantage.

## Preparation history, not study outcomes

The initial Qwen lifecycle request `op-23ff2b94d96b7af1fabe3fdf` failed: node job
results on DGX1 and DGX2 state `Qwen target/drafter model mount is unavailable`.
The controller recorded terminal cleanup results. This is an environment/runtime
preparation failure, not PI or Qwen model-quality evidence.

After registered-share recovery and a fresh executable dry-run, the new operation
`op-8120f188022bdea7ed063feb` succeeded on DGX1+DGX2 at 13:50:22 UTC. Binding
generation 19 published `http://10.10.10.101:8078/v1`. Temporary API credentials
were audited and revoked. No conflicting operation was replaced.

The live service reports `context_length: 262144` and `max_req_input_len: 262138`.
A bounded preflight then processed 100,598 prompt tokens with thinking enabled and
`reasoning_effort: xhigh`, correctly retrieved both end markers, and reported 98
reasoning tokens (112 completion tokens total) in 54.133 seconds. The model's
tokenizer template rejected `high` and stated support for `xhigh`, `medium`, and
`low`; generic OpenAPI's broader enum did not establish model-specific support.
Evidence: `state/project-intent/evaluations/study03-preparation/qwen-context-20260906.json`
under the workspace root. This verifies context acceptance and observable thinking,
not long-context coding quality or that effort levels scale in a quantified way.
No Study03 A/B trial has been launched yet.

On 2026-09-06, the new isolation layer passed four focused tests alongside all six
v1 harness tests. Deterministic Chromium preflight evidence is preserved at
`/tmp/pi-isolation-browser-v2-gi6aa02l/preflight.json`. A fresh Codex CLI worker
(`gpt-6-astra`, medium) then completed the actual browser/Git/hidden-context/handoff
preflight in 57.141 seconds, with evidence under
`/tmp/pi-codex-worker-v2-1vw414xi/artifacts/` and source/handoff in its `worker/`.
This is neutral harness validation, not a PI-aware preflight or A/B result.
