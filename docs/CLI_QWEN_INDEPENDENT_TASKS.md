# Independent requests · Qwen collision study v1

Historical prelaunch status: implemented; prelaunch tests passed. The plan below
does not itself establish model results. For the subsequent September 10 run,
see the [recorded outcomes and evidence limits](results/qwen-independent-requests.md).

Research question: when different user requests naturally touch shared code and
contracts, does PI plus automatic steering help workers avoid or repair incompatible
changes? This is not task decomposition from an identical umbrella assignment.

## Frozen assignment structure

| Worker request | Functional responsibility, not file ownership |
| --- | --- |
| Money | Integer cents, rounding, public money representations, four-store migration, legacy compatibility |
| Recovery | Reservations/orders, retries/restarts, outboxes, deferred capture, cancellation, joins and observable purchase state |
| Returns | Partial returns across inventory, order records, settlement and receipt/revenue projections |

Prompts are literal `TASKS` constants in `experiments/qwen_independent_tasks.py`.
They are different between workers, byte-identical for corresponding workers in
A and B. Each task may legitimately require edits across any component. There is
no assigned integrator, repairer, file division, prescribed order or readiness gate.
No prompt says another task will collide with this one. All three task documents
are available in the shared repository for ordinary discovery. Workers are not
instructed to read all peer tasks at startup. The complete public functional contract
is a reference, not an umbrella assignment to implement everything personally.

## Requirement coverage and unchanged acceptance

Starting Python, component CONTRACT.md files, original local tests, architecture
and the 15-group acceptance checker are byte-identical to distributed candidate2.
Only README, OBJECTIVE allocation prose and task files change, through explicit
versioned replacements. Tests reverse every OBJECTIVE replacement and recover the
exact historical text. Old role tasks never enter worker Git history. This is a
new assignment study, not a claim of identical historical worker-facing inputs.

Coverage audit against the full reference contract:

| Reference requirements | Assigned request coverage |
| --- | --- |
| Common validation, detached JSON, persisted state, version handling | Money migration; Recovery durable updates; Returns preserves these constraints |
| Precision/rounding, original totals, legacy fields and formatting | Money; return-credit arithmetic additionally belongs to Returns |
| Catalog pricing/get/quote and migration | Money |
| Catalog reserve/release, basket validation and stable retries | Recovery |
| Orders public representation and migration | Money |
| Orders place/cancel/recovery and outboxes | Recovery |
| Old wire normalization and compatibility | Money conversions; Recovery validation/deduplication/delivery |
| Settlement migration and money representation | Money |
| Deferred capture/cancellation/replay and balance | Recovery |
| Reporting migration, receipt representation/legacy formatting | Money |
| Reporting delayed joins, state precedence and revenue | Recovery |
| Full partial-return extension including interrupted restore and cancellation | Returns |
| New producer-defined JSON, versioning, docs, return/refund joins and absent-return fields | Returns |
| No private peer-state/parser coupling, old behavior, no new services | All requests constrained by the same reference |

Overlap here describes reviewer coverage, not exclusive implementation ownership;
this table is not mounted in workers' environments. Every functional paragraph
remains available in OBJECTIVE.md. No hidden acceptance requirements are introduced.
The existing joint reference passes 15/15 under the new document packaging. Existing
fixture tests retain alternative JSON representation and incompatible-consumer probes.
This proves preservation and selected checker sensitivity, not exhaustive correctness.

## Arms and controls

- **A:** three ordinary Qwen Code workers; no PI bundle/hooks/inventory.
- **B:** the same three requests and permissions, with the unchanged compact PI
  workflow, filtered CLI and nested-source steering from the previous complex run.
- Three projects per arm, frozen order **A1, B1, B2, A2, A3, B3**. This order is
  chosen before outcomes, not randomized. One project at a time; three workers
  inside each project launch concurrently without an imposed work barrier.
