# Qwen confidence prompt · one PI-only project

[All results](../../RESULTS.md) · [Measurements](qwen-confidence-measurements.json) · [Profile switches](../PI_FOR_QWEN.md)

**0/7 integrated. Both workers finished; neither timed out.** The confidence
sentence did not prevent extended repetitive deliberation or an unresolved
producer/consumer compatibility break in this one project.

| Trial | Executed UTC | Accepted | Producer seams | Consumer seams | Project time | Worker time | Intervention |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C1 | Sep 9, 21:14–21:22 | No · **0/7** | 7/7 | 0/7 | **8m 8s** | 9m 20s aggregate | None |

All consumer checks were blocked by the same module import failure. This is **not
evidence of seven independent coding mistakes**. No ordinary project, replacement
trial, evaluator repair or follow-up model run was performed.

## Frozen configuration

- Original seven-seam fixture, **not refund torture**; unchanged checker and acceptance.
- Qwen Code **0.23.2**, model `qwen38-27b-dflash2`, DGX1+DGX2.
- Medium effort, thinking **on**, 230,000 context, 32,768 maximum output,
  temperature 0.6, top-p 0.95; native compaction at 85%.
- Two fresh concurrent producer/consumer sessions sharing one disposable project.
- PI **v0.05 unchanged**, with the existing Qwen session adaptation.
- New experiment route **`pi-for-qwen/v1`**; confidence **on**, exactly one project.

Each original role prompt received only this additional sentence:

> You are very knowledgeable. An expert. Think and respond with confidence.

The route also normalizes Qwen Code's generic effort setting to Medium. Recorded
provider requests used `reasoning_effort: medium` and `enable_thinking: true`;
neither High nor XHigh was requested. No production PI changes were made.

## What actually happened

The consumer implemented labels using the original representations, verified them,
and exited after **71.919s**. It made **no PI CLI calls** and read no PI operational
documents. Its work therefore preceded the producer's migration without recorded
peer enrollment or integration refresh.

The producer read the PI instructions, eventually enrolled, migrated all seven
modules, refreshed context, and released its registration. Its own helper checks
passed. It then explicitly tested and recognized that `presentation.py` could no
longer import `NAMES`; it also identified the removed `REFUNDED` and stale unit
assumptions. It left those repairs to the consumer, which had already exited.
Its final answer accurately called integration **pending/unverified**, not accepted.

This is an observed stale-consumer and unresolved-handoff failure. PI was available,
but only one worker enrolled. The record does not establish that both workers
followed PI and PI failed to expose their shared state.

The producer's fifth model request took approximately **193 seconds** and reported
**10,502 reasoning tokens**. Inspection found repeated reconsideration rather than
a repeated tool-retry sequence. The confidence sentence did not eliminate that
behavior in this sample; this is not proof that it caused the integration failure.

## Time and compute

| Worker | Native duration | Input | Cached input¹ | Output | Reasoning² | Requests |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Producer | 487.688s | 849,590 | 809,664 | 27,464 | 21,215 | 15 |
| Consumer | 71.919s | 227,258 | 220,288 | 4,613 | 2,348 | 8 |
| Total | 559.607s | 1,076,848 | 1,029,952 | 32,077 | 23,563 | 23 |

¹ Cached input is a subset of input, not additional tokens. ² Reasoning is reported
separately and must not be added again to output. All 23 requests reported usage.

Project elapsed was **488.025s**, including final recording/verification, not the
sum of worker durations. Setup was 0.250s, archive 0.154s, final verification
0.042s. Worker execution spanned 487.688s; maximum concurrency was two and the
active-time concurrency factor was **1.147**. Both processes exited successfully,
with complete native streams and relay receipts; the integrated source failed.

```text
Elapsed         0s             72s                               488s
Consumer        ├──────────────┤ exited against old representations
Producer        ├────────────────────────────────────────────────┤
Final checker                                                    ✗ 0/7
```

Different files retained each worker's contribution, but the contributions were
incompatible. Overlapping process time alone was not useful integrated concurrency.

## Interpretation and next question

The earlier Medium PI batch scored **7/7, 6/7, 7/7** without this sentence. That
historical cohort is context, not a fresh matched control for this one-run profile.
Neither shorter elapsed time for a failed project nor one failure establishes an
efficiency or causal effect of the phrase.

**Observed problem:** extended deliberation delayed migration while the unenrolled
consumer finished, and the producer left a known integration break unresolved.
**Proposed next test:** thinking off, confidence off, otherwise unchanged, to test
whether disabling deliberation reduces delay while retaining PI onboarding and
integration behavior. It would not isolate an onboarding fix, and has **not run**.

## Evidence and validation

Local immutable evidence: `20260909-qwen-confidence-v1/C1/seam-project-d_ba6r_e`
under the evaluation store. Public measurements retain per-seam failures, native
identities, usage completeness, timing and result/plan hashes. Raw session and
transport artifacts remain local.

| Input | SHA-256 |
| --- | --- |
| Frozen batch | `6958b4c9d073e26a4d34ac3be36070b1ecbb7ad2f1587f2293217c816d03f050` |
| Plan | `402c0cbd4d0ca9be5009ef652b0d7e16a381c68feea56af0c5e8747cb425e4c2` |
| New profile route | `f44db5d71bdfd8628608cc09bbb7c4e6ab52cc9c3b2d2bda9a00a534eb9c8214` |
| Unchanged seven-seam recorder | `adee913e5cc070a1ba2b09a02d5fe7f6bc026c5ac84bb60a062d68bd4ce54628` |

Before execution: **20 focused harness tests and 385 full Python tests passed**;
isolated native CLI and no-model PI preflight passed. The fixture, checker, PI
source and historical recorder were unchanged. Harness tests are not model trials.
