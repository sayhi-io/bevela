# BEVELA (PI-Project-Intent)

*Do not take BEVELA™ if you are allergic to concurrent agents.*



## $1,250.00? For a cup of tea?

One coding agent changed prices from dollars to integer cents. Another kept building receipts as if nothing had changed.

Both pieces of code looked reasonable. The checkout total was even correct.

The receipt?

```text
tea:   $1250.00
cake:   $725.00
```

Welcome to concurrent software development with AI agents.

**Project Intent gives coding workers shared project state so independently reasonable changes can still become one coherent product.**

Workers can see neighboring intent, declared architectural seams, active work and integration context—across repositories, worktrees and component boundaries—before `$12.50` becomes `$1,250.00`.

[Results](RESULTS.md) · [How it works](#how-it-works) · [Get started](#get-started) · [Architecture](docs/ARCHITECTURE.md)

---

## We tried giving the problem a smarter model.

It still lost.

On the original seven-seam migration, **Luna Low with Project Intent preserved every seam in both runs.** Neither Luna Low nor the stronger Sol Low configuration completed the whole project without PI.

```text
SEVEN SEAMS / LOW-EFFORT A/B/C
============================

A   LUNA LOW / WITHOUT PI
    Run 1   [.......]   0/7
    Run 2   [##.....]   2/7

B   SOL LOW / WITHOUT PI
    Run 1   [###....]   3/7
    Run 2   [####...]   4/7
    Run 3   [###....]   3/7

C   LUNA LOW / WITH PI
    Run 1   [#######]   7/7
    Run 2   [#######]   7/7

# preserved seam   . failed seam
```

**Two complete projects with PI. None across five ordinary runs.**

Small exploratory batches, every run shown, low reasoning effort throughout. This does not prove PI makes weaker models smarter. It suggests something more interesting:

> **Sometimes the model is not the problem. The project state is.**

[Explore the A/B/C discovery →](docs/results/seven-seams.md#low-effort-abc-comparison)

---

## The problem lives between the changes

The tea bug is deliberately tiny because the failure mode is not.

A worker changes a schema. Another keeps using the old one. One migrates a security boundary. Another still assumes the previous authorization model. A producer and consumer can each pass their own tests while the combined product is wrong.

Project Intent began inside sayhi.io studio: one product assembled from many independently developed repositories, with AI workers changing APIs, schemas, runtime assumptions and security boundaries at the same time.

Git records what changed. **Project Intent records what workers say they are changing next, what boundaries they share, and what still has to work together.**

That is the gap PI is trying to close.

## How it works

**Keep the workers' normal tools. Give them shared project context.**

1. **Find the actual task.** Inspect its scoped requirements, constraints, acceptance criteria and related architecture.
2. **Declare the work.** Enroll the session with its checkout, paths, seams and intended changes.
3. **Reconcile the boundary.** Refresh peer context and inspect the affected code. For competing repairs, agree on one repairer and a bounded set of paths.
4. **Verify the combined result.** Check both sides of the contract, retain useful evidence and hand off unresolved impacts.

Workers get **related task requirements**, **last-known peer summaries** and **explicit repair agreement**.
A shared seam is context—not a lock, a scheduler or permission to take over someone else's work.

[Worker workflow](skills/project-intent/SKILL.md) · [Repair agreement](docs/REPAIR_COORDINATION.md) · [Reporting & handoff](docs/REPORTING.md)

## A correctness win is not yet a concurrency win

The A/B/C result was exciting. Then we tried to figure out what it actually meant.

Was PI helping because workers had better peer context? Was it enabling useful parallel work? Was it merely rescuing a weaker model? Or were we testing the wrong thing entirely?

So we kept running experiments—and kept the inconvenient results.

### Great teamwork. Still slower than one worker.

With a predefined producer/consumer split, both PI workers landed distinct, retained contributions during overlap in **3/3 projects**, versus **0/3 ordinary projects**.

That is the behavior we wanted to see.

The economics were less flattering: **every condition still passed 7/7**, and one ordinary worker had the lowest median completion time and token usage on this small fixture. PI made the concurrent work cleaner, but the task was too short for parallelism to repay its coordination overhead.

[Split-role study →](docs/results/concurrency.md)

### Three agents walk into a repository. One does all the work.

Next we gave three Luna Medium workers the **same complete objective** and removed the predefined split.

PI told them about one another. They still did not meaningfully divide the implementation.

One worker implemented the entire migration in every project; the others mostly attempted duplicate work. Ordinary and PI projects all reached 7/7, and PI added overhead.

That does not necessarily mean PI failed. It may mean **task decomposition belongs to an orchestrator, while PI should stay focused on keeping already-divided work coherent.**

[Self-organizing study →](docs/results/self-organizing.md)

### The harder refund fixture moved the needle again

On a more difficult overlapping-edit migration, Luna Medium ordinary workers scored **0/7, 6/7, 6/7**. Luna Medium + PI scored **0/7, 7/7, 7/7**.

That is promising, but not clean enough to declare victory. One PI run failed completely, Luna High solved the task once without PI, and the treatment still bundles shared context with coordination behavior.

So the next methodological shift is deliberate: **stop making the model weaker to make PI visible. Make the project harder while keeping the worker capable enough to use PI reliably.**

[Refund torture study →](docs/results/refunds.md)

### Yeah, yeah. You only use Codex Astra XHigh.

Fair objection.

A benchmark can make PI look useful simply by choosing a worker that is weak enough to lose track of a concurrent project. But that creates a nasty confound: the same weaker worker may also be worse at following PI's own coordination instructions.

So we are changing the test, not weakening the model.

Our working hypothesis is that the cleanest evaluation regime looks like this:

- use a **strong worker whose PI protocol compliance is already reliable**;
- make the **distributed software problem** difficult enough that concurrent ordinary workers do not succeed every time;
- keep the programming task within that model's actual capability;
- make the difficulty come from changing schemas, stale assumptions, cross-repository contracts, migration/versioning, retries, compatibility and integration—not puzzle tricks;
- freeze the task decomposition so PI is tested as a coordination substrate, not as an accidental orchestrator.

In other words, if Sol Medium can follow PI correctly but also solves the fixture 10/10 without it, **the fixture is too easy**. The answer is not to drop to a dumber model until something breaks. The answer is to build a harder project.

We are currently designing that benchmark: a longer, genuinely distributed task where one capable worker can understand the system, several capable workers have meaningful work to do in parallel, and the shared seams are difficult enough that project state—not basic coding ability—becomes the variable under test.

> **Do not make the worker less capable to make Project Intent look useful. Make the coordination problem harder while keeping the worker capable.**

That is the standard we want the next round of results to meet.

**Correctness. Project time. Worker effort. Useful concurrency.** We measure them separately.
More tokens are not automatically worse; more active processes are not automatically progress.

[All results, newest first →](RESULTS.md) — including failures, interrupted attempts, backend versions and follow-up questions.

---

## One product. A dozen-ish repositories. What could go wrong?

Project Intent started because sayhi.io studio is one product assembled from nearly a dozen repositories.

Once AI workers started changing several of them concurrently, the human operator became the world's least interesting message bus: constantly relaying what one worker was doing to another worker somewhere else.

PI is an attempt to replace that human relay with durable shared project state.

The same coordination problem appears at several scales:

- different repositories sharing an API or product contract,
- different worktrees changing related behavior,
- several workers sharing one checkout,
- a worker handing work to a successor after its session ends.

PI does not require those workers to become nodes in a proprietary agent graph. They remain ordinary coding workers. PI is the shared substrate around them.

## Mission Control, without the commanding

**Mission Control is a read-only observatory—not a control panel for its workers.**

Browse workstreams, architecture, reports, worker/session observations and attention indicators. The [Developers Board and work calendar](docs/ACTIVITY_VIEWS.md) separate current observations from timestamped evidence; the experimental [Workstream Map](docs/WORKSTREAM_MAP_EXPERIMENT.md) shows declared boundaries and convergence pressure.

Historical registrations are not a headcount. Missing observations do not mean no one is working. Integration context and repair plans are CLI features; Mission Control does not yet display those plans.

<!-- Screenshot placeholder. Recommended capture: Workstream Map with several simultaneous workers, visible seams, and one overlap or repair state. -->

> **Screenshot coming soon.**

## Get started

Python **3.11+**. No runtime dependencies outside the standard library.

From this repository:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m unittest discover -s tests -v
source .venv/bin/activate
```

With your [local worker scope map configured](docs/OPERATIONS.md), move to the **actual task checkout**:

```bash
cd /absolute/path/to/your/task-checkout
project-intent onboard --query "task keywords"
project-intent onboard --scope YOUR_SCOPE --workstream SELECTED_WORKSTREAM
```

Review the assignment, then follow the returned enrollment template. Installation alone does not discover arbitrary provider projects. A missing task can be recorded through a separately configured, authorized [registration capability](docs/TASK_REGISTRATION.md).

<details>
<summary><strong>Run Mission Control locally</strong></summary>

With the environment above active and your private service configuration prepared:

```bash
project-intent serve --config /private/project-intent/config.json --port 8290
```

Open `http://127.0.0.1:8290`. Keep it loopback-only unless a separately reviewed network, TLS and identity boundary is in place. Provider credentials stay outside the browser and repository.

See [Operations](docs/OPERATIONS.md) for configuration, recovery and deployment boundaries.

</details>

## What PI does not magically solve

**It is not your orchestrator.** PI currently does not decide who should work on what. That may belong to a separate orchestrator agent.

**It does not read minds.** PI is declaration-based. Hidden edits remain hidden until a worker reports or discovers them.

**It does not grant authority.** A lease, repair claim or “done” report is neither editing permission nor proof of correctness.

**It does not make bad code good.** The integrated project still has to pass its actual tests and acceptance checks.

**It is not distributed locking.** Current repair agreement is cooperative and scoped; there is no filesystem fencing or global seam lock.

**It is not deployment.** Review, CI, merge and activation remain separate concerns.

Those are intentional boundaries, not hidden footnotes.

## Go deeper

- **Evaluate:** [Results](RESULTS.md) · [Methodology](docs/CLI_AB_EVALUATION.md) · [Original seven seams](docs/CLI_SEVEN_SEAMS.md) · [Refund torture](docs/CLI_TORTURE_REFUNDS.md)
- **Understand:** [Architecture](docs/ARCHITECTURE.md) · [Read model](docs/READ_MODEL.md) · [Worker skill](skills/project-intent/SKILL.md)
- **Operate:** [Operations](docs/OPERATIONS.md) · [Integration gate](docs/INTEGRATION_GATE.md) · [Session connector](docs/SESSION_CONNECTOR.md)

---

*Independent workers. One coherent product. And, ideally, reasonably priced tea.*
