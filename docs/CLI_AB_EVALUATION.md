# Evaluation methodology

[Results](../RESULTS.md) · [Original seven seams](CLI_SEVEN_SEAMS.md) · [Concurrency versus context](CLI_CONCURRENCY_STUDY.md) · [Self-organization](CLI_SEVEN_SEAMS_SELF_ORGANIZING.md)

## Native workers, measured projects

Codex is the worker harness. Experiment machinery prepares disposable source,
launches fresh sessions, records their execution and checks the combined result.
It must not supply an ordinary worker with a coordination plan, staged reminders,
peer handoff summaries or evaluator-directed correction rounds.

Normal shell, Git, repository inspection, documentation and tests remain available.
A complete product requirement is not a solution hint. Workers may coordinate or
repair on their own; the observer must not do that work for them after launch.

Freeze the source, prompts, checker, model/effort, PI implementation and trial
boundary before execution. Preserve failed, incomplete and timed-out trials without
silent retries. Run projects one at a time, with the workers inside a multi-worker
project launched concurrently. Historical deviations remain disclosed in reports;
this policy does not retroactively change their execution.

## Different studies answer different questions

- **Original seven seams:** concurrent producer/consumer tasks test compatibility
  across seven dependent boundaries. Historical PI workers had access to peer-task
  context beyond the ordinary worker's own role prompt. Treat this as an observation
  of that whole treatment, not an isolated live-coordination effect.
- **Concurrency versus context:** the same complete task information is available
  in every arm; single-worker baselines distinguish one coherent session from a
  predefined producer/consumer pair. No after-launch coordination is injected.
- **Self-organization:** every worker receives the same complete objective and
  normal development capabilities. No ownership, file allocation, integrator or
  repairer is assigned by the experiment. Whether a useful division emerges is
  the outcome, not a prerequisite manufactured by the runner.
- **Refund torture:** a different, harder fixture. Its seven-point results are not
  interchangeable with the original seven seams.

Equal task information in the later studies was deliberate context ablation, not
a reason to exclude an unfavorable outcome. Detailed protocols and frozen inputs
define each study; do not combine them into one success rate.

## Report outcomes separately

Record integrated correctness, project elapsed time, aggregate worker time/tokens,
retained concurrent contributions, concrete duplication/rework, human intervention
and PI overhead. More tokens or a longer individual session do not alone imply a
slower project. A quick failed project is not equivalent to an accepted project.

Use the frozen acceptance contract, not a new requirement invented during review.
Inspect source and logs for material differences and observable mechanisms; do not
assign a subjective coordination score. Label suspected causes as hypotheses and
state the next question for ties or cases where PI did not help. A proposed next
test is not a completed result.

## Withdrawn coached controls

Withdrawn on September 9, 2026, at the user's request:

- **Status Pilot01:** the setup supplied named peers, an ordinary notes channel,
  detailed handoffs and a bounded integration successor. It tested PI on top of
  coordinator-arranged handoff machinery, not ordinary native coordination.
- **Status Study02:** prompts prescribed ownership, named notes files and detailed
  handoffs; the runner provided a fresh integrator and owner-correction rounds.
- **Release Study03 v1/v2:** the runner explicitly announced revision transitions,
  told workers to reread peer handoffs, replaced an owner at a checkpoint and
  orchestrated integration/corrections. Its ordinary arm received coordination
  that the intended comparison was supposed to leave to the workers. V1 also had
  an invalidated evaluator; that is a separate defect.
- The unexecuted **Study03 continuity draft** and its acceptance prototype are
  retired with the same scripted study family, not counted as completed trials.

Their case-specific protocols, fixtures, launchers, acceptance scripts and release
harness tests have been removed from the current tree, and their outcome rows have
been removed from the results catalog. Generic isolation/recording utilities and
their safety tests remain; those utilities do not prescribe a task workflow.

This is a design-based exclusion, not filtering by winner. Native microstudies,
seven-seam studies, refund trials and both later concurrency studies remain,
including PI failures, ties and overhead. All 57 curated recent project measurements
are unchanged.

Original private frozen inputs and outputs were not edited or deleted. The removed
public source and summaries remain recoverable in
[the pre-withdrawal Git tree](https://github.com/meanaverage/sayhi-project-intent/tree/56bf4efc4c32e61911c40b92b80244bfcf90da84).
They are withdrawn comparisons, not efficacy evidence for or against PI.
