# Study 02 packet: shareable incident history

Status: execution protocol, not a completed study. Do not relabel the first pilot
or its repairs as a second A/B result. Project Intent remains unchanged.

## Product request given identically to both arms

In a disposable SayHi Status fork, let a visitor browse incident history by
component and incident state, load additional pages, and share the selected view
through a URL. Preserve the existing public status summary and report submission.
No monitored endpoints, scheduled checks, production databases, deployment,
credentials, or canonical source mutations are permitted.

Base: `sayhi-status` commit `92b68abbca805af45f2161409770ebe746146e9f`.
This base has a snapshot limited to the latest 20 incidents; filtering that
truncated snapshot is NOT complete incident-history filtering.

Two simultaneous owners, separate linked worktrees in each disposable arm:

1. **History data/API:** own server-side incident query, bounded pagination,
   validation, public response and focused database/route tests.
2. **History browser:** own filters, URL state, accessible load-more/empty/error
   behavior, browser integration and client tests.

Both see this entire request, both owners' scopes, all architectural constraints,
peer checkout references and ordinary asynchronous notes. They may agree on the
smallest shared interface without waiting for a human. Neither owns peer files.
Shared edits require a bounded coordination note or integration-owner follow-up.
No interface design is secretly supplied to the PI arm alone.

A fresh third worker integrates the delivered commits, tests the complete feature,
and routes bounded corrections to the original owners if actually needed. It has
no original conversation history in either arm. It receives repository artifacts,
notes and handoffs; the PI arm additionally receives its scoped PI context.
This is normal integration succession, not an injected interruption or blocker.

## Frozen acceptance contract

The public GET route is `/api/incidents`, with optional `component`, `state`,
`limit`, and `cursor`. Its JSON response has `incidents` (existing public incident
objects) and `nextCursor` (opaque string or null). This small public envelope is
given to BOTH arms. Workers choose and document cursor encoding and internal
interfaces together; tests never depend on their private encoding.

- Default page size 10; integer sizes 1–50 accepted; invalid/duplicate parameters,
  unsupported filters and malformed cursors receive a bounded 400 response.
- Component values are canonical component IDs. States are `investigating` and `resolved`;
  absent filters mean all. Both filters compose before pagination.
- Order by incident `started_at` descending, then incident ID descending as an
  unambiguous tie-breaker. Continuation excludes already-returned IDs even when
  newer incidents are inserted between requests. No offset pagination.
- Tests include more than 20 incidents, equal timestamps, both states and multiple
  components. Walking pages on a fixed dataset yields every matching incident
  once. Empty results have no next page. Query parameters never become raw SQL.
- Pagination does not promise an immutable snapshot under incident updates or
  deletes. Document this limitation; do not add snapshot storage to solve it.
- Existing `/api/status`, summary, component monitoring and report submission
  remain compatible. No new public mutation endpoint or schema migration needed.
- Browser selectors and URL agree on initial load, reload, back/forward and
  changes. Changing filters clears obsolete pages and cursor.
- If a slow old response arrives after a newer filter selection, it cannot replace
  or append to the current view. Repeated load-more clicks cannot duplicate rows.
- Loading, empty results and network failure are distinguishable. Retry preserves
  selected filters; malicious-looking incident text renders as text, not HTML.
- Keyboard users can operate filters and load-more. Focus is not lost on refresh;
  status updates have useful accessible announcements. Narrow layout remains usable.
- `npm test` and `npm run check` pass. Native browser validation on loopback uses
  deterministic local data only, including deliberately reordered HTTP responses.
  Browser checks validate ordinary races; they are not fabricated worker failures.
- Handoffs identify exact commits, interface decisions, actual evidence and
  remaining limits. Local acceptance does not claim review, merge or production.

## Why this is harder

The first pilot's adjacent features could succeed largely independently. This
feature crosses storage selection, ordering/cursor semantics, an HTTP contract,
browser URL state, asynchronous response ordering and integration succession.
Success requires the pieces to agree, not merely pass each worker's own tests.
Difficulty comes from the product, not unequal information or arbitrary obstacles.

