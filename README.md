# Project Intent

### Shared project state for concurrent coding workers.

Project Intent helps independent workers understand **what neighboring work is changing, where their tasks meet, and what must still work together**.

It began inside SayHi: one product assembled from many independently developed repositories, with AI workers changing APIs, schemas, security boundaries and runtime assumptions at the same time. A change can be correct inside one repository and incompatible with work happening elsewhere. The same problem appears between worktrees and between workers sharing one checkout.

The aim is to let those workers anticipate incompatible changes, discover related work and reconcile shared boundaries without a human coordinating every interaction.

> The goal is not more agent conversation. It is a coherent product after concurrent changes.

[Results](RESULTS.md) · [Architecture](docs/ARCHITECTURE.md) · [Worker workflow](skills/project-intent/SKILL.md) · [Operations](docs/OPERATIONS.md)

## The problem: locally correct, jointly broken

One worker changes prices from dollars to integer cents. Another builds a receipt against the old representation. Their focused tests can pass while the combined receipt charges the wrong amount.

Git records source changes. It does not, by itself, tell a worker what a peer **intends** to change across another repository, which contract that peer is preserving, or whether somebody has agreed to repair the resulting break.

Project Intent exposes scoped task and architecture records alongside workers’ declared paths, seams and work summaries. Workers can refresh that context, inspect the actual code and validate the combined behavior before claiming completion.

## What workers share

| Primitive | What it provides |
| --- | --- |
| **Intent** | Recorded tasks, constraints, acceptance criteria and applicable architecture. |
| **Presence** | Session leases, actual checkout identity and worker-declared editing boundaries—not proof of active inference. |
| **Seams** | Named architectural boundaries connecting related work, even across files or repositories. |
| **Integration context** | Related task requirements and last-known peer summaries, including released registrations. |
| **Repair agreement** | A cooperative, path-bounded plan with one repairer and explicit acknowledgment from named peers. |
| **Evidence & handoff** | Revision-aware reports, source-bound validation assertions and retained successor context. |

This is **cooperative coordination, not enforcement**. PI does not discover every hidden edit, push automatic code-change notifications, lock a seam, schedule workers or grant execution authority. Workers must declare changes, read refreshed context and check the actual integrated source. Missing observations remain unknown; a lease or a “done” summary is not a correctness certificate.

Context is limited to the selected configured scope. Current repair agreement requires cooperating workers using the same scope feed and local repository/host; it is not an arbitrary cross-repository or cross-scope repair service. The CLI exposes integration context and repair plans; Mission Control does not yet display those plans.

Durable task truth stays with the configured provider; Git owns source history. Local snapshots support last-known orientation, not a claim that remote state is current. An already assigned task can be recorded through a configured, separately authorized [registration capability](docs/TASK_REGISTRATION.md).

## What the experiments show

We measure **accepted project results**, elapsed project time and aggregate worker effort separately. More tokens are not automatically worse, and overlapping model processes are not automatically useful parallel work.

| Finding | Evidence | What it does—and does not—show |
| --- | --- | --- |
| **Low-effort A/B/C breakthrough** | Luna Low + PI: **7/7, 7/7**. Luna Low without PI: **0/7, 2/7**. Sol Low without PI: **3/7, 4/7, 3/7**. | Luna Low with PI outperformed both ordinary configurations on final integrated correctness, including the stronger Sol model. |
| **Predefined roles stayed more distinct** | Luna Medium, two workers: separate retained contributions during overlap in **3/3 PI** projects versus **0/3 ordinary** projects. | Both arms still finished **7/7 in 3/3**. A single ordinary worker had the lowest median completion time and token usage on this small fixture. |
| **Identical goals did not become a parallel team** | Luna Medium, three workers with the same complete objective: **no useful implementation partition in either arm**. | All projects reached 7/7. PI added overhead; one worker implemented the whole migration in each project. |

The A/B/C comparison asks whether PI can help a lower-capability configuration preserve the combined project better than simply using a stronger model without it. The observed answer was yes in these small batches. The later studies below ask a different question: whether that value comes from useful concurrency, beyond access to peer task context.

The latest small-fixture results suggest two limits: one worker can finish before coordination pays off, and awareness of peers does not necessarily produce an agreed division of work. A proposed next study would hold task information equal on a longer, genuinely parallel task and measure whether workers establish useful responsibility boundaries; it has not been run.

**[Read the results →](RESULTS.md)**

