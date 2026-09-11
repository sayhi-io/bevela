# Qwen Code Medium · original seven seams · v1

User-authorized September 9, 2026: three ordinary and three PI projects on the
original, **non-torture** producer/consumer fixture. This is a new study, not a
replacement or retry of the ten distributed candidate-2 projects.

**Completed:** [six-project results](results/qwen-seven-seams.md). Ordinary 3/3
accepted; PI 2/3 accepted; all twelve workers finished without timing out.

## Frozen comparison

- Native Qwen Code **0.23.2**, local served model `qwen38-27b-dflash2`.
- Literal server `reasoning_effort: medium`, thinking enabled, **230,000** context,
  native automatic compaction at 85%, output limit 32,768; temperature 0.6 and
  top-p 0.95. No cloud fallback or substitution of xhigh.
- **Two concurrent workers** per fresh shared checkout: producer and consumer.
  Each gets its existing role prompt unchanged. Projects run sequentially in
  order **B1, C1, C2, B2, B3, C3** (B ordinary; C PI).
- Worker deadline remains **1,800 seconds**, the prior Qwen budget, not a runtime
  target. Preserve unfinished source and all timeouts; never replace a failed run.
- Original fixture in `experiments/seven_seams/fixture`, original role prompts,
  and `seven_seams_check.py` are unchanged. No refund-torture or 15-group tasks.
- Original information treatment: ordinary workers receive their own task and
  inspect shared source normally. No shared document hands them the peer's future
  task. PI's inventory exposes the two actual tasks through its ordinary workflow.
  This therefore tests the combined context/coordination treatment, not an
  equal-static-context ablation.
- PI code and skill are frozen. Only the native identity instruction changes from
  Codex's thread variable to Qwen Code's session variable. The CLI uses the sandbox's
  Python interpreter. Neither preparation nor the observer enrolls model workers.
- PI source access is limited to runtime, skills and operational documentation;
  prior results, transcripts, evaluator tests and reference solutions are not
  mounted. Ordinary workers have no PI bundle or operator credentials. Both arms
  retain native shell, Git, source inspection and test capabilities.

## Recording and acceptance

The existing Qwen recorder owns no model loop: Qwen Code chooses tools, reasoning,
implementation and compaction. A passive HTTP relay records actual request controls
and usage. Fresh UUIDs/homes and disposable filesystem namespaces isolate trials.
Network remains available for inference and ordinary tools; this is not hostile
network isolation or a claim of exclusive GPU allocation.

Freeze all six input plans and source/runtime/settings hashes before launch. Run
focused harness tests, unchanged-fixture checker tests and no-model isolation/CLI
checks before the batch. Exclusive launch markers prevent replay. Stop sequencing
on infrastructure/recording failures; ordinary task failures and predetermined
deadlines remain results, not reasons to silently retry.

The frozen checker executes only after both workers exit, on a private copy of
their combined output. Each seam counts only when both producer and consumer
checks pass, including current-data behavior. Score **0/7–7/7** separately from
native process success, timeout and recording completeness. A model saying done
does not establish accepted integration. No evaluator repair or follow-up prompt.

Report all six scores, exact failed seams, worker exits and elapsed durations,
project wall time, aggregate observed tokens and usage completeness. Cached input
and reasoning are subsets, not additional tokens. Lower bounds remain labeled;
failed attempts are not time-to-success measurements. Inspect PI use and retained
source for concrete coordination/duplication evidence without inventing a score.

## Relationship to the earlier Qwen cohort

The distributed candidate-2 cohort had 0/5 accepted in each arm and 35/40 worker
timeouts. This version changes fixture complexity, worker count and effort together
at the user's request. It cannot by itself determine which of those changes causes
any improvement. Within this new cohort, B/C share model, effort, fixture and
deadline. No production PI or model-serving change belongs to this study.

## Preparation evidence

The first preparation was never executed: independent review required an isolated
native version check and refusal to advance after non-timeout EOF without a
correlated final native receipt. Both were corrected before model execution.
The original preparation and its `NOT_EXECUTED.json` remain outside Git.

Corrected batch: `20260909-qwen-seven-medium-v1-preflight2` in the private evaluation
directory. All twelve native homes are fresh; separate preflight profiles verified
the frozen CLI reports 0.23.2. Twelve new focused tests and **377 total Python tests**
passed. Fixture/checker bytes remain unchanged. Frozen manifest SHA-256:
`fe378b77345b414204d50601d3d3ce400f0fe5c79d4fdefe97bc9d3ecbe11b45`.

The recorder source SHA-256 is
`adee913e5cc070a1ba2b09a02d5fe7f6bc026c5ac84bb60a062d68bd4ce54628`.
The inherited Qwen settings retain a generic UI effort default, but explicit
provider `extra_body.reasoning_effort: medium` overrides it. Every actual request
is checked for literal Medium, thinking enabled, model identity and output limit;
the UI label alone is not evidence of the executed effort.
