# Qwen Code · distributed candidate 2

[All results](../../RESULTS.md) · [Method and amendments](../CLI_QWEN_DISTRIBUTED.md) ·
[Frozen objective](../../experiments/assets/distributed_v2/fixture/OBJECTIVE.md)

**Completed: five ordinary and five PI projects; neither arm produced an accepted
project.** All failures are retained. Executed September 9, 2026,
12:47:31–18:00:57 UTC, with sequential projects and four concurrent workers each.

| Condition | Accepted | Median final project time | Median worker time | Median observed tokens | Timed-out workers |
| --- | ---: | ---: | ---: | ---: | ---: |
| Qwen ordinary | **0/5** | 1,800.970s | 7,110.941s | ≥6,611,938 | 17/20 |
| Qwen + PI v0.05 | **0/5** | 1,800.988s | 7,200.206s | ≥6,730,229 | 18/20 |

These are **15-group scores**, not the original seven-seam scores. Both arms'
median score was 5/15. All projects exhausted at least one worker's 30-minute
budget; no accepted intermediate state was observed. These durations measure
failed attempts, not time to a correct product. No human repaired a project after
launch; three between-project inspection pauses are recorded below.

**Finding:** this cohort does not show a PI benefit. **Possible limits:** 35/40
workers timed out, long reasoning/stream limits constrained useful output, and
most PI workers did not complete enrollment. **Next test should distinguish**
native Qwen/tool throughput and reliable PI operation from software coordination,
using separate bounded runtime and protocol checks before another frozen A/B.
Adding a second model instance is an infrastructure change, not a repair to these
historical projects or proof that PI would have helped.

**Separate recovery check:** after infrastructure recovery, a fresh native Qwen
Code 0.23.2 session on DGX1+DGX2 passed a tool/write smoke in **17.587 seconds**
with 230k context and server xhigh thinking. This demonstrates basic runtime
operation, not sustained four-worker throughput or PI protocol competence; it is
outside the ten-project cohort. A second-pair launch failed on DGX3 alongside its
known GPU firmware fault and was cleaned up without disturbing DGX1+DGX2.

[Structured per-worker measurements and exact failures](qwen-distributed-measurements.json)

## Every project · newest first

All rows are unaccepted. “Local” refers to component-local test suites, not
integration. Unchanged legacy tests can pass without a migrated implementation.
Tokens are observed input + output lower bounds; cached input and reasoning are
subsets, not additional charges.

| Project | Start UTC | Score | Local | Final seconds | Worker-s | Tokens ≥ | Timeouts |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| C5 · PI | 17:30:56 | 5/15 | 4/4 pass | 1,801.002 | 7,024.302 | 7,026,095 | 3/4 |
| B5 | 17:00:55 | 5/15 | 4/4 pass | 1,800.970 | 7,200.250 | 4,101,882 | 4/4 |
| B4 | 16:30:53 | 5/15 | 4/4 pass | 1,801.032 | 7,110.941 | 6,611,938 | 3/4 |
| C4 · PI | 16:00:52 | 5/15 | 4/4 pass | 1,800.988 | 7,200.285 | 7,592,314 | 4/4 |
| C3 · PI | 15:25:05 | 5/15 | 4/4 pass | 1,802.165 | 7,204.275 | 4,980,488 | 4/4 |
| B3 | 14:55:03 | 7/15 | 4/4 pass | 1,801.755 | 7,201.302 | 7,030,710 | 4/4 |
| B2 | 14:25:02 | 6/15 | 4/4 pass | 1,800.847 | 6,915.900 | 7,583,793 | 3/4 |
| C2 · PI | 13:55:00 | 7/15 | Orders: 3 failures | 1,800.917 | 6,528.379 | 5,947,105 | 3/4 |
| C1 · PI | 13:21:53 | 4/15 | Settlement: 1 failure, 2 errors | 1,800.976 | 7,200.206 | 6,730,229 | 4/4 |
| B1 | 12:47:31 | 4/15 | 4/4 pass | 1,800.928 | 6,587.995 | 4,579,008 | 3/4 |

### Exact failed integration groups

All ten failed `migration_and_restart`, `validation_is_atomic`, and
`integrated_replay`. The additional failures were:

