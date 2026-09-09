# Project Intent

### Coordination infrastructure for concurrent AI software workers.

Project Intent helps independent coding workers understand **what other workers are changing, where their work intersects, what must remain true, and how to reconcile a shared boundary before declaring success**.

Project Intent began with a concurrency problem: SayHi is one product assembled from nearly a dozen repositories, often with AI workers changing several of them at the same time. Those repositories are independently owned and developed, but they are not truly independent. Their APIs, schemas, security boundaries, runtime assumptions, and product behavior meet at seams that no single repository fully owns.

The original goal was to let workers in different repositories understand those shared seams—to anticipate incompatible changes, discover neighboring work, and help mend cross-repository breaks without requiring a human to continuously coordinate every interaction. As we built and tested that idea, the same failure mode became visible between workers in different worktrees and different parts of one repository: individually reasonable changes can still produce an incoherent combined system.

> **The goal is not to make agents talk more. The goal is to let concurrent workers converge on a coherent product.**

[Architecture](docs/ARCHITECTURE.md) · [Worker protocol](skills/project-intent/SKILL.md) · [Experiments](docs/CLI_AB_EVALUATION.md) · [Operations](docs/OPERATIONS.md)

---

## Why this exists

Modern coding agents are increasingly capable in isolation. A product with several of them working across repositories, worktrees, and architectural boundaries at once introduces a different class of failure.

One worker changes a representation. Another consumes the old representation. Both implementations can look reasonable locally. Both can pass focused tests. The product still breaks at the seam.

Giving the workers more reasoning time does not necessarily repair the missing shared state. They need a durable way to discover neighboring work and answer questions such as:

- What is another worker changing right now?
- Which contracts or architectural seams do our tasks share?
- Which assumptions may have become stale while I was working?
- Has somebody already accepted responsibility for a specific cross-seam repair?
- What evidence says the combined behavior works?
- What should a successor know after the original worker disappears?

Project Intent makes those facts explicit without turning development into a mandatory agent graph or central planner.

## What Project Intent provides

Project Intent maintains a bounded, scoped model of project work and exposes it to workers and humans through a local CLI and the read-only **Mission Control** observatory.

| Primitive | Purpose |
| --- | --- |
| **Intent** | The task, constraints, acceptance criteria and relevant architecture. |
| **Presence** | Which workers are active, where they are working and what they report doing. |
| **Seams** | Declared architectural boundaries where independently owned work may interact. |
| **Integration context** | Relevant peer requirements and last-known work summaries, including after handoff. |
| **Repair coordination** | One acknowledged repairer for a specific break and path set, without claiming ownership of the whole seam. |
| **Evidence** | Revision-aware reports and source-bound validation rather than an unqualified “done.” |
| **Mission Control** | A human-readable projection of workstreams, workers, architecture, attention and convergence state. |

Project Intent does **not** grant code authority, infer hidden edits, replace Git, schedule workers, or make a task correct because it appears in Mission Control. Its coordination model is deliberately cooperative and explicit.

## Experimental results

The repository includes matched worker studies because the central question is empirical: **does structured shared project state actually help concurrent workers produce a correct combined result?**

The first paired pilot did not show a clear quality advantage: ordinary and PI-aware Astra/Medium teams both completed the requested Status features and passed the same 11/11 independent acceptance checks. See [Pilot 01](docs/CLI_AB_PILOT_01.md).

A newer **seven-seam** fixture increases the concurrency pressure. Two native workers share a disposable checkout. One migrates seven data representations while the other builds seven consumers of those changing contracts:

| Seam | Concurrent pressure |
| --- | --- |
| Prices | integer cents ↔ dollar totals and labels |
| Stock | on-hand/reserved records ↔ sellable counts |
| Weights | integer grams ↔ kilogram totals and labels |
| Discounts | basis points ↔ percentages and discounted prices |
| Delivery | stored hours ↔ displayed days |
| Contacts | structured contacts ↔ email/name presentation |
| Orders | explicit states ↔ paid/pending/refunded labels |

The checker scores whether **both sides of each seam survive together**, from 0/7 to 7/7. Workers receive their complete tasks up front; there is no hidden model adjudicator, prescribed task order, injected failure notification, or automatic repair owner. See [Seven-seam study](docs/CLI_SEVEN_SEAMS.md).

### Luna Medium: concurrency study

A 12-project / 18-session Luna Medium study compared four execution regimes, with three fresh project trials per condition. There were no human interventions, retries, or timeouts. **Every project reached 7/7**, so this fixture showed no correctness advantage for PI at Luna Medium.

