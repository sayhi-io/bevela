# Qwen single worker · thinking off

[All results](../../RESULTS.md) · [Measurements](qwen-single-worker-measurements.json) · [Frozen method](../CLI_QWEN_SINGLE_WORKER.md)

**3/3 accepted, 7/7 each.** One no-thinking Qwen Code session can solve the
complete original seven-seam task without PI in these three fresh repetitions.
No timeouts, external repairs or reported reasoning tokens.

## Per-project results · newest first

| Run | Launch UTC, Sep 9 | Integrated | Producer / consumer | Project time | Worker time | Input + output |
| --- | --- | --- | --- | --- | --- | ---: |
| A3 | 21:44:30 | **7/7 accepted** | 7/7 · 7/7 | 72.246s | 71.912s | 505,647 |
| A2 | 21:43:42 | **7/7 accepted** | 7/7 · 7/7 | 47.926s | 47.385s | 286,224 |
| A1 | 21:43:00 | **7/7 accepted** | 7/7 · 7/7 | 41.497s | 41.065s | 198,077 |

Median project time **47.926s**. Whole sequential batch: **162.068s (2m 42s)**
from batch execution start to final completion. Project times include recording
and final verification; worker times exclude that overhead. Setup is separate
in the ledger. These were three projects in order A1, A2, A3—not three workers
sharing one project.

## Thinking-off comparison

| Configuration | Runs accepted | Scores | Median project time | Median aggregate worker time | Median input + output |
| --- | --- | --- | --- | --- | ---: |
| One worker, no PI | **3/3** | 7, 7, 7 | **47.926s** | 47.385s | 286,224 |
| Two ordinary workers | 0/1 | 0 | 44.072s, failed | 79.241s | 241,948 |
| Two workers + PI | **1/1** | 7 | 146.669s | 278.968s | 1,983,581 |

All rows use the original non-torture fixture, thinking off and confidence phrase
off. [Ordinary pair](qwen-ordinary-thinking-off.md) · [PI pair](qwen-thinking-off.md).

**The single-worker path produced accepted projects faster and with less aggregate
model usage than the observed PI pair.** The ordinary pair's shorter failed run
is not a faster accepted result. Samples are small and unequal; this does not
establish population success rates or a general speedup.

The solo worker receives both original task texts in one prompt. Each ordinary
concurrent worker received its own role prompt and could inspect normal shared
source; PI adds related task context and workflow instructions. This is a ceiling
diagnostic, not a pure concurrency-only ablation with equal per-worker information.

## What the worker did

Each session implemented the data migration and its labels in one coherent scope,
then performed its own checks. No peer patch, ownership negotiation or integration
handoff was required. The final frozen checker passed all producer and consumer
groups, including dynamic-data behavior—not only the example outputs.

A3 took longer because it corrected its own discount formatting and pending-status
wording, and moved its ad hoc checks into a test file after assertion/quoting
friction. This was ordinary within-session self-repair, not a hidden retry or
additional worker. All three logs used only reads, edits, writes and shell commands;
no native agent-delegation call was observed.

```text
Batch elapsed
  0s  ├──── A1: one worker ────┤ 42s  7/7
 42s                          ├──── A2: one worker ─────┤ 90s  7/7
 90s                                                   ├──── A3 ─────┤ 162s  7/7
```

Times rounded from recorded starts/completion. Maximum simultaneous workers was
**one** in every project; active-time concurrency factor **1.000**.

## Compute

| Run | Input | Cached input¹ | Output | Reasoning | Requests |
| --- | ---: | ---: | ---: | ---: | ---: |
| A3 | 499,792 | 489,216 | 5,855 | 0 | 16 |
| A2 | 282,210 | 274,240 | 4,014 | 0 | 10 |
| A1 | 194,603 | 187,712 | 3,474 | 0 | 7 |

¹ Cached input is a subset of input. All 33 requests reported complete usage;
every request had thinking disabled and no reasoning stream was observed.
Aggregate repeated input is not unique context size or an estimated bill.

## Interpretation and next question

The underlying programming task is within no-thinking Qwen's capability when
one session owns both sides. The two-worker ordinary failure therefore need not
mean Qwen cannot solve the code; it is consistent with losing compatibility as
separate workers finish against different states.

**Why PI is not the best path on these observations:** the fixture fits in one
short coherent session, so parallelism and PI overhead have no demonstrated
payoff over that session. **A future test should examine** whether larger,
genuinely independent contributions make useful concurrency repay that overhead,
without weakening the control or changing these results. No further trial queued.

## Frozen inputs and validation

Qwen Code **0.23.2**, model `qwen38-27b-dflash2`, resolved DGX1+DGX2 endpoint,
230k context, native compaction, unchanged output/sampling controls. No PI bundle
or task instructions; ordinary tools retained. Existing combined solo prompt
reused verbatim. Three fresh checkouts, native homes and UUIDs frozen before A1.
The final checker remained observer-only. No production/runtime changes.

- New launcher: `qwen-single-worker/v1`; SHA-256
  `9f3818ee96a53d622f4616061fd1e409c3d85675fbfc91ac60800c1dff5b14f6`.
- Batch: `20260909-qwen-single-worker-v1`; SHA-256
  `af7dfae61e1967adebae2dc1b5d59f6c467d0609f64d5063ab8ba36084f09d40`.
- Historical profile route, original recorder, fixture, checker and PI untouched.
- **24 focused tests; 389 total Python tests passed** before model execution.
  All three isolated native CLI/preflight checks passed before batch launch.

Per-run ledger retains exact source/result/plan hashes, identities, timestamps,
checks, usage completeness and infrastructure status. Raw transcripts stay local.
