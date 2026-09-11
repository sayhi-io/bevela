# Distributed coherence · software protocol v1

Status: both allowed ordinary calibration candidates completed **3/3 accepted**.
The bounded calibration stopped as saturated; no single-worker ceiling or PI
software evaluation ran.
[Measured software results](results/sol-distributed.md).
The original prelaunch version of this protocol remains in the frozen batch.
[Parent protocol](CLI_SOL_DISTRIBUTED.md) · [Protocol calibration](results/sol-protocol.md)

The prerequisite completed with 8/9 reviewed workflows within the frozen 300-second
window (audit 3/3, repair-owner 3/3, repair-peer 2/3). One timeout and several
transcription errors remain recorded. This establishes bounded demonstrated use,
not perfect PI operation or spontaneous adherence during substantial coding.

## Fixed study inputs

- Native `gpt-5.6-sol`, medium reasoning, Codex 0.153.4; verify recorded turn identity.
- PI main `689a91979e313ac295e2e9277d82b4c9d0dff573`, behavior v0.05.
  No backend, workflow, or runtime changes during calibration/evaluation.
- Four owned component roots in one disposable Git repository. This preserves
  semantic cross-component ownership without introducing multi-repo transport or
  exceeding the current same-repository repair primitive.
- Ordinary and PI concurrent workers receive byte-identical role prompts, the
  same complete objective, public architecture map, initial source and acceptance.
  PI records contain those same task facts, not evaluator hints or hidden changes.
- PI workers additionally receive the existing frozen skill/workflow and a fresh
  local inventory/presence/report feed. They enroll themselves; the evaluator does
  not manufacture model registrations, claims, acknowledgments or summaries.
- Single worker receives the same complete objective and owns all four components.
  No fictitious producer/consumer dependency or obligation to wait for peers.

## Candidate 1: Depot

This starts as a working legacy dollar-based commerce product, not empty stubs.
Each component owns a separate JSON store and source root. Runtime calls are
sequential; development is concurrent. No database server, broker or networking
failure is introduced to simulate repository boundaries.

| Owned component | Migration work | Cross-component dependency |
| --- | --- | --- |
| Catalog | Decimal-to-cents conversion, immutable reservation snapshots, inventory retry/release, old-store migration | Orders consumes its reservation contract |
| Orders | Recovery after a persisted reservation, canonical retries, cancellation, durable acknowledged outbox | Catalog inventory and downstream order-event readers |
| Settlement | Deferred capture, cancel/refund reordering, deduplication, durable payment outbox | Orders' old/new events and reporting's payment reader |
| Reporting | Late order/payment joins, revision precedence, retained historical receipts, integer revenue | Both event streams plus legacy receipt clients |

All workers can read the complete [objective](../experiments/assets/distributed_v1/fixture/OBJECTIVE.md),
role tasks, architecture map and public checker. Required semantics include zero
amounts, historical price snapshots, mixed-version redelivery, restart and stale
event ordering. They are task requirements, not facts withheld from the control.
The specified post-reservation fault is a product recovery test, not an evaluator
message or a timed mutation during worker execution.

The checker has twelve named integration groups plus component-local results.
An observer-only reference demonstrates achievability; deliberate mutations test
whether the checker detects broken contracts, including local-pass/integration-fail
examples. Reference code is never mounted for workers. These twelve groups are
not the prior fixture's seven seams and their scores must not be pooled.
The checker measures functional integration, not filesystem atomicity or power-loss
durability; those limits are explicit in the public objective before execution.

## Candidate 2: implementation-defined return contracts

Candidate 1 completed three ordinary projects, all accepted. The second and final
candidate retains its migration and twelve integration groups, and adds durable
partial returns across the same four owned roots. Public external behavior fixes
inventory restoration, original-price credit allocation, retry/recovery,
cancellation interaction, deferred refunds and receipt results. Producers choose
and document the new internal JSON representations; consumers must integrate the
actual peer contract. No business rule or reference payload is PI-only.

The new black-box groups pass actual emitted data to actual consumers and compare
stock, credits, balances and receipts with independently computed expected outcomes.
Coherently wrong components must fail. Reference, alternative-representation and
mutation checks precede model execution. All requirements live in the protected
OBJECTIVE.md, copied in full to PI's assignment acceptance; role prompts are identical
between B/C. The recorder, PI, worker count and all execution/selection gates below
are unchanged. [Candidate 2 methodology](CLI_SOL_DISTRIBUTED_CANDIDATE2.md).
The following records the historical preparation checkpoint, before candidate 2
model execution. Prelaunch
validation passed **300 repository tests**, including 23 fixture tests (11 original,
12 candidate-2). The candidate-2 reference passed all fifteen integration groups
and eight original local tests. Coherent alternate layouts pass; a producer-only
layout change fails new integration while legacy/local checks remain passing.
Reference/checker defects found during preparation were corrected before this
validation. No model trial, PI behavior or original frozen evidence was changed.

## Calibration before treatment

At most two explicitly versioned fixture candidates, three ordinary concurrent
projects each. Aim for integration failures due to distributed assumptions with
an unsaturated ordinary baseline, not obscure coding or missing requirements.
Preserve every candidate and outcome. Do not adapt the fixture against PI results.