- **C5, B4, C4, C3:** `deferred_settlement`, `cancellation_reordering`,
  `reporting_late_join`, `mixed_wire_versions`, `legacy_workflow`,
  `partial_return_pipeline`, `partial_return_cancellation`.
- **B5:** `money_and_quotes`, `reservation_atomicity`, `order_recovery`,
  `durable_order_outbox`, `partial_return_recovery`, `partial_return_pipeline`,
  `partial_return_cancellation`.
- **B3, C2:** `reporting_late_join`, `mixed_wire_versions`, `legacy_workflow`,
  `partial_return_pipeline`, `partial_return_cancellation`.
- **B2:** `deferred_settlement`, `cancellation_reordering`, `mixed_wire_versions`,
  `legacy_workflow`, `partial_return_pipeline`, `partial_return_cancellation`.
- **C1, B1:** `order_recovery`, `durable_order_outbox`, `reporting_late_join`,
  `mixed_wire_versions`, `legacy_workflow`, `partial_return_recovery`,
  `partial_return_pipeline`, `partial_return_cancellation`.

## Useful work, rework and PI cost

Maximum concurrency was four in every project; overlap factors ranged from
3.627 to 4.000. That is process overlap, not productive reasoning time.
Native writes and retained source show these component contributions:

| Project | Retained component implementations |
| --- | --- |
| C5, B4, C4, C3 | Catalog, Orders |
| B5 | Settlement, Reporting |
| B3, C2 | Catalog, Orders, Settlement |
| B2 | Catalog, Orders, Reporting |
| C1, B1 | Catalog, Settlement |

No cross-owner overwrite was observed. Repeated source investigation occurred,
but there is no defensible token-level duplicate-work ratio. Ordinary B3/B4
Orders workers reread Catalog and corrected receipt use. Static review also found
incompatible return assumptions; examples and their limits are recorded below.
Missing implementation and runtime limits prevent a clean attribution of every
integration failure to concurrent stale state.

Only **7/20 PI workers initially enrolled**, six with explicit edit access.
Two enrolled before implementation, two after starting it, and three did not
implement their component. Two later low-level presence writes lacked the earlier
rich binding metadata: C4 Catalog while active and C5 Catalog on release. An
inactive release record is not equivalent to losing an active declaration; neither
was silently counted as preserved rich enrollment. No repair
claim/ack/complete or report workflow was observed.

The recorder identified **39 PI-tagged shell calls**, totaling **19.935 worker-s**
and **588,256 returned bytes**. Calls sometimes bundled ordinary shell work;
their spans are neither PI-exclusive overhead nor incremental prompt tokens.
Zero recorded tagged tool errors does not mean every PI command succeeded:
shell bundling and internal command outcomes limit that counter. Reading/reasoning
about PI output is not separately measurable. Per-worker counts and incomplete
usage flags remain in the ledger.

### Measured representative timelines

Seconds are relative to first launch, rounded; all four workers began within 3ms.
First writes are observed implementation events, not estimates of when thought began.

```text
B1 ordinary
    0  Four workers launch
  921  Catalog first implementation write
1,188  Catalog exits successfully
1,322  Settlement first implementation write
1,800  Orders / Settlement / Reporting hit budget
1,801  Final verification: 4/15, not accepted

C2 PI
    0  Four workers launch
  788  Catalog first implementation write
1,128  Catalog exits successfully
1,378  Settlement first implementation write
1,633  Orders first implementation write
1,800  Orders / Settlement / Reporting hit budget
1,801  Final verification: 7/15, not accepted; Orders local failures
```

These examples show retained progress and incomplete projects, not an A/B speed
win. No accepted result exists for a compute-to-success comparison, and no
single-worker ceiling was measured. PI's concurrency-substrate value remains
unestablished for this Qwen configuration.

## What this comparison measures

Four native Qwen Code workers own Catalog, Orders, Settlement and Reporting in
one disposable shared checkout. The existing candidate-2 migration, durable
partial-return problem and **15-group acceptance checker are unchanged**. Both
arms have the same complete task information and ordinary development tools.
Only C receives the frozen PI worker workflow and shared project state.

This is the requested new Qwen stratum, not a resumption or replacement of the
earlier Sol calibration. There is no Qwen single-worker ceiling or separate PI
protocol-competence calibration, so a failed project cannot by itself distinguish
programming limits, runtime limits and coordination failure.