- Qwen Code **0.23.2**, `qwen38-27b-dflash2`, thinking off, confidence phrase off,
  230k context, native compaction, 500 session turns, 500 tool calls per turn,
  1,800-second worker boundary. Native loop guards remain unchanged.
- Fresh checkouts, Git histories, homes and native UUIDs. Prior trials, evaluator
  snapshots, reference solutions and operator credentials are not mounted. The
  network remains available; this is not hostile network/tenant isolation.
- No human intervention, evaluator feedback, forced stale read, timed source
  mutation, wait choreography, resumption, automatic replacement or model fallback.
  Native harness behavior (including native retries) is recorded, not rewritten.
- Failed correctness and native guard failures remain in the sequence. Uncertain
  recording/relay cleanup, infrastructure or protected-input failures stop the batch
  with `stopped.json`, without quietly substituting a run.

## What PI actually knows

Its three task records contain the exact public task prompts. All three requests
have cross-product scope, so each record uses the union of boundaries in the
unchanged public architecture.json. This is deliberately broad, not a hidden map
of predicted collisions, file ownership or peer actions. Workers must declare their
actual paths/seams. No synthetic peer enrollments, claims or reports are inserted.

Steering uses the unchanged 12-file component source/contract allowlist and normal
PI context. It emits bounded notices at native hooks: at most 12/session, 6,000
characters each. It cannot infer authorship or semantic correctness, observe new
files outside that list, or revive a completed worker. Allowlists include own edits.
No test results, evaluator source, suggested fixes or peer transcripts are supplied.
This is **PI plus broad change-notification steering**, not an isolated proof of
semantic impact detection or PI backend-only value. Production PI is unchanged.

## Recording and interpretation

The existing native recorder captures start/end times, literal tool/model events,
transport usage and 100ms source observations. The observer does not score or send
messages during execution. Final verification happens on an isolated copy after
all worker exits, against the frozen checker. Project time is that final verified
boundary, not summed worker time. First passing worker probes and any post-hoc
sampled acceptance times must be separately labeled; neither proves continuous
acceptance between samples. Source snapshots are not atomic across files.

Report all six projects: final 0–15 score and exact failures, component tests,
accepted source vs all-native-worker completion, project seconds, aggregate worker
seconds, native exits/limits, tokens and cached/reasoning subsets, concurrency factor,
PI hook time/notices/suppression, and intervention count. Native tokens are not
direct cost equivalence or an efficiency score.

After completion, trace concrete episodes from tools and source history: competing
implementations, overwritten/discarded work, stale assumptions, source inspection
after notices, voluntary changes in approach, and repairs. Attribute edits using
tool records, not file-change timing alone. Separate duplicate inspection from
implementation. Do not fabricate productive seconds or a duplicate-work ratio.

Call an event prevention evidence only if the trace supports anticipation and
adaptation before an incompatible edit; a notice alone is not prevention. A repaired
break is repair evidence. If both arms pass without meaningful overlap, collision
prevention is inconclusive. If ordinary workers handle the same overlap just as
well, report that. One successful arm does not establish what would have happened
to that identical worker without PI. The sample is exploratory, three projects/arm.

## Commands

```sh
.venv/bin/python -m unittest tests.test_qwen_independent_tasks tests.test_distributed_fixture -q
.venv/bin/python -m experiments.qwen_independent_tasks freeze /absolute/new-batch \
  --runtime /absolute/verified-qwen-runtime --endpoint http://resolved-host:8078/v1
.venv/bin/python -m experiments.qwen_independent_tasks run /absolute/new-batch
```

All six plans, runtime manifests, original/new fixture hashes, prompt/checker hashes,
PI source/manifests, hook dependencies, settings and session identities are frozen
and checked before the first launch. Run cannot override the frozen configuration.
Do not edit the experiment or treatment mid-cohort. Reports and a structured ledger
will be versioned separately after results exist; historical evidence stays intact.

