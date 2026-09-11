# Qwen thinking off · ordinary follow-up

[All results](../../RESULTS.md) · [Measurements](qwen-ordinary-thinking-off-measurements.json) · [Preceding PI run](qwen-thinking-off.md)

**0/7 integrated in 44 seconds.** Both ordinary workers finished successfully as
processes, but their combined project failed. No timeouts or human intervention.

## Thinking-off comparison · one project per condition

| Condition | Accepted | Score | Project elapsed | Aggregate worker time | Input + output tokens |
| --- | --- | --- | --- | --- | ---: |
| Ordinary, latest B1 | No | **0/7** | 44.072s | 79.241s | 241,948 |
| PI, preceding C1 | Yes | **7/7** | 146.669s | 278.968s | 1,983,581 |

Both used thinking **off**, confidence phrase **off**, Qwen Code **0.23.2**,
`qwen38-27b-dflash2`, 230k context and the original **non-torture** seven-seam
fixture. Fixture/runtime manifests, role-prompt input hashes and settings hash
matched exactly. PI availability/instructions/context differed as the treatment;
this is not an equal-static-context ablation. These projects ran sequentially,
PI first, with two concurrent workers inside each fresh project.

The failed ordinary project is not a cheaper or faster *accepted result*. This
one-per-condition observation supports further investigation, not a reliability
estimate or a claim that PI alone caused the difference.

## Why ordinary failed

The consumer implemented and checked labels using the old data, then exited at
**35.719s**. The producer began applying its migration at approximately **35.759s**,
after that exit. It preserved its helper contracts and passed existing tests, but
removed `NAMES` and `REFUNDED`, which the consumer still imported.

The producer had read `presentation.py` earlier, but did not reread or test it
after migration. Both final messages claimed their own work was complete; neither
reported the integrated break. There was no observed repair attempt.

Final producer checks: **7/7**. Final consumer checks: **0/7**, all blocked by
`ImportError: cannot import name 'NAMES' from 'customers'`. These seven failures
share one module-loading gate; they are not seven independently diagnosed defects.

```text
Elapsed       0s                    36s       44s
Consumer      ├─────────────────────┤ old-data labels checked; exits
Producer      ├───────────────────── migration ─┤
Final checker                                  0/7
```

Maximum simultaneous workers: two; active-time concurrency factor **1.821**.
Distinct source contributions remained, but they were incompatible. Native
overlap alone did not produce useful integrated concurrency.

## Compute and integrity

| Worker | Duration | Input | Cached input¹ | Output | Reasoning | Requests |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Producer | 43.522s | 133,187 | 122,688 | 2,737 | 0 | 5 |
| Consumer | 35.719s | 104,151 | 77,568 reported | 1,873 | 0 | 4 |
| Total | 79.241s | 237,338 | 200,256 reported | 4,610 | 0 | 9 |

¹ Cached input is included in input. One consumer response omitted cached usage,
so its cache subtotal and the aggregate are incomplete, not zero-filled estimates.
All nine requests reported input/output and zero reasoning tokens. Every request
had `enable_thinking: false`; no reasoning stream was observed. Native generic
effort was `none`, explicit provider field Medium; no High/XHigh requested.

No PI files or instructions were mounted to the ordinary workers. No follow-up
messages, hidden repairs, retries or replacement trial. Qwen ran on freshly
resolved DGX1+DGX2; production PI and model placement stayed unchanged. The
experimenter's PI bookkeeping was outside the isolated worker environment.

**Observed problem:** the ordinary workers stopped after locally reasonable work
without checking compatibility after the peer migration. **Proposed next test:**
repeat the unchanged thinking-off comparison to see whether this difference
persists or depends on completion order. No additional run is queued.

## Evidence

- Batch: `20260909-qwen-ordinary-thinking-off-v1`, project `B1/seam-project-v4i390cq`.
- Executed: **2026-09-09 21:36:25–21:37:09 UTC**.
- Frozen batch SHA-256: `cb23887419b1b9f2b3c620e2f2d9e4be6c6feaea1f0fa2e893e20fc6f5572349`.
- Plan SHA-256: `0355c370cb420ae094b7ae38c7be49feebbad555e14801e3abe3c2b74755ddf9`.
- Profile route: `pi-for-qwen/v1`, unchanged; PI behavior **none** in B1,
  **v0.05 unchanged** in the preceding C1.
- **20 focused harness tests passed**, followed by fresh native isolation and CLI
  preflight before launch. Final acceptance was evaluated after worker exit.

Public measurements retain exact identities, usage completeness, timings, checks
and result hashes. Historical PI evidence remains unchanged.
