# CLI A/B pilot 01: Status freshness and component filtering

Outcome: both teams delivered the requested combined behavior and passed blinded
independent review. This pilot did **not demonstrate an implementation-quality,
coordination or speed advantage from Project Intent**. It demonstrated usable
structured observation/handoffs, not their net productivity value. One run cannot
establish that PI generally helps or hurts.

## What actually ran

Four fresh ordinary Codex CLI workers implemented two useful product changes on
isolated copies of SayHi Status: truthful observation freshness across public
snapshot/page/tests/docs, and shareable component filtering across API/page/tests/docs.
These were coordinator-selected example-repository features, not asserted live
Status-owner assignments. No actual product worktree, service or deployment changed.

Each arm had a freshness worker and a filter worker, separate worktrees, identical
requirements and an ordinary notes channel. The aware arm additionally used actual
PI discovery/start/enrollment/reporting against two provider-enrolled pilot records
(SAYINT-12 and SAYINT-13) and an isolated exported snapshot/presence/report feed.
No provider credentials or global workspace snapshot went to trial workers.
Both teams preserved global health/freshness context while filtering local display.
No blocker, architectural revision, collision or review finding was injected.

Baseline Status SHA: `92b68abbca805af45f2161409770ebe746146e9f`.
PI CLI: running immutable `617f5957bcb602997f8f54d7a0faa4171006a5f4`,
tree-identical to main merge `f57251e38e59744abe820dbecba4e5817aea81ad`.
Codex CLI 0.153.4, same configured gpt-6-astra/medium, Node v22.23.2.

## Observed results

| Measurement | Ordinary CLI | PI-aware CLI |
| --- | --- | --- |
| Parallel implementation phase (slower worker) | 320.02 s | 390.02 s |
| Bounded integration successor | 95.80 s | 93.64 s |
| Combined source tests | 49/49 | 41/41 |
| Same independent acceptance checks | 11/11 | 11/11 |
| Blinded acceptance-blocking findings | 0 | 0 |
| Human intervention requests | 0 | 0 |
| Natural source merge conflicts | page renderer | page renderer and README |

Test counts are not quality scores. Both met the same acceptance rubric. The reviewer
also reported six passing date-boundary diagnostics per candidate. Node VM UI tests
are not native visual, keyboard or screen-reader verification; that remains unproven.
A non-blocking observation concerned the control UI test harness's permissive DOM
mock, not a discovered defect in its page. No post-review correction was required;
the coordinator reran both test/syntax/acceptance gates after review with no source
changes. These are local results, not actual GitHub CI or production assurance.

Worker plus integration CLI usage (not including coordinator/reviewer/setup):

| Reported tokens | Ordinary CLI | PI-aware CLI |
| --- | ---: | ---: |
| Input, including cached | 1,259,944 | 1,466,172 |
| Cached input subset | 1,104,512 | 1,329,664 |
| Output | 18,251 | 21,475 |

These are CLI-reported counts, not dollars. More total input did not mean more
uncached input; no cost conclusion follows without the relevant accounting.

## What helped, what did not, and actual friction

The ordinary team used notes effectively without PI. The aware team also used notes,
plus discoverable leases/readiness/handoffs. Both integration successors recovered
the correct full-snapshot/global-warning intent. No observed PI-specific message
changed a decision that the control failed to make. No participant stalled on a
planner dependency. PI did not prevent ordinary textual merge conflicts, nor was
that its promised authority.

One aware worker supplied inline JSON to `report --input`, which expects a filename;
it recovered itself using a file. This is concrete CLI discoverability friction,
not a need for another workflow service. A small help/example clarification is a
candidate follow-up; no implementation change was made during the experiment.

Both arms encountered a launcher environment defect: workspace-write permissions
omitted the separate Git common directory. They completed code/tests and handed off
instead of bypassing permissions. The coordinator sealed the delivered files and
resolved Git index state after the integration agents resolved source conflicts.
This is harness/environment-profile debt, not a PI model defect. The launcher also
reused a detailed handoff path for final-message output, shortening some saved
handoffs; original detailed command evidence remains in JSONL. Fix both setup defects
for future trials rather than adding PI features to compensate.

## Limits and next decision

This was a strong baseline: both prompts named the peer and supplied the same complete
requirements. It tests incremental PI value over a good handoff, not discovery of
otherwise-unmentioned workspace work. Fixed arm order, shared host, one integration
overlapping the aware implementation, model variation and incomplete setup-time
instrumentation limit causal conclusions. Source/read isolation was cooperative
same-user plus write sandbox, not separate-host confinement. Command-path audits
found no cross-arm references; that does not prove hidden reads impossible.

Keep direct CLI work first-class; retain optional PI observability and cheap context.
Do not expand the execution graph or bridge on a claimed productivity benefit this
pilot did not establish. Next trials should fix setup, counterbalance ordering and
exercise ordinary discoverable adjacent work without preassembling its entire
context in the primary prompt. A later packet-only comparison can distinguish better
project information from live coordination. At least two more distinct paired tasks
remain before any directional multi-task conclusion. No general verdict yet.

## Provenance and successor

Control sealed candidate: `249c7dec6d92abfba522e3ee615aaba39c4afb9b`.
Aware sealed candidate: `afeaebac54e3e2bb6679ec58de5d78757b83100f`.
These are disposable local commits, not product-main merges or PRs.

Artifacts retained outside Git under
`/home/meanaverage/sayhi/state/project-intent/evaluations/20260906-status-cli-pilot-01/`:
frozen tasks, enrollment/export, prompts, launcher, command logs, timings/usage,
source manifests, binary patches, independent review, gate logs and source-only
review copies. Raw working area: `/tmp/pi-cli-ab.fCugoI`.
Review mapping (revealed only after review): cedar=aware, larch=control.

The SparkOps durability prototype remains preserved and unwired. No PI runtime
code, service deployment, production credentials or admission boundary changed.