Prelaunch validation: seven focused adapter tests passed, including real filesystem
isolation and hook execution with fake version-only native runtimes (no inference),
three-way native-record entry, sequential cohort execution and no replay. The full
suite discovered 425 tests: 424 passed and one optional native-provider test skipped.
An additional independent reviewer could not start because its Codex account quota
was exhausted; no independent review approval is claimed. The implementing agent
performed the direct source/method review. A transient stale readiness observation
cleared on fresh fleet/semantic observations without restarting or moving the model.

## Observer-only continuation amendment v1

A1 finished with accepted source **15/15**, all three native workers exited 0,
and project time was **1476.974s**. The original controller stopped because its
telemetry classifier required `max_tokens == 32768` on every request. Nine Money
requests instead used 25106–32389 while all model/session identities, reasoning
settings and thinking-off observations remained correct. Installed Qwen Code
0.23.2's `clampOutputTokensToWindow` call lowers the output allowance as prompt
context fills; the native configured ceiling remained 32768. This was an observer
assumption failure, not a changed worker configuration or failed acceptance.

The user explicitly authorized starting the five remaining projects. A separate
`experiments/qwen_independent_resume.py` controller preserves the original study
source, six plans, native settings, original A1 result and stopped.json unchanged.
It freezes an audit amendment, then launches only **B1, B2, A2, A3, B3**, sequentially.
It never resumes or reruns A1, rewrites its result, or inserts model guidance.

The observer audit applies equally to both arms: every request must retain the
correct model, medium wire effort, thinking off, and a positive integer output
budget no greater than 32768. Every actual native setting must match the frozen
template (allowing only the recorder's loopback relay port and the already frozen
PI hooks). Identity, transport, recording, relay cleanup and protected-input
failures still stop execution. Reduced allowances are logged per request. Native
errors remain errors; accepted source and clean worker completion remain separate.

`continuation-v1/` retains the immutable amendment, evidence hashes, separate
per-project audits, launch/completion or stop state. A1's original controls-failure
flag remains visible alongside its corrected audit. This is a disclosed post-hoc
observer correction, not a new treatment or a silent replacement experiment.

```sh
.venv/bin/python -m unittest tests.test_qwen_independent_resume -q
.venv/bin/python -m experiments.qwen_independent_resume freeze /absolute/original-batch
.venv/bin/python -m experiments.qwen_independent_resume run /absolute/original-batch
```

### Timeout-cleanup continuation amendment v2

B1 ended at its unchanged 1,800-second worker limit: all three workers timed out,
final source **13/15**, with failures in `partial_return_pipeline` and
`partial_return_cancellation`; every component-local suite passed. Its final project
window was **1801.372s**. The v1 continuation then stopped because it refused all
transport errors, including socket cleanup at the predetermined timeout boundary.

The user authorized continuation. `experiments/qwen_independent_timeout_resume.py`
adds a post-exit-only audit for `ConnectionResetError`, `BrokenPipeError`, and
`IncompleteRead` on already-successful in-flight responses at/after the actual
deadline. It requires recorded timeout termination (-15/-9) in the bounded cleanup
window, matching request/HTTP-200 response before cutoff, complete native stream
recording and relay cleanup. Errors before cutoff, non-timeout errors, HTTP failures,
changed controls and incomplete evidence still stop the batch. The existing v1
output-budget and identity/settings checks remain in force.

No original file or failed result is rewritten. Separate `continuation-v2/` audits
preserve cleanup errors and worker timeout status. Only **B2, A2, A3, B3** are
launched, sequentially, using the original frozen six-project inputs. A1 and B1
are neither repaired nor rerun. B1 remains an unaccepted 13/15 timed-out project.

```sh
.venv/bin/python -m experiments.qwen_independent_timeout_resume freeze /absolute/original-batch
.venv/bin/python -m experiments.qwen_independent_timeout_resume run /absolute/original-batch
```
