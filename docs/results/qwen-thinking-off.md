# Qwen thinking off · one PI-only project

[All results](../../RESULTS.md) · [Measurements](qwen-thinking-off-measurements.json) · [Profile switches](../PI_FOR_QWEN.md)

**7/7 accepted in 2m 27s. Both workers finished; no timeouts.** Thinking was
disabled in all 44 recorded provider requests, with zero reported reasoning tokens
and no reasoning stream observed. Confidence phrase off; no ordinary run.

| Trial | Executed UTC | Integrated | Producer | Consumer | Project time | Worker time |
| --- | --- | --- | --- | --- | --- | --- |
| C1 | Sep 9, 21:29:57–21:32:24 | **7/7 accepted** | 7/7 | 7/7 | **146.669s** | 278.968s aggregate |

## Same problem, different thinking profile

Original **non-torture** seven-seam fixture and unchanged checker. Native Qwen Code
**0.23.2**, `qwen38-27b-dflash2` on the freshly resolved DGX1+DGX2 service;
230,000 context, 32,768 output cap, native compaction at 85%. Two fresh concurrent
producer/consumer sessions shared one disposable project. PI **v0.05 unchanged**;
research route **`pi-for-qwen/v1`**, thinking **off**, confidence **off**, PI **on**,
exactly **one** project. The provider's Medium field remained set alongside
`enable_thinking: false`; native generic effort was `none`. No High/XHigh.

Reused only the preceding batch's hash-bound CLI runtime bytes, not worker homes,
transcripts or project artifacts. Fresh fixture, sessions and PI state; no human
repairs, follow-up messages, replacement run or production changes.

## What worked—and what still did not

Both workers enrolled and read integration context. The consumer explicitly
recognized the producer's active migration, but its first implementation still
imported the obsolete `NAMES` and `REFUNDED`. It subsequently inspected migrated
source, replaced those imports and updated label behavior itself.

The producer also detected that break and attempted the same import repair at
**89.546s**, after the consumer's import correction at **78.226s**. Qwen Code's
edit guard rejected the producer attempt, requiring a fresh read. Its next read
showed the consumer's corrected file. **One redundant repair attempt; no second
retained import fix.** No repair claim/ack agreement was observed. This is not
evidence that PI prevented duplicate repair or established exclusive ownership.

Further integrated checks caught two formatting issues: the consumer corrected
`10.0%` to `10%`; the producer corrected its helper's `2.0 days` result to integer
days. Each retained useful changes in its primary area. Both refreshed context
and released presence, although PI usage had friction: the consumer corrected
invalid enrollment flags, and the producer replaced an invented
`integration_context.refresh` command with `start`. The producer's final assertion
that `start` also updates the heartbeat is not verified behavior: orientation is
read-only.

```text
Elapsed      0s          58s       78s    90s               133s    147s
Consumer     ├────────── labels ── imports fixed ──────────┤
Producer     ├──────────────────────── rejected duplicate ─────────┤
Final checker                                                     7/7
```

Positions are compact; labels use measured event times, rounded to seconds.
Both workers were active for about 133s; concurrency factor **1.909**, maximum two.

## Compute and comparison

| Worker | Duration | Input | Cached input¹ | Output | Reasoning | Requests |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Producer | 146.119s | 1,089,250 | 1,050,048 | 7,634 | 0 | 23 |
| Consumer | 132.849s | 879,892 | 852,928 | 6,805 | 0 | 21 |
| Total | 278.968s | 1,969,142 | 1,902,976 | 14,439 | 0 | 44 |

¹ Cached input is included in input, not additional tokens. All requests reported
usage. Aggregate input plus output was **1,983,581 tokens**, mostly cached input;
this is not a unique-context size or a billing estimate.

The previous thinking-on/confidence-on project scored **0/7 in 488.025s**, with
23,563 reasoning tokens and 1,108,925 aggregate input-plus-output tokens. This
thinking-off project finished sooner and passed, but used more aggregate input
through more model turns. These are **one run per profile**, not proof of a stable
speedup or a PI effect; the preceding profile also had the confidence sentence.
The earlier phrase-free Medium PI batch scored 7/7, 6/7, 7/7.

**Remaining problem:** shared awareness did not stop a stale initial implementation
or a duplicate repair attempt. A separately authorized repeat would test whether
this thinking-off profile reliably retains correctness and timely reconciliation,
including whether native edit guards keep resolving collisions. No further run
was launched or queued.

## Evidence

Batch: `20260909-qwen-thinking-off-v1`, project `C1/seam-project-ype1r9fh`.
The public ledger preserves worker identities, exact timing, usage, per-seam
checks and source hashes. Final acceptance is post-exit, not a continuously
observed time-to-first-correct measurement.

- Frozen batch SHA-256: `b11879a9735af5bd91a5ce98f029532268903f48159915fc61da482cdea30442`.
- Plan SHA-256: `964c5c75336504edd7fa11d2ffb71f2c200699ebdc11b14bb0cb65a5ea82d06b`.
- Profile route SHA-256 unchanged: `f44db5d71bdfd8628608cc09bbb7c4e6ab52cc9c3b2d2bda9a00a534eb9c8214`.
- Seven-seam recorder SHA-256 unchanged: `adee913e5cc070a1ba2b09a02d5fe7f6bc026c5ac84bb60a062d68bd4ce54628`.
- **20 focused harness tests passed** before this run; frozen native CLI/isolation
  and PI preflight passed. No harness or product edits were needed.
