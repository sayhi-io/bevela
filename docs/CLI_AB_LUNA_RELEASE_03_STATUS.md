# Luna release Study03: invalidated, not an A/B result

> Historical source recovery. Historical v1 invalidation and oracle-repair summary, not a current study status or a valid matched result. Later attempts remain distinct; diagnostic passes are not rescoring.
>
> Status and authorization statements below describe their original writing;
> they are not current launch permission or new validation claims. See
> [Results](../RESULTS.md) for the maintained result index. Archive references
> identify private evidence, not public downloads; no raw artifacts are included.
> This sanitized documentation copy is not a replacement for a historical sealed
> input. Original frozen source and evidence remain unchanged in their archives.

The first frozen scored sequence was stopped after A-control's independent
acceptance and during its review. A-aware, B-aware and B-control were prepared
but never launched. No valid PI efficacy or productivity comparison exists.

## What happened

The frozen browser navigation test derived expected IDs from the live DOM row
count after Back. Snapshot metadata could already match the URL while the rows
were still loading. It therefore sometimes captured an empty expected list and
waited for zero rows after the correct ten matching incidents had appeared.

Ten instrumented repetitions against unchanged candidate commit
`4a33a9d90a4f80d441c1d9f16a3e5abc3ab240e0` produced four errors and one assertion
failure. All five captured empty expectations alongside the ten correct displayed
IDs. This is evaluator evidence, not a baseline-model or PI failure.

The scored driver was terminated; no candidate or review process remains running.
Original source, worktrees, commits, handoffs, gates, partial review, preflight and
rehearsal artifacts remain intact. The 13 original frozen input hashes still match.
No candidate was repaired by the coordinator and no result was silently rescored.

## Separate repair

[`luna_release_browser_v2.py`](../experiments/luna_release_browser_v2.py) retains
seven frozen browser tests and overrides navigation once. It captures complete
first-page IDs before navigating, then checks those stable IDs and snapshot
bindings after reload, Back and Forward.

Ten repetitions of the complete proposed v2 suite passed **80/80** tests, with
zero errors, failures or skips, against the same unchanged candidate. Independent
Luna-medium review confirmed eight collected tests, no weakened assertion and no
blocking finding. This supports the repair, not universal race freedom or product
acceptance. V2 is outside the original freeze and has not been used for scoring.

Repository validation: 139 Python tests and 13 Node tests passed; diff checks
passed. Source changes are uncommitted in `agent/luna-release-study`; no canonical
product source, deployment, push or merge was performed.

## Evidence and next step

Private archive ID: `20260908-luna-release-03` (members below are not public links)

- `freeze.json`: original immutable scored protocol and input hashes.
- `invalidation.json`: stop reason and which arms did/did not start.
- `diagnostics/navigation-race/`: original assertion instrumentation and failures.
- `diagnostics/navigation-v2/`: proposed repair, source binding and 80-test result.
- `arms/A-control/evaluation/`: original independent gates and partial review.
- `arms/rehearsal-{control,aware}/`: completed unscored rehearsal evidence.

A new explicitly versioned freeze and fresh scored attempt identifiers are needed
before relaunching the matched comparison. Keep the task, Luna-medium model,
budgets and counterbalanced order unchanged; include the repaired oracle and
preserve this invalidated attempt separately. Do not relabel the old A-control
candidate as a new matched run or count diagnostic repetitions as scores.
