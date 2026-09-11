# Qwen PI steering · first pilot

[All results](../../RESULTS.md) · [Measurements and notices](qwen-steering-measurements.json) · [Toggle and limits](../CLI_QWEN_STEERING.md)

**7/7 accepted in 94.860s. Both workers enrolled, retained distinct work and
released their registrations.** No timeout, native loop guard or human feedback.
Thinking was disabled in all 25 provider requests, with zero reported reasoning
tokens. This is one successful pilot, not established reliability.

| Run | Executed UTC | Integrated | Producer | Consumer | Project time | Aggregate worker time |
| --- | --- | --- | --- | --- | ---: | ---: |
| C1 | Sep 9, 22:55:25–22:57:00 | **7/7 accepted** | 7/7 | 7/7 | **94.860s** | 187.587s |

## Treatment

Original non-torture seven seams, unchanged role prompts and checker. Two native
Qwen Code 0.23.2 workers, `qwen38-27b-dflash2` on DGX1+DGX2, 230k context,
thinking off, confidence off. Same 260-word compact startup and filtered CLI.
Backend **v0.05 unchanged**; new worker integration **`qwen-steering/v1`**, on.

Native hooks deliver bounded PI declarations and observed source-file changes
without requiring a worker to compose a change report. Notices carry no source
patch, checker result, reference answer, inferred authorship or repair assignment.
The first version observes all allowlisted source files, not inferred semantic
impact; it also notices the receiving worker's own changes. Nothing waits for
peers or resumes exited workers. Fresh sessions and source, one frozen project,
no additional ordinary or steering-off run.

## Observed sequence

Times are seconds after first worker launch:

| Time | Observation |
| ---: | --- |
| ~0 | Native prompt hooks emit initial related PI context to both workers. |
| 16.4 | Producer requests enrollment before editing. |
| 33.8 | Consumer requests enrollment and inspects Git state. |
| 43.1 | Consumer writes its first presentation implementation. |
| 43.7 | Producer writes the migrated data modules. |
| 47.4 | Consumer hook emits changed-source notice including catalog, contacts, delivery, inventory, orders, promotions and shipping. |
| 54.1 | Producer corrects its initially missed checkout cents conversion after a test failure. |
| 58.6 | Consumer explicitly recognizes the migrated representations on disk. |
| 63.2 | Consumer replaces its presentation implementation for those representations. |
| 72.5 | Consumer runs existing tests and all 15 label assertions successfully. |
| 93.0 / 94.5 | Producer / consumer exit normally. |
| 94.9 | Independent post-exit checker accepts 7/7. |

The source-change notice precedes the consumer's explicit recognition and rewrite.
It also read changed source through normal tools. This supports successful
delivery and subsequent reconciliation, not proof that the notice uniquely caused
the fix. Both workers already had access to the underlying task/source information.

There was **one stale-consumer rewrite** and a producer-local checkout correction.
No competing cross-worker repair or repair claim/ack was observed. Producer edited
the migration/helper files; consumer edited presentation. The producer's release
summary described its peer as unaffected, which is not a complete causal account
of the earlier compatibility change. Automatic observation did not make every
manual summary accurate.

## Cost and comparison

| Configuration | Outcome | Project time | Input + output tokens |
| --- | --- | ---: | ---: |
| Preceding filtered CLI, no steering | 0/7; one project | 76.207s | 507,564 |
| Steering on | **7/7; one project** | 94.860s | 1,006,100 |

The failed 76-second project is not a faster path to the same accepted result.
Neither does a single success establish a reliable improvement. Prior compact
v1 runs also included a 7/7 success without steering; preserve that stochastic
history rather than treating steering as necessary for correctness.

| Worker | Active time | Input | Cached input¹ | Output | Hook calls | Notices | Hook-body time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Producer | 93.048s | 512,288 | 481,536 | 4,137 | 41 | 11 | 7.956s |
| Consumer | 94.540s | 485,302 | 458,816 | 4,373 | 42 | 7 | 7.407s |
| Total | 187.587s | 997,590 | 940,352 | 8,510 | 83 | **18** | **15.363s** |

¹ Included in input. All request usage was reported. Native request input totals
include repeated cached context, not unique context or hook-only tokens.
Hook-body time includes locking, context reads and observation work but excludes
process startup; it overlaps across workers and is **not** 15.363 seconds of
additive project delay. No notices hit the per-session suppression budget.

Maximum workers: two; concurrency factor **1.984**. Both retained useful work
during overlap, but source reconciliation still required rework. Emitted notices
are recorded verbatim in the public ledger; emission alone is not proof of model
attention. A separate real-native/scripted-provider test verified hook context
reaches model requests without performing model inference.

## Next step and provenance

Repeat the frozen steering configuration before altering it or claiming a stable
benefit. No further project was queued. Remaining limitations include incomplete
manual reporting, whole-allowlist rather than semantic file routing, and inability
to notify a worker after exit.

Batch `20260909-qwen-steering-v1`, C1 `seam-project-cfpr38a8`; hashes, controls,
per-seam checks, native receipts and hook notices are in the ledger. Raw native
transcripts remain local. Frozen inputs were verified after execution.

Validation: nine focused steering tests and the explicit native transport test
passed. Full suite: **408 discovered, 407 passed, one optional native test skipped**;
that native test passed separately. No backend deployment, commit, push or merge.