Once a candidate is selected, run two fresh single-worker ceiling projects. If
both fail, investigate capability/decomposition rather than attribute failure to
coordination. If both allowed candidates remain saturated, report that the bounded
calibration did not establish headroom; do not lower the model or silently add trials.

After selecting a defensible fixture and completing the ceiling diagnostic,
freeze three fresh A, five fresh B and five fresh C projects. Execution order:

```text
A1 B1 C1 C2 B2 A2 B3 C3 C4 B4 A3 B5 C5
```

Calibration and ceiling outcomes are not pooled into this evaluation sample.
No orchestrator is included. A later orchestrator study would use the same fixed
vs agent-decomposed × ordinary vs PI matrix, with role allocation separated from
PI's shared-state responsibility. That follow-up is prepared conceptually, not run.

## Execution and isolation

One project at a time; four component workers within B/C launch concurrently via
the existing native recorder. Each worker has a fresh native profile and session;
only its shared disposable checkout, own profile, system tools, and optional frozen
PI bundle are mounted. Neither reference implementation, raw historical evidence,
peer transcript nor the recorder/observer directory is available in that mount.
Normal shell, Git, inspection, tests and ordinary file-based coordination remain.
Network remains available for native authentication/inference; this is not a
hostile-code network-isolation claim. No infrastructure services or packages are
installed for the synthetic product.

Maximum 900 seconds per worker, starting at its actual native launch. Record launch
skew and per-worker bounds. No forced workflow barriers or integration phase. No
scripts modify product source or PI state after launch. No feedback, silent retry,
replacement worker, successor, repair message or human intervention.

The runner starts at most one project per invocation. Before advancing, an observer
reviews the completed record and source history. Infrastructure or study-integrity
failures stop the batch and remain archived. Ordinary coding failures do not cause
replacement or fixture changes inside a frozen batch. Review never contacts workers.

One initial preparation was rejected with **zero model launches**: even the native
`--version` probe created helper files in the checked worker profiles. That prepared
directory and recorder snapshot are retained. Version probing now uses a separate
disposable preflight profile, leaving actual worker profiles config-only. A regression
test covers this effect. The corrected candidate preparation follows **269 passing
repository tests**, including 20 recorder tests and 11 fixture tests with 12 deliberate
mutation subcases. No software trial was replaced and no PI behavior was changed.

A study registry binds those batches to the source-hash-verified protocol gate and
one immutable PI snapshot. It limits ordinary calibration to two candidates; an
unsaturated three-project candidate is selected rather than silently retuned.
Ceiling and evaluation must use that candidate's exact fixture/checker, and
evaluation requires a successful single-worker ceiling case. A study-wide lock
rejects overlapping project launches. New batch directories do not reset the budget.
Every trial is prepared from frozen copies, not repeatedly copied from a live tree.

## Verification and measurements

Before models: require passing reference implementation, contract-mutation checks,
focused recorder tests, complete repo tests and independent review; then freeze
source, checker, tasks, architecture, recorder, test sources and PI hashes.

The primary endpoint is the frozen checker's accepted integrated source. Record
native process completion independently: correct source at timeout is not a fully
completed native workflow, and a clean process exit is not product acceptance.
Altered checker/objective/task/architecture inputs invalidate acceptance.

Record per-contract failures and component checks, actual worker launch/exit,
aggregate worker-seconds and concurrency factor, setup/archive/final-verification
time, per-worker reported token subsets, commands, patches and agent completion
claims. No outside integration/repair time exists: natural repairs stay inside the
worker window. Missing token fields are unknown, not zero; timeout usage may be partial.

Sample source bytes every 100ms and on native patch events. Replay recorded states
**after workers exit**, using the same frozen checker on isolated copies. Report
first accepted and first durably accepted sampled state separately from final
verification and worker exit. Sampling is not an atomic filesystem journal; do not
claim an exact first passing instant. Replay evaluation errors remain visible.
Unsupported filesystem entries are recorded, sampled object/checker hashes are
verified, and final replay is reconciled with final scoring. A mismatch cannot be
reported as durably accepted. Freshness checks allow only the initial config file
in each native profile immediately before launch, not merely an unchanged config.

Use logs plus retained source to identify distinct useful contributions, duplicate
implementation, stale patches/assumptions, overwritten work, and repairs. Counts
must have concrete evidence; inspection overlap is not implementation duplication.
Do not invent a duplicate-effort fraction when token attribution is unavailable.

For PI, separately record onboarding/enrollment span, context refreshes, declarations,
repair/handoff operations, rejected commands and observable influence on behavior.
Mixed tool-call time is not isolated PI service latency. Output bytes are not exact
PI tokens. Do not treat total tokens, command counts or longer individual workers
as an efficiency verdict. Compare accepted project outcomes before costs.

Classify failures conservatively: coding, stale assumptions, conflicting changes,
missing integration, decomposition, PI misuse, missing/stale PI information,
infrastructure or ambiguous. Distinguish information exposed but unused from
information PI never exposed. Preserve ties and negative outcomes.
