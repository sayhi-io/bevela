# Qwen steering follow-up — ON HOLD

Recorded 2026-09-10 at the user's request. Do not implement or launch the trial
until the user resumes this work. Current priority: inspect existing SparkOps
Actions and standalone MCP/development bridge progress.

## Held task list

- [ ] Preserve essential existing PI context in Qwen steering: actual checkout
  identity, relevant path/seam declarations, current repair agreements, freshness
  and explicit coverage/omissions. Shorten presentation, not PI capabilities.
- [ ] Make competing-repair notices actionable: encourage an agreed, bounded
  repairer and retention of diagnosis, attempted fix and validation outcome using
  existing PI mechanisms. Shared seams alone must not force serialization or
  grant ownership. Other workers remain free to progress on unrelated work.
- [ ] Replace the lifetime 12-notice cutoff with deduplicated, rate-limited
  delivery that retains pending meaningful changes. Preserve bounded overhead,
  explicit freshness and honest source attribution; a changed path is not proof
  of a collision, author identity or semantic impact.
- [ ] After implementation and focused validation, freeze a new Qwen-only version
  and run one PI trial on the same independent-request candidate2 fixture.
  Keep model/settings, task inputs, checker, deadline and three-worker arrangement
  unchanged. Measure shared diagnoses, repair agreements, repeated/reversed fixes,
  retained progress and notice overhead as well as final 15-group acceptance.

## Guardrails

- Preserve traditional/non-Qwen PI behavior, including backend presence for other
  callers; do not expose the presence command to Qwen as a replacement for enrollment.
- Do not modify frozen historical inputs or evidence, production runtime, models,
  placement, scheduling, execution authority or worktree ownership.
- PI records observed checkout/branch/HEAD and declared related work; it does not
  provision or allocate worktrees. The current experimental Qwen source watcher
  observes one checkout, not arbitrary peer worktrees.
- Keep future ChatGPT orchestration, SparkOps execution/admission, and independent
  PI context/coordination responsibilities separate. The development integration
  remains outside Bevela in the standalone bridge repository.

## Evidence motivating the follow-up

Study: `qwen-independent-requests/candidate2-v1`, 2026-09-10.
Ordinary A1/A2/A3: 15/15 each. PI+steering B1/B2: 13/15 at the 30-minute
worker boundary; B3: 15/15. Do not infer that PI caused the failures.

- B1: an alternative draft included current-return quantities but its whole-file
  write was rejected by the native harness. A later partial repair of the landed
  implementation removed an undefined variable without including current-return
  quantities. That bug survived. Subsequent debugging repeatedly exercised a
  passing 101-cent example while the remaining receipt-status failure was at zero.
- B2: workers added/removed the same cancellation-implies-refund workaround five
  times, alternating two incompatible checker outcomes. Some reversals were by
  the same worker. The underlying pending-payment overwrite was identified near
  timeout, with no repair applied before exit.
- Workers noticed peers but did not establish a PI repair agreement. All exhausted
  their steering notice allowance early, including successful B3. Notice exhaustion
  alone is therefore not a sufficient explanation, nor is more notification a
  proven remedy for the underlying coding/debugging errors.

This file records deferred work, not a newly executed experiment or a provider
lifecycle change. Commit/publication requires separate authorization.
