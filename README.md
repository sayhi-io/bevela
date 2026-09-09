# Project Intent

### Shared project state for concurrent AI software workers.

Project Intent helps independent coding workers understand **what other workers are changing, where their work intersects, what must remain true, and how to reconcile a shared boundary before declaring success**.

It began as a way to expose project intent to AI workers. In practice, the harder problem turned out to be concurrency: capable workers can each complete a locally reasonable task while producing an incompatible combined system. Project Intent is evolving into a coordination substrate for that problem.

> **The goal is not to make agents talk more. The goal is to let concurrent workers converge on a coherent project.**

[Architecture](docs/ARCHITECTURE.md) · [Worker protocol](skills/project-intent/SKILL.md) · [Experiments](docs/CLI_AB_EVALUATION.md) · [Operations](docs/OPERATIONS.md)

---

## Why this exists

Modern coding agents are increasingly capable in isolation. A repository with several of them working at once introduces a different class of failure.

One worker changes a representation. Another consumes the old representation. Both implementations can look reasonable locally. Both can pass focused tests. The project still breaks at the seam.

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

The first paired pilot was intentionally inconclusive. Ordinary and PI-aware Astra/Medium teams both completed the requested Status features and passed the same 11/11 independent acceptance checks. The PI-aware arm was not faster and used more reported input tokens. That result prevented us from claiming a benefit simply because the system looked useful. See [Pilot 01](docs/CLI_AB_PILOT_01.md).

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

### Latest seven-seam observations

> **RESULT PLACEHOLDER — replace with the committed trial summary before release.**
>
> Recent local trials have produced the most interesting signal so far: configurations that plateau without Project Intent have reached **7/7 with Project Intent**, including low-reasoning runs. Add the exact model × effort × PI/no-PI repetitions, run counts, hashes and timing here once their evidence bundle is committed. Do not promote the observation into a generalized productivity or model-superiority claim.

Suggested final chart once the result packet is committed:

```text
Seven seams preserved together

Luna · Low · ordinary      ████░░░  4/7   ← replace with measured aggregate
Luna · Low · Project Intent ███████  7/7   ← replace with measured aggregate
Sol  · Low · ordinary      ████░░░  4/7   ← replace with measured aggregate
Sol  · Low · Project Intent ███████  7/7   ← replace with measured aggregate

Illustrative layout only — values above are placeholders until linked evidence is committed.
```

The hypothesis worth testing is stronger than “more context helps”: **some apparent reasoning failures may actually be failures of project-state representation and worker concurrency.** We are treating that as a hypothesis, not a conclusion, until repetitions across fixtures and model strata support it.

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
                coherent project
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

**The project is larger than the conversation.** Important task, architecture, peer and handoff state should survive individual model sessions.

**Seams matter more than file collisions.** Concurrent workers can conflict semantically without touching the same file. Project Intent records architectural boundaries as first-class coordination state.

**Evidence beats ceremony.** Enrollment counts, messages and claims are not success. The relevant combined behavior still has to work.

**Missing information stays missing.** Project Intent avoids silently converting absent observations into reassuring assumptions.

**Keep the baseline strong.** Evaluation controls retain normal source inspection, Git, repository documentation and ordinary communication. PI should earn its complexity rather than win against an artificially weakened worker.

## Origin

Project Intent started inside SayHi while several increasingly autonomous coding workers were operating across projects such as SparkOps, Verify and the broader SayHi platform.

The original problem looked like **intent preservation**: give a worker enough durable project context that it could understand its assignment, architectural constraints and neighboring work without a human repeatedly reconstructing that context in chat.

Dogfooding exposed a more consequential problem. The workers were often individually capable; the fragile part was the **space between them**. Parallel changes could be locally correct and globally incompatible. Conversation history was ephemeral. Git showed what had changed, but not necessarily what another worker was about to change or which architectural contract it believed it was preserving.

That shifted the project from a passive intent record toward a bounded concurrency and convergence substrate: presence, semantic seams, integration context, successor handoffs, repair agreement and source-bound evidence. “Project Intent” remains the name because intent is still the foundation—but the system increasingly exists to help many workers preserve that intent **together**.

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

Development is intentionally evidence-driven. The immediate work is to commit and summarize the new seven-seam repetitions, replace the result/chart placeholder above with source-linked measurements, capture the first Mission Control screenshot, and continue testing whether the observed concurrency benefit survives across tasks and model/reasoning strata.

Project Intent should become more complicated only where the experiments show that the complication helps workers converge.