| Condition | Runs | 7/7 rate | Median project wall time | Aggregate worker time | Median aggregate tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| Single worker | 3 | 100% | **81.6s** | **81.6s** | **152,371** |
| Concurrent ordinary | 3 | 100% | 99.6s | 156.6s | 337,743 |
| Concurrent + PI | 3 | 100% | 141.4s | 236.9s | 949,750 |
| Single worker + PI | 3 | 100% | 118.3s | 118.3s | 371,850 |

Tokens include cached input and are usage counters, not measured GPU compute or monetary cost.

The project-level result is straightforward: **one Luna Medium worker was the best execution strategy for this small fixture.** It reached the same accepted result with the lowest median wall time and fewest recorded tokens. Concurrency did not pay for its coordination overhead here.

The concurrency behavior, however, differed materially. In all three ordinary concurrent runs, one worker attempted overlapping implementation against changes its peer had already made: there were **3 stale-patch failures** and **2 peer-label rewrites** across the three projects. In all three PI concurrent runs, both workers landed separate retained contributions while their peer was active: the producer handled the producer modules and the consumer handled `presentation.py`. *Peer-stale patch failures and peer-label rewrites both fell to zero.*

PI did not eliminate rework. Two PI projects required day-format integration corrections, and another encountered a self-inflicted cleanup-patch failure. PI also carried measurable overhead: enrollment completed roughly 30 seconds into each worker run, PI operations added about 1.9 aggregate seconds per concurrent project, malformed command groups required recovery, and PI-aware runs processed substantially more context.

So the measured conclusion is deliberately narrower than “PI is faster”:

> **On a problem one worker could already solve comfortably, PI made concurrent work less duplicative but did not make the project faster or cheaper.**

That is useful product guidance. Project Intent should stay cheap or largely dormant when there is no meaningful neighboring work. Its economic case depends on tasks large or distributed enough that useful parallelism can repay coordination cost.

It also motivates the next experiment: give several workers the **same complete objective**, remove harness-assigned producer/consumer ownership, and observe whether they can self-organize useful parallel work. A later, larger fixture is needed to test the wall-clock economics of parallelism when the serial critical path is long enough for concurrency to plausibly win.

Timing and token totals therefore remain separate from the primary concurrency phenomenon. A multi-worker system can consume more aggregate model compute while reducing project wall time on a sufficiently parallel task; conversely, as this study shows, concurrency can be unnecessary overhead when one worker can cheaply own the whole problem.

## Mission Control

Mission Control is the read-only human observatory over Project Intent state. It exposes workstreams, architecture, reports, worker/session detail, attention state and an experimental Workstream Map for seeing declared boundaries and convergence pressure.

<!-- Screenshot placeholder. Recommended capture: Mission Control Workstream Map with 3–5 simultaneous workers, visible seams, one overlap/repair state, and enough surrounding UI to establish that this is an operational product rather than a diagram. -->

> **Screenshot coming soon.**  
> Recommended asset path: `docs/assets/mission-control-workstream-map.png`

Mission Control deliberately does not mutate provider state or grant execution authority. The browser is an observatory; worker and operator mutations remain explicit local operations.

## How it works

A worker begins with the task it was actually assigned. Project Intent discovers the corresponding scoped workstream and returns its requirements, constraints, acceptance criteria, architecture and relevant neighboring work. The worker then enrolls its actual checkout, access mode, paths and semantic seams.

As work proceeds, other workers can see that declared state through scoped integration context. When two changes create a concrete shared break, workers can establish a path-bounded repair plan: one worker volunteers, affected peers acknowledge the plan, the repairer performs the agreed edit, and closure records validation evidence bound to the relevant source. Independent work on the same architectural seam remains independent.

At handoff, last-known summaries survive the worker session so a successor can reconstruct the project situation without inheriting the original conversation. Mission Control projects the same normalized state for humans.

```text
          task + constraints + architecture
                       │
                       ▼
                 Project Intent
                ╱      │       ╲
               ╱       │        ╲
          Worker A   Worker B   Worker C
             │          │          │
             └────── seams ─────────┘
                       │
                integration context
                       │
                 repair / validate
                       │
                       ▼
                 coherent product
```

## Quick start

Project Intent requires Python 3.11+ and currently has no runtime dependencies outside the standard library.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m unittest discover -s tests -v
```

Orient a worker from its **actual task checkout**:

```bash
project-intent onboard --query "task keywords"
project-intent onboard --scope YOUR_SCOPE --workstream SELECTED_WORKSTREAM
```

Review the returned assignment and enrollment template, then enroll the worker with its real checkout boundary and work summary. `discover`, `start`, and `enroll` are available as lower-level operations.

For local development of Mission Control:

```bash
project-intent serve --config /private/project-intent/config.json --port 8290
```

Then open `http://127.0.0.1:8290`. The development service requires independently configured credentials and should remain loopback-only unless a separately reviewed network/TLS/identity boundary is provided.