## Matched experiment and launch gates

- Create NEW detached disposable clones with no remotes. Neither arm can write
  the canonical repository. Harness grants only exact worker checkout, its
  disposable common Git directory, and arm-specific notes/coordination directories.
  This is cooperative experiment isolation, not a hostile-agent security boundary.
- Preserve pilot 01's model/reasoning settings (`gpt-6-astra`, medium), or record
  an unavailable-model change BEFORE launching and use it identically in both arms.
- 20-minute initial budget per owner; 15-minute successor budget; at most two
  10-minute owner-correction rounds per arm. Record overruns/failures, never hide
  a failed attempt by silently restarting. Owner timeouts do not imply PI failure.
- CLI sessions are ephemeral. A correction uses a fresh session in the same owner
  role and checkout, supplied the preserved handoff, notes and concrete findings;
  it is not falsely described as a resumed conversation. Both arms use this policy.
  Successor initial integration plus post-correction continuations share 15 minutes
  total; mechanical acceptance time and independent review are measured separately.
- Both arms have normal CLI/shell, source, tests, notes and Git. PI adds only
  existing assignment/start/enrollment/report context, not extra architectural facts.
  Include an actual JSON-file example for `report --input` in the PI instructions.
- New feature assignments must be enrolled for this trial before launch. Do not
  reuse pilot 01 freshness/filter IDs or relabel its provider history. Trial snapshot
  contains only that pair's two owners and integration assignment; no provider
  credentials or global workspace map supplied.
- Capture setup elapsed time from clone creation, including enrollment/export and
  troubleshooting. Capture per-process timing/tokens, integration/correction time,
  human interventions, acceptance defects and coordination administration.
- Freeze task, prompts, acceptance tests, launcher, model/version and source hashes
  before either arm runs. Execute automated acceptance and browser checks against
  the base first: required new behavior must fail for the expected missing-feature
  reason, while existing regression tests pass.
- Run two pairs sequentially: pair A ordinary then PI-aware; pair B PI-aware then
  ordinary. Workers/reviewers are fresh and cannot inspect earlier results or
  opposite-arm artifacts. No overlapping arms or unrelated evaluation subprocesses.
- Randomize opaque candidate labels for fresh independent review. Give the reviewer
  the same requirements and source/evidence, not arm labels or worker transcripts.
  Reviewers may still infer provenance from code; report that blinding limitation.
- Primary endpoint: total effort to accepted integration, including setup and
  corrections. Also report quality, missed constraints, recovery work, human
  interventions, wall time and PI overhead. More tests written is not a quality score.
- Publish all four runs, including failures and setup costs. Two pairs of one
  feature remain a limited pilot, not evidence of general superiority.

## Harness repair evidence

`experiments/cli_harness.py` replaces the old trial-specific launcher for new runs.
Its `--add-dir` includes the resolved, trial-contained Git common directory, and
CLI final output is a separate artifact outside the worker checkout. Detailed
`TRIAL_HANDOFF.md` is never passed to `-o`. Existing artifacts are refused.

Run regression tests and a real sandbox smoke test:

```sh
.venv/bin/python -m unittest discover -s tests -p test_evaluation_harness.py -v
.venv/bin/python -m experiments.preflight_cli
```

The smoke test commits one harmless file in a temporary repository and verifies
different handoff/final-message sentinels survive. It never touches pilot 01.
Its output is harness evidence only, not another PI-versus-Codex study.

`experiments/incident_history_acceptance.mjs` exercises the real worker route over
an in-memory SQLite adapter using repository migrations. Run with `TRIAL_CHECKOUT`
set to the disposable candidate root. It is intentionally red on the untouched base.
It is not a complete Cloudflare D1 emulator or a replacement for browser validation.

The native browser suite and selector contract are now checked in alongside the
API suite. `experiments/shared_contract_study.py` prepares fresh paired-arm setup
and provider enrollment, freezes prompts and actual input copies, requires the
base validation gate, and runs owner/successor/correction stages. Never count setup
as an executed study or launch without the recorded fairness gates.
