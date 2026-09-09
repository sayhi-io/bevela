# Project Intent

**Independent workers. One coherent product.**

Shared project state for coding agents working across repositories, worktrees and architectural boundaries.
See what neighboring workers report changing, understand the contracts you share, and reconcile the combined result.

[Results](RESULTS.md) · [How it works](#how-it-works) · [Get started](#get-started) · [Architecture](docs/ARCHITECTURE.md)

---

## A weaker model with PI beat a stronger model without it.

On the original seven-seam migration, **Luna Low with Project Intent preserved every seam in both runs.**
Neither Luna Low nor the stronger Sol Low configuration completed the whole project without PI.

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

**Two complete projects with PI. None across the five ordinary runs.**

Each project used two concurrent workers. Every point requires the producer **and** consumer contract to survive together—not just a worker's own tests. Low reasoning effort throughout; PI behavior v0.05; small exploratory batches, with every run shown.

[Explore the A/B/C discovery →](docs/results/seven-seams.md#low-effort-abc-comparison)

---

## The problem lives between the changes

One worker migrates prices from dollars to cents. Another builds a receipt against the old representation.
Both can pass focused tests. Together, they can print **$1,250.00 instead of $12.50**.

Project Intent began inside SayHi: one product assembled from many independently developed repositories.
APIs, schemas, security boundaries and runtime assumptions cross those repository lines. A human should not have to relay every relevant change between workers.

Git tells you what changed. PI adds recorded task intent, architectural relationships and declared neighboring work—including work that has not landed yet.

## How it works

**Keep the workers' normal tools. Give them shared project context.**

1. **Find the actual task.** Inspect its scoped requirements, constraints, acceptance criteria and related architecture.
2. **Declare the work.** Enroll your own session with its checkout, paths, seams and intended changes.
3. **Reconcile the boundary.** Refresh peer context and inspect the affected code. For competing repairs, agree on one repairer and a bounded set of paths.
4. **Verify the combined result.** Check both sides of the contract, retain useful evidence and hand off unresolved impacts.

Workers get **related task requirements**, **last-known peer summaries** and **explicit repair agreement**.
A shared seam is context—not a lock or permission to take over someone else's work.

[Worker workflow](skills/project-intent/SKILL.md) · [Repair agreement](docs/REPAIR_COORDINATION.md) · [Reporting & handoff](docs/REPORTING.md)

## A correctness win is not yet a concurrency win

The A/B/C result established an observed capability advantage. The next question was **why**:
better peer context, useful parallel coordination, or both?

The later Luna Medium studies gave ordinary workers the same task information and added single-worker baselines.

### Assigned roles: more distinct contributions, no speedup

With a predefined producer/consumer split, both workers landed distinct, retained contributions during overlap in **3/3 PI projects**, versus **0/3 ordinary projects**.

But **every condition passed 7/7**. One ordinary worker had the lowest median project completion time and token usage on this small task. The suspected limit was that coordination overhead outweighed the short serial workload; the next completed study removed the predefined split.

[Split-role study →](docs/results/concurrency.md)

### Identical objectives: awareness did not become a work split

Three workers received the same complete objective. **Neither arm divided implementation usefully.**
One worker implemented the entire migration in every project; the others mostly attempted duplicate work.
All conditions still reached 7/7, and PI added overhead.

The suspected limit: broad declarations did not establish agreed responsibilities before one worker could finish.
The proposed next test is a longer, genuinely parallel task with equal information and no prescribed allocation. **It has not been run.**

[Self-organizing study →](docs/results/self-organizing.md)

**Correctness. Project time. Worker effort. Useful concurrency.** We measure them separately.
More tokens are not automatically worse; more active processes are not automatically progress.

[All results, newest first →](RESULTS.md) — including failures, interrupted attempts, backend versions and follow-up questions.

---

## Mission Control

**A read-only view of the project—not a control panel for its workers.**

Browse workstreams, architecture, reports, worker/session observations and attention indicators.
The experimental [Workstream Map](docs/WORKSTREAM_MAP_EXPERIMENT.md) shows declared boundaries and convergence pressure.

Historical registrations are not a headcount. Missing observations do not mean no one is working.
Integration context and repair plans are CLI features; Mission Control does not yet display those plans.

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

## Boundaries worth knowing

**Active SayHi dogfood. Experimental infrastructure. Not a generally available production service.**

- **Declarations, not surveillance.** PI does not detect hidden edits or push automatic code-change notifications. Workers must refresh context and check the actual source.
- **Coordination, not authority.** A lease, repair claim or “done” report is neither editing permission nor proof of correctness. No scheduling or filesystem fencing.
- **Explicit scope.** Worker integration context is scoped. Current repair agreement requires the same configured scope feed and local repository/host—not arbitrary cross-repository repair.
- **Clear ownership.** Providers own durable task truth; Git owns source history. Offline snapshots and retained worker summaries are last-known context, not guarantees of current remote state.
- **Source is not deployment.** Review, CI, merge and activation are separate. No claims of hostile-tenant isolation, distributed fencing or production high availability.

## Go deeper

- **Evaluate:** [Results](RESULTS.md) · [Methodology](docs/CLI_AB_EVALUATION.md) · [Original seven seams](docs/CLI_SEVEN_SEAMS.md) · [Refund torture](docs/CLI_TORTURE_REFUNDS.md)
- **Understand:** [Architecture](docs/ARCHITECTURE.md) · [Read model](docs/READ_MODEL.md) · [Worker skill](skills/project-intent/SKILL.md)
- **Operate:** [Operations](docs/OPERATIONS.md) · [Integration gate](docs/INTEGRATION_GATE.md) · [Session connector](docs/SESSION_CONNECTOR.md)

---

*The goal is not more agent conversation. It is a coherent product after concurrent changes.*