## Runtime and authority

- **Qwen Code 0.23.2**, installed and configured through SparkOps' native Twin
  Plane tool APIs in the dedicated `qwen-distributed-study` plane. Other planes
  and active runtimes were not upgraded.
- Served model **`qwen38-27b-dflash2`**, the already loaded local TP2 service.
  Its advertised capacity is 262,144 tokens; the CLI is bounded to **230,000**,
  with native automatic compaction enabled at 85%.
- Requested high reasoning maps to **server `xhigh`**, with thinking enabled:
  this server rejects literal `high`. Response limit **32,768**, temperature
  **0.6**, top-p **0.95**. This is not equivalent to Codex High calibration.
- **1,800 seconds per worker**, four concurrent workers per project, projects
  strictly sequential. All workers share one inference service; this is not four
  independently reserved GPUs/model instances, and unrelated load was not excluded.
- Native Qwen Code owns its model loop, tools, compaction and retries. The adapter
  records transport and execution; it does not steer coding or provide answers.
  No cloud fallback, evaluator repair or follow-up assignment is injected.

SparkOps deployed the managed binary and endpoint configuration. The experiment
uses read-only snapshots of that binary as isolated native processes, **not
SparkOps Actions or managed workspace execution receipts**. Bevela has no SparkOps
runtime dependency. A fresh native smoke produced a real tool effect before the
batch; it is separate from the ten project trials. The stale historical SparkOps
lifecycle binding was not relabeled healthy or used to justify a model reload.

## Measurement semantics

Acceptance requires every integration group and the required component-local
checks, with protected inputs unchanged. A native worker's successful exit is not
project acceptance. Legacy component tests can pass while that component has not
implemented the migration at all.

Project time runs from the first native launch through final verification; summed
worker time is separate. Failed projects have **no measured time to an accepted
result**. Recorded tokens are lower bounds when interrupted requests omit usage;
cached input and reasoning output are subsets, not additional token charges.

Retained implementations are corroborated by native writes and final source
history. Mere process overlap, repeated repository inspection and source-observer
triggers do not establish productive coding time, authorship or duplicated work.
PI-tagged tool spans may include ordinary shell work, and observed result bytes
are not a measurement of PI-attributable prompt tokens.

## Integrity and limitations

Review of the completed projects found no observed
cross-owner overwrite. That does not mean all concurrent assumptions were
compatible: in **B5**, Settlement emits a per-return `refund_minor`, while
Reporting expects `amount_minor` and treats values as cumulative maxima.
Reporting last inspected Settlement before its implementation changed and then
tested against its own assumed payload. This is a concrete source-review finding,
not an additional executed failure: the recorded return checks stop earlier at
unchanged Catalog APIs. Conversely, ordinary Orders workers in **B3 and B4**
reread Catalog and retained actual receipt-consumption corrections. PI does not
have exclusive credit for cross-component repair.

Each project has a fresh source tree and four fresh native homes/session UUIDs.
Workers cannot see prior trials, observer artifacts, reference implementations,
peer transcripts or operator credentials. Native instruction-delivery auditing
used a fake endpoint without model inference and confirmed PI instructions in the
outgoing context; that verifies delivery, not adherence.

The source observer is passive. Its 100ms, non-atomic snapshots are checked only
after worker exit, without feeding results back to workers. Final acceptance uses
the frozen checker on an isolated copy, never a worker-edited checker.

Three **between-project sequencing amendments** preserve the original failures:
first to distinguish expected process-budget termination from infrastructure
failure, then to recognize its chunked-response exception, and finally to
recognize an exactly corroborated native stream cancellation. No project was
retried, replaced, extended or repaired. Their inspection pauses are batch
overhead, not coding-worker time or a claim of uninterrupted automation.

C3 Settlement hit Qwen Code's native **900,000ms stream-lifetime limit** and retried
inside its own session. The cap remained unchanged. Separately, v1 relay shutdown
exposed a main-thread/handler HTTP-response cleanup race in C1 and C4; raw
diagnostics remain evidence. It was not repaired during this cohort. Neither
runtime limitation is automatically attributable to PI or to a programming error.

Private native profiles, transcripts, runtime state and tool outputs remain in
the local evidence archive. The public ledger is an allowlisted projection of
measurements, identities and hashes, not a transcript dump.
