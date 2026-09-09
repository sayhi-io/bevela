# Original seven seams — historical runs

[All results](../../RESULTS.md) · [Fixture and protocol](../CLI_SEVEN_SEAMS.md) · [Machine-readable measurements](measurements.json)

Seven interdependent seams: prices, stock, weights, discounts, delivery, contacts and orders. Each point requires both the producer and consumer contract to survive. These are correlated groups, not seven independent statistical samples. A module import failure can fail all seven.

## Low-effort A/B/C comparison

| Configuration | Runs | Scores (trial-number order) | Accepted projects |
| --- | ---: | --- | ---: |
| A — Luna Low, ordinary | 2 | 0/7, 2/7 | 0/2 |
| B — Sol Low, ordinary | 3 | 3/7, 4/7, 3/7 | 0/3 |
| C — Luna Low + PI v0.05 | 2 | **7/7, 7/7** | **2/2** |

**Luna Low with PI outperformed both ordinary configurations on final integrated correctness, including the stronger Sol model.** This is the historical A/B/C capability comparison: helping the lower-capability configuration versus increasing model capability without PI. The chronology below preserves the separate execution batches; their model strata are not pooled into a success average.

These historical batches used two preassigned producer/consumer workers per project. PI workers could discover the peer’s future task in PI inventory; ordinary workers received their own task and could inspect the shared source, but did not receive both future tasks as a shared document. PI bundles also contained the broader documentation tree. Host reads/native configuration were not hermetically isolated. Therefore these observations are not an ablation of live coordination versus equal static context. The later [concurrency study](concurrency.md) deliberately equalized task information and limited bundled documents.

Times below are the native **worker execution window**, not time through final verification. Worker-s sums both processes; neither is isolated inference time. Historical token totals were not uniformly analyzed and remain unavailable in the curated data, not zero. Many early batches ran independent projects simultaneously; later concurrency/self-organizing projects ran one at a time. Sub-millisecond launch order within an earlier batch is not a serial task order.

Groups and runs appear newest first by actual UTC launch timestamps. The source result hashes and per-run frozen-plan/input hashes are retained in measurements.json. No raw transcripts, credentials, registrations or private paths are published.

## Sol · Medium and High · ordinary

Started **2026-09-09 03:57:46 UTC** · PI **none** · archive `20260909-seven-seams-sol-medium-high-control-v1`.

All four projects passed: 2/2 at Medium and 2/2 at High, reported separately. No matched PI arm exists here. Higher effort is one possible explanation for recovering the low-effort failures; the next completed fixture increased shared-function editing pressure, not evidence that PI was necessary. The original batch marker mistakenly said low/three trials; per-trial plans, command lines and all eight native contexts confirm Medium/High and four trials.

| Run (latest launch first) | Model / effort | Both sides | Producer / consumer | Failed seams | Worker window | Worker-s |
| --- | --- | ---: | --- | --- | ---: | ---: |
| medium2 | sol / medium | 7/7 | 7/7 · 7/7 | none | 118.904s | 217.341 |
| medium1 | sol / medium | 7/7 | 7/7 · 7/7 | none | 152.644s | 268.347 |
| high1 | sol / high | 7/7 | 7/7 · 7/7 | none | 141.681s | 262.022 |
| high2 | sol / high | 7/7 | 7/7 · 7/7 | none | 153.733s | 290.432 |

## Sol · Low · ordinary

Started **2026-09-09 03:53:03 UTC** · PI **none** · archive `20260909-seven-seams-sol-low-control-v1`.

Scores were 3/7, 4/7 and 3/7 in trial-number order. Discounts, contacts and orders failed in every run; delivery formatting failed in trials 1 and 3. This is the stronger ordinary configuration in the A/B/C comparison above. The next completed Sol tests raised reasoning effort without PI to see whether additional reasoning would preserve the remaining contracts.

| Run (latest launch first) | Model / effort | Both sides | Producer / consumer | Failed seams | Worker window | Worker-s |
| --- | --- | ---: | --- | --- | ---: | ---: |
| control2 | sol / low | 4/7 | 7/7 · 4/7 | discounts, contacts, orders | 69.539s | 117.527 |
| control3 | sol / low | 3/7 | 7/7 · 3/7 | discounts, delivery, contacts, orders | 89.395s | 143.909 |
| control1 | sol / low | 3/7 | 7/7 · 3/7 | discounts, delivery, contacts, orders | 103.369s | 154.665 |

## Luna · Low · ordinary

Started **2026-09-09 03:38:51 UTC** · PI **none** · archive `20260909-seven-seams-luna-low-control-v1`.

The paired historical PI scores were 7/7 and 7/7. Ordinary trial 1 retained a deleted NAMES import, preventing presentation from loading; trial 2 preserved stock/delivery but left five incompatible contracts. A later equal-information study tested whether shared-state coordination adds value once ordinary workers also have both tasks.

| Run (latest launch first) | Model / effort | Both sides | Producer / consumer | Failed seams | Worker window | Worker-s |
| --- | --- | ---: | --- | --- | ---: | ---: |
| control2 | luna / low | 2/7 | 7/7 · 2/7 | prices, weights, discounts, contacts, orders | 55.085s | 93.386 |
| control1 | luna / low | 0/7 | 7/7 · 0/7 | prices, stock, weights, discounts, delivery, contacts, orders | 46.426s | 79.612 |

## Luna · Low · PI

