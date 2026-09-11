# Qwen compact PI v2 · one project

[All results](../../RESULTS.md) · [Measurements](qwen-compact-pi-v2-measurements.json) · [Route](../../experiments/qwen_compact_pi_v2.py)

**0/7 in 76.207 seconds. Both workers exited normally.** No timeout, loop guard,
enrollment corruption or attempted `presence` command. However, the consumer
made **zero PI calls** and the producer did not reconcile its migration with the
consumer's implementation.

| Run | Executed UTC | Integrated | Producer | Consumer | Project time | Worker time |
| --- | --- | --- | --- | --- | ---: | ---: |
| C1 | Sep 9, 22:42:45–22:44:02 | **0/7; not accepted** | 7/7 | 0/7 | 76.207s | 113.335s aggregate |

## Frozen treatment

Original non-torture seven-seam fixture and checker; two concurrent Qwen Code
0.23.2 producer/consumer sessions in a fresh disposable project. Model
`qwen38-27b-dflash2` on the freshly resolved DGX1+DGX2 runtime, 230k context,
thinking off, confidence off. Same **260-word prompt** as compact v1.

Only worker-facing change: **CLI adapter v2** hides/rejects the legacy `presence`
command and keeps returned onboarding/refresh commands on the filtered entry
point. General PI backend **v0.05 unchanged**. Exactly one project was frozen
and executed (`--runs 1`); no ordinary trial, injected steering, retries or repairs.
The earlier v1 plans and evidence remain unchanged.

## What happened

- Consumer implemented labels against pre-migration data, ran example checks and
  the existing unittest suite, then exited at **37.316s**. It did not onboard,
  enroll, refresh or release. An unavailable pytest invocation was followed by
  successful unittest execution; this was not a native process failure.
- Producer called `onboard` once, `start` once and `enroll` twice including release.
  It knew the CONSUMER task existed, but explicitly concluded it “must not touch
  presentation.py.” That ownership prohibition was its interpretation, not the
  compact prompt, which says peer assignments are not ownership walls.
- Producer began migration writes at **51.217s**, after the consumer had exited.
  It passed the seven existing tests and checked its new representations, but
  did not reread or run the consumer after migration. It exited at **76.020s**.
- Final acceptance failed all seven integrated seams because `presentation.py`
  still imports the removed `customers.NAMES`; it also retains the old
  `orders.REFUNDED` import and representation assumptions. The checker reports
  the import failure, not seven independently diagnosed label defects.

No duplicate implementation or repair was observed. The native worker intervals
overlapped, but producer implementation began only after the consumer exited:
concurrency factor **1.491** does not demonstrate useful simultaneous implementation.

| Worker | Duration | Input | Cached input¹ | Output | Reasoning | Requests |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Producer | 76.020s | 317,650 | 275,712 (partial) | 3,945 | 0 | 9 |
| Consumer | 37.316s | 184,295 | 179,136 | 1,674 | 0 | 7 |
| Total | 113.335s | 501,945 | 454,848 (partial) | 5,619 | **0** | 16 |

¹ Cached input is included in input. All 16 requests verified thinking disabled
and reported complete input/output and reasoning usage. Total input plus output:
**507,564**, not a unique context size or accepted-project efficiency result.

## Interpretation and next question

The hidden-command safeguard did not encounter an attempted invocation in this
run, so its protection is established by unit tests, not this model observation.
This project still failed without the earlier corruption or loop. **Suspected
remaining problem:** workers can skip the PI workflow entirely or mistake related
assignments for prohibitions, then validate only their own contribution.

A separately authorized next experiment could test whether a supported,
between-turn notification of relevant changed context improves actual uptake
and final source reconciliation. It must not inject task solutions, silently
resume exited workers or claim PI currently supports automatic steering. Nothing
further was launched or queued; one run cannot establish a causal CLI effect.

Nine focused harness tests passed before launch; the complete suite passed
**398 tests**. The public ledger retains the frozen plan, template, adapter and
recorder hashes, per-seam checks and per-worker receipts. Acceptance is post-exit,
not continuously measured first correctness. Raw recordings remain local outside
Git. No production activation, commit, push or merge occurred.
