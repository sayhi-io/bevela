# Distributed candidate 2: fixed business semantics, worker-designed wire contracts

Status: candidate2 completed **3/3 ordinary projects accepted**, each 15/15.
Both allowed candidates saturated; calibration stopped before the single-worker
ceiling or matched PI evaluation. [Completed results](results/sol-distributed.md).
[Measured outcomes](results/sol-distributed.md). The method below describes the
prelaunch design checkpoint; the original copy and input hashes remain retained.
Candidate1's three ordinary concurrent Sol Medium projects all reached accepted
source with 12/12 integration groups. No Sol single-worker ceiling or PI-enabled
software project has run in this study at this checkpoint. Phase1's 8/9 protocol
qualification is a separate result, not a software comparison.

[Software protocol and execution gates](CLI_SOL_DISTRIBUTED_SOFTWARE.md) ·
[Parent study](CLI_SOL_DISTRIBUTED.md) ·
[Phase1 results](results/sol-protocol.md)

## Why a second candidate

Candidate1 supplies a detailed internal wire contract. Its components can largely
be implemented independently against that common specification. Three accepted
ordinary projects leave no observed correctness headroom in that calibration.
They do not establish that ordinary workers always succeed or that PI cannot help.

Candidate2 retains candidate1's external compatibility requirements and twelve
integration groups, and adds one coupled lifecycle: partial returns with cumulative,
durable business state. The new internal event representations are designed by
their producers during implementation. Consumers must interoperate with those
actual producers, rather than receive predetermined new payload-field answers.

This is an explicit change in the experimental task: from implementing a supplied
integration design to implementing compatible internal designs across owned
components. Preserve both candidates and report them separately. Do not pool their
scores or call a difference between candidates a PI treatment effect.

## What must be fixed before launch

The fixture objective must fully specify the public business behavior, external
entry points and arguments, compatibility obligations, and observable results.
Representation freedom must not leave business policy for consumers to guess.
Before freezing the candidate, the objective and checker must agree on:

- Valid partial returns, cumulative returned quantities and amounts, limits, and
  the treatment of repeated or conflicting requests.
- Which original price/quantity snapshots determine inventory restoration,
  refunds and receipts; later price changes cannot silently redefine history.
- Persistence and restart behavior, including retry identity and retained
  cumulative state.
- The required behavior under delayed, duplicate and reordered event delivery,
  including intermediate states and final convergence.
- The interaction with existing cancellation, capture/refund and legacy behavior,
  including any explicitly excluded combinations.

These are prelaunch specification obligations, not additional hidden checker
requirements or a substitute for the concrete fixture objective. Any unresolved
policy must be resolved publicly before model execution. The scope is partial
returns; this note does not add a separate fulfillment or amendment subsystem.

## What workers may design

Keep the same four owned roots: Catalog, Orders, Settlement and Reporting. Preserve
the fixed external interfaces and existing compatibility contract. For the new
internal extension, producers may choose payload layouts and representations within
the publicly stated transport constraints. Consumers may inspect current peer code
and any wire documentation authored in the producer's own root. Such documentation
describes an implementation; it cannot revise the frozen business requirements.

Both ordinary and PI workers receive identical role prompts, complete business
facts, initial source, public architecture and acceptance checker. Both can inspect
the same shared checkout and worker-authored wire documents. The PI inventory may
restate those same task facts; it must not supply extra payload answers, reference
implementation details or evaluator guidance. The reference implementation stays
outside worker mounts. This methodology document is not a treatment-only source
of task requirements.

No task prescribes a coordination command, waiting period, message exchange or
barrier. No external actor changes source or broadcasts interface revisions after
launch. The evolving boundary comes from ordinary worker implementation choices,
not secret facts, a timed evaluator intervention or a forced coordination ritual.

## Black-box acceptance and prelaunch review

The checker must feed actual producer-emitted extension events into actual
consumer handlers. It must not construct a reference-specific new payload or
require the reference's internal storage layout. Any transport fields needed to
route, identify or acknowledge events must be stated in the public objective.
Existing versioned compatibility events remain governed by their existing contract.

Expected business outcomes must be computed independently of the emitted payload's
claims. Compare inventory, cumulative returns/refunds, balances and receipts against
the frozen business oracle. A producer and consumer sharing the same mistake, or
emitting no necessary events, must not pass merely because they agree with each
other. Tests should include changed data, repeated operations, restart, deterministic
delivery permutations and observable intermediate checkpoints. Do not use sleeps
or wall-clock races to manufacture integration pressure.

Before models, independently review the objective, role prompts, public checker,
reference and mutation tests. Demonstrate that:

- The reference satisfies the complete compatibility and extension acceptance.
- Deliberate cumulative-state, redelivery, persistence and cross-component defects
  are rejected, including locally plausible but jointly incorrect behavior.
- The extension checker does not depend on reference-specific payload field names;
  a coherent alternative internal representation can satisfy the same oracle.
- Ordinary workers have every business fact needed to implement and test the task;
  PI supplies its unchanged workflow/context mechanism, not additional answers.

Reference success establishes achievability, not model competence. Mutation checks
establish selected checker sensitivity, not complete correctness coverage. Test
delivery permutations are product acceptance exercises, not live calibration peers.
JSON round-tripping establishes serialization, not the absence of peer imports or
direct peer-state reads. Independent import smoke checks can expose eager coupling;
lazy imports and direct state access remain source/log review constraints, not
claims proven by a passing functional checker or source-pattern score.

## Gates and budgets remain unchanged

Candidate2 is the second and final allowed ordinary calibration candidate. Freeze
its exact fixture, public checker and task inputs before three fresh B projects.
Retain every outcome, infrastructure rejection and review; do not retry failed
model projects, silently retune the candidate or allocate a third candidate.

The existing registry requires an unsaturated ordinary candidate: one or two
accepted projects out of three. If candidate2 is also saturated, or none is
accepted, the bounded calibration has not established the required region; stop
before the software treatment evaluation rather than lower the model or change
the acceptance standard. A selected candidate receives the existing two fresh
single-worker ceiling checks. Evaluation requires at least one accepted ceiling
source; native completion remains separately recorded.

Only after those gates, use the frozen three A, five B and five C evaluation
projects in the existing order. Keep Sol Medium, four concurrent component workers
in B/C, the solo ownership of all four roots in A, the 900-second per-worker limit,
one project at a time, fresh profiles and the source-bound post-exit reviews. PI
behavior v0.05, its frozen source bundle, and the software recorder remain unchanged.
No orchestrator, post-launch feedback, integration successor or automatic repair
controller is introduced. The deterministic peer from Phase1 is not part of this
software study.

## Interpretation limits

This candidate is intended to increase the need to reconcile actual peer interfaces,
not merely add small independent checks or adversarial type puzzles. It also adds
coding work. Failures therefore require evidence-based attribution; they are not
automatically coordination failures. The single-worker ceiling is a diagnostic
against confusing general task difficulty with distributed implementation difficulty.

A later PI advantage would support integration under implementation-defined
internal contracts. It would not alone establish spontaneous protocol use, useful
parallelism, faster delivery or lower cost. Report accepted source, native workflow
completion, sampled first/durable acceptance, elapsed time, worker effort and
concrete retained contributions separately. There are no candidate2 outcomes or
single-worker/PI software efficacy results to report at this checkpoint.