Newest-first study history, every recovered run, backend behavior versions, failures, timing definitions and follow-up questions. Negative findings and interrupted attempts stay visible.

## Mission Control

Mission Control is the read-only human observatory over the normalized project state. It shows workstreams, architecture, reports, worker/session observations and attention indicators. The experimental [Workstream Map](docs/WORKSTREAM_MAP_EXPERIMENT.md) visualizes declared boundaries and convergence pressure.

It is not a live editor, repair dispatcher or authority surface. Provider credentials remain outside the browser. Freshness and observation gaps matter: historical registrations are not a count of people, and an unavailable worker observation does not mean no one is working.

## Worker workflow

1. **Orient.** From the actual task checkout, discover candidates and inspect the exact scoped assignment. Matching text is a suggestion, not ownership.
2. **Enroll.** Register your own session with the checkout, paths, seams and bounded work you actually intend to perform.
3. **Integrate.** Refresh relevant peer context and inspect affected code. For competing fixes to a concrete break, agree on a repairer and affected paths; ordinary independent edits do not need a repair ceremony.
4. **Validate and hand off.** Exercise both sides of affected contracts, record unresolved impacts and release presence with a useful summary. Durable evidence reports and provider publication are separate operations.

The [worker skill](skills/project-intent/SKILL.md) defines the supported procedure. It supplies context to native coding workers; it does not replace their execution loop.

## Local development

Python **3.11+**; no runtime dependencies outside the standard library. From this repository:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m unittest discover -s tests -v
```

Activate that environment before changing to your task checkout:

```bash
source .venv/bin/activate
cd /absolute/path/to/your/task-checkout
project-intent onboard --query "task keywords"
project-intent onboard --scope YOUR_SCOPE --workstream SELECTED_WORKSTREAM
```

Onboarding requires a configured local worker scope map; installation alone does not discover arbitrary provider projects. Review the returned assignment and use its enrollment template. The [operations guide](docs/OPERATIONS.md) covers configuration and the distinction between credential-free local orientation and authorized provider access.

To serve Mission Control with your private service configuration:

```bash
project-intent serve --config /private/project-intent/config.json --port 8290
```

Open `http://127.0.0.1:8290`. Keep the service loopback-only unless a separately reviewed network, TLS and identity boundary is in place. Configuration and credentials are not part of this repository.

## Maturity and boundaries

Project Intent is **active SayHi dogfood and experimental infrastructure**, not a generally available production service. This repository includes the local service, CLI, normalized read model, observatory, cooperative repair protocol and experiment machinery.

It does not claim hostile-tenant isolation, distributed fencing, generalized scheduling or production high availability. Source integration, independent review, required CI, provider publication and runtime activation are distinct steps. A merged backend change is not automatically running in an existing deployment.

The working principles are simple: coordination is not authority; architecture extends beyond file collisions; explicit evidence matters more than enrollment counts; and uncertainty must remain visible.

## Documentation

| Start here | For |
| --- | --- |
| [Results](RESULTS.md) | Newest-first outcomes, limitations and next questions |
| [Architecture](docs/ARCHITECTURE.md) · [Read model](docs/READ_MODEL.md) | Components, authority and normalized state |
| [Worker skill](skills/project-intent/SKILL.md) · [Task registration](docs/TASK_REGISTRATION.md) | Orientation, enrollment and missing inventory |
| [Repair coordination](docs/REPAIR_COORDINATION.md) · [Reporting](docs/REPORTING.md) | Peer agreement, validation and durable handoffs |
| [Operations](docs/OPERATIONS.md) · [Integration gate](docs/INTEGRATION_GATE.md) | Configuration, review, release and recovery |
| [Session connector](docs/SESSION_CONNECTOR.md) | Bounded continuation of an existing session |
| [Evaluation methodology](docs/CLI_AB_EVALUATION.md) | Historical study design and measurement rules |
| [Original seven seams](docs/CLI_SEVEN_SEAMS.md) · [Refund torture](docs/CLI_TORTURE_REFUNDS.md) | Distinct fixtures and acceptance contracts |
| [Concurrency vs. context](docs/CLI_CONCURRENCY_STUDY.md) · [Self-organization](docs/CLI_SEVEN_SEAMS_SELF_ORGANIZING.md) | Newer matched study protocols |

Project Intent should earn its complexity by helping workers preserve a coherent combined result—not by making an activity dashboard look busy.