For the complete worker workflow, use the [Project Intent skill](skills/project-intent/SKILL.md). For deployment and authority boundaries, read [Operations](docs/OPERATIONS.md) first.

## Design principles

**Workers remain workers.** Project Intent does not replace native coding-agent behavior with a proprietary execution loop.

**Coordination is not authority.** Presence, a Workstream ID, a repair claim or a UI state never grants permission to edit or deploy.

**The product is larger than any repository or conversation.** Important task, architecture, peer and handoff state should survive individual model sessions and repository boundaries.

**Seams matter more than file collisions.** Concurrent workers can conflict semantically without touching the same file—or even the same repository. Project Intent records architectural boundaries as first-class coordination state.

**Evidence beats ceremony.** Enrollment counts, messages and claims are not success. The relevant combined behavior still has to work.

**Missing information stays missing.** Project Intent avoids silently converting absent observations into reassuring assumptions.

**Keep the baseline strong.** Evaluation controls retain normal source inspection, Git, repository documentation and ordinary communication. PI should earn its complexity rather than win against an artificially weakened worker.

## Origin

Project Intent started inside SayHi because the product is assembled from nearly a dozen repositories that nevertheless share product, API, schema, runtime and security seams. AI coding workers were increasingly able to work independently inside those repositories, and we wanted them to work on different parts of the product simultaneously without requiring a human to act as the permanent cross-repository coordinator.

The original problem was therefore concurrency across **shared seams**. A worker changing one repository needed a way to know that another worker was approaching a related boundary elsewhere, understand the intent and constraints on both sides, avoid preventable incompatibilities, and help repair a cross-repository break when one occurred.

Git could tell us what had already changed inside a repository, but not necessarily what a neighboring worker intended to change, which architectural contract it believed it was preserving, or how work in another repository related to the same product boundary. Conversation history could carry some of that information, but it was ephemeral and isolated to individual workers.

Building the system clarified that the same coordination problem exists at several scales: between repositories, between worktrees, and between independently owned areas of one codebase. That led to the current primitives—intent, presence, semantic seams, integration context, successor handoffs, repair agreement and source-bound evidence. Project Intent is the shared substrate intended to let concurrent workers preserve the coherence of **one product across many boundaries**.

## Current maturity

Project Intent is active SayHi dogfood and experimental infrastructure, **not a generally available production service**. The repository contains a real local service, CLI, normalized read model, Mission Control UI, worker/session observation, repair coordination and evaluation harnesses. Public/multi-host deployment, hostile-tenant isolation, distributed fencing, generalized scheduling and production HA are outside the current claim.

The local browser surface is read-only. Provider credentials stay outside the UI. Source changes do not automatically become a managed runtime release. See [Architecture](docs/ARCHITECTURE.md), [Read model](docs/READ_MODEL.md), [Operations](docs/OPERATIONS.md), and [Integration gate](docs/INTEGRATION_GATE.md) for the precise boundaries.

## Documentation

| Document | Go here for |
| --- | --- |
| [Architecture](docs/ARCHITECTURE.md) | authority boundaries, components and data flow |
| [Read model](docs/READ_MODEL.md) | normalized project/workstream projection |
| [Operations](docs/OPERATIONS.md) | local service, configuration, recovery and deployment limits |
| [Worker skill](skills/project-intent/SKILL.md) | canonical worker-facing workflow |
| [Task registration](docs/TASK_REGISTRATION.md) | recording an already assigned task when inventory is missing |
| [Repair coordination](docs/REPAIR_COORDINATION.md) | bounded peer agreement for a concrete cross-seam repair |
| [Reporting](docs/REPORTING.md) | evidence, publication and reconciliation |
| [Session connector](docs/SESSION_CONNECTOR.md) | bounded continuation of an existing session |
| [Workstream Map](docs/WORKSTREAM_MAP_EXPERIMENT.md) | Mission Control convergence visualization |
| [Evaluation](docs/CLI_AB_EVALUATION.md) | experimental principles and methodology |
| [Pilot 01](docs/CLI_AB_PILOT_01.md) | first matched A/B result and its negative finding |
| [Study 02](docs/CLI_AB_SHARED_CONTRACT.md) | harder cross-layer shared-contract study |
| [Study 03](docs/CLI_AB_STUDY03.md) | continuity/succession study design |
| [Seven seams](docs/CLI_SEVEN_SEAMS.md) | concurrent seven-contract fixture and recorder |

## Status

Development is intentionally evidence-driven. The immediate work is to run the self-organizing seven-seam study, commit its result packet, capture the first Mission Control screenshot, and then test the economics of PI concurrency on a larger task whose serial critical path is long enough for useful parallelism to plausibly reduce project wall-clock time.

Project Intent should become more complicated only where the experiments show that the complication helps workers converge.