Started **2026-09-09 03:32:47 UTC** · PI **v0.05** · archive `20260909-seven-seams-luna-low-v1`.

Both projects reached 7/7. The subsequent same-model ordinary batch reached 0/7 and 2/7. This is the recovered low-effort breakthrough, but PI included peer task visibility and additional workflow context; the comparison does not isolate live shared state from context.

| Run (latest launch first) | Model / effort | Both sides | Producer / consumer | Failed seams | Worker window | Worker-s |
| --- | --- | ---: | --- | --- | ---: | ---: |
| luna1 | luna / low | 7/7 | 7/7 · 7/7 | none | 119.958s | 193.564 |
| luna2 | luna / low | 7/7 | 7/7 · 7/7 | none | 87.870s | 169.344 |

## Spark · XHigh

Started **2026-09-09 03:17:00 UTC** · PI **v0.05** · archive `20260909-seven-seams-spark-xhigh-v1`.

PI-only, no matched ordinary arm: 3/7, 3/7 and 0/7 in trial-number order. More reasoning did not achieve acceptance. Failures included cents/grams/basis-point conversion and obsolete NAMES imports; the next low-effort Luna tests explored a different capability point, not a stronger causal PI claim.

| Run (latest launch first) | Model / effort | Both sides | Producer / consumer | Failed seams | Worker window | Worker-s |
| --- | --- | ---: | --- | --- | ---: | ---: |
| spark1 | spark / xhigh | 3/7 | 7/7 · 3/7 | prices, weights, discounts, contacts | 48.962s | 67.725 |
| spark2 | spark / xhigh | 3/7 | 7/7 · 3/7 | prices, weights, discounts, contacts | 53.592s | 67.173 |
| spark3 | spark / xhigh | 0/7 | 7/7 · 0/7 | prices, stock, weights, discounts, delivery, contacts, orders | 28.028s | 47.276 |

## Luna and Spark · Medium · refreshed integration context

Started **2026-09-09 03:11:06 UTC** · PI **v0.05** · archive `20260909-seven-seams-luna-spark-v2`.

Backend change: related-task context and retained peer summaries became available even before peer enrollment or after release, with explicit refresh guidance. Luna again passed all three; Spark still passed none. The next Spark XHigh test asked whether more reasoning would resolve the stale-contract failures without another PI change.

| Run (latest launch first) | Model / effort | Both sides | Producer / consumer | Failed seams | Worker window | Worker-s |
| --- | --- | ---: | --- | --- | ---: | ---: |
| luna1 | luna / medium | 7/7 | 7/7 · 7/7 | none | 137.160s | 225.676 |
| luna3 | luna / medium | 7/7 | 7/7 · 7/7 | none | 101.249s | 184.451 |
| luna2 | luna / medium | 7/7 | 7/7 · 7/7 | none | 161.118s | 304.456 |
| spark3 | spark / medium | 0/7 | 7/7 · 0/7 | prices, stock, weights, discounts, delivery, contacts, orders | 26.736s | 49.269 |
| spark2 | spark / medium | 3/7 | 7/7 · 3/7 | prices, weights, discounts, contacts | 41.758s | 65.541 |
| spark1 | spark / medium | 0/7 | 7/7 · 0/7 | prices, stock, weights, discounts, delivery, contacts, orders | 29.552s | 55.497 |

## Luna and Spark · Medium · first seven-seam batch

Started **2026-09-09 02:52:51 UTC** · PI **v0.04** · archive `20260909-seven-seams-luna-spark-v1`.

PI-only: Luna passed all three; Spark passed none. Spark left obsolete imports/units, so this is a model-stratum comparison, not evidence that PI beats ordinary workers. The next batch changed backend integration context and worker guidance while freezing the fixture, prompts and checker.

| Run (latest launch first) | Model / effort | Both sides | Producer / consumer | Failed seams | Worker window | Worker-s |
| --- | --- | ---: | --- | --- | ---: | ---: |
| luna1 | luna / medium | 7/7 | 7/7 · 7/7 | none | 113.766s | 203.905 |
| luna3 | luna / medium | 7/7 | 7/7 · 7/7 | none | 94.145s | 160.285 |
| spark2 | spark / medium | 0/7 | 7/7 · 0/7 | prices, stock, weights, discounts, delivery, contacts, orders | 46.659s | 88.506 |
| luna2 | luna / medium | 7/7 | 7/7 · 7/7 | none | 96.152s | 183.217 |
| spark3 | spark / medium | 3/7 | 7/7 · 3/7 | prices, weights, discounts, contacts | 42.879s | 55.577 |
| spark1 | spark / medium | 0/7 | 7/7 · 0/7 | prices, stock, weights, discounts, delivery, contacts, orders | 28.113s | 54.321 |

## What NAMES means

`NAMES` and `CONTACTS` are fixture symbols in `customers.py`, not skill features. The producer migrates separate name/email data into structured contact records. A consumer that still imports the removed `NAMES` symbol can stop the entire presentation module from importing, which cascades across all seven label checks. Later `integration_context` exposed the related task and retained summaries; that was a real PI behavior change, not a test fix that restored the obsolete fixture symbol.

## Interpretation boundary

The A/B/C gap is substantial in these seven observations, not a measured population success rate. It demonstrates the observed value of the Luna-plus-PI configuration relative to both ordinary alternatives. The subsequent equal-information concurrency studies ask which part of PI supplies that value—context, concurrent coordination or both—rather than repeating this capability comparison.
