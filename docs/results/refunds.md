# Refund migration — overlapping edits

[All results](../../RESULTS.md) · [Fixture and checker](../CLI_TORTURE_REFUNDS.md) · [Measurements](measurements.json)

This is the **separate harder refund fixture**, not the original seven-label migration. Two workers can edit the same purchase/refund and persistence functions. Seven correlated acceptance groups cover units, both features, rounding, inventory, retry safety, persistence and receipts. A shared API failure can fail all seven; the score does not establish seven independent bugs or prove edit-race causation.

## Luna Medium comparison

| Treatment | Runs | Scores (trial-number order) | Accepted | Median worker window |
| --- | ---: | --- | ---: | ---: |
| PI v0.05 | 3 | 0/7, 7/7, 7/7 | 2/3 | 209.2s |
| Ordinary | 3 | 0/7, 6/7, 6/7 | 0/3 | 156.9s |

PI had an observed acceptance advantage, but did not eliminate failure. Both arms’ trial 1 lacked the required `refund(quantity=...)` interface. Ordinary trials 2/3 retained schema version 1 rather than the required version 2; the checker reports that under `both_features`, not `persistence`. Shorter failed runs are not cheaper accepted projects.

These were separately launched batches, with three projects running concurrently within each batch. Model/effort, core source, task prompts and checker were frozen; PI added its normal instructions and both task records. The PI bundle included the broader documentation tree and native host configuration was inherited, so these results do not isolate dynamic coordination from peer-task context or establish hermetic evidence exclusion. Next, the completed [original-fixture concurrency study](concurrency.md) equalized task information and compared one worker to two, with projects run sequentially.

## Every run — newest first

Worker window ends at the last native process exit and excludes post-exit scoring. Token/PI-only compute attribution was not reconstructed for these historical batches. No failed run was dropped.

| UTC launch | Batch / trial | Model / effort | PI behavior | Score | Failed groups | Worker window | Worker-s |
| --- | --- | --- | --- | ---: | --- | ---: | ---: |
| 04:33:29.698 | Medium PI / trial3 | Luna / medium | v0.05 | 7/7 | none | 218.536s | 394.110 |
| 04:33:29.685 | Medium PI / trial1 | Luna / medium | v0.05 | 0/7 | units, both_features, rounding, inventory, retry_safety, persistence, receipts | 186.458s | 299.282 |
| 04:33:29.669 | Medium PI / trial2 | Luna / medium | v0.05 | 7/7 | none | 209.184s | 344.055 |
| 04:24:46.584 | Medium ordinary / trial3 | Luna / medium | none | 6/7 | both_features | 148.590s | 236.048 |
| 04:24:46.575 | Medium ordinary / trial2 | Luna / medium | none | 6/7 | both_features | 156.934s | 234.863 |
| 04:24:46.563 | Medium ordinary / trial1 | Luna / medium | none | 0/7 | units, both_features, rounding, inventory, retry_safety, persistence, receipts | 163.494s | 255.287 |
| 04:16:03.917 | High ordinary / trial1 | Luna / high | none | 7/7 | none | 309.832s | 493.332 |

All launches above were **2026-09-09 UTC**. Source archive IDs and result hashes are in measurements.json. Backend v0.05 is the same core used in the later concurrency studies; switching fixtures did not change PI.

## Luna High baseline

The earlier single no-PI project passed 7/7 in 309.832s of worker execution. There is no Luna-High PI arm, so this is neither a PI win nor a measured PI loss. A plausible explanation is that more reasoning/integration work sufficed without PI; the next completed test lowered effort to Medium to observe a less saturated baseline.
