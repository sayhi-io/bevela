---
name: project-intent
description: Orient workers and orchestrators to enrolled Project Intent assignments, scoped architecture, nearby work, reporting, and successor handoffs. Use for development coordinated through Project Intent or recovery of an existing enrolled workstream.
---

# Project Intent

Carry an actual assignment from orientation through evidence and continuity. The PM
provider owns durable project truth; Project Intent assembles applicable context and
observations. Git owns source history. A session lease is neither an assignment nor
proof of current inference, and delivery of a continuation is not completion.

## Bootstrap

Read the task checkout's AGENTS.md. Discover the installed `project-intent` command;
in the SayHi workspace use `/home/meanaverage/sayhi/bin/project-intent`. Run `--help`
and command-specific help before relying on flags. Use the checkout's Project Intent
README and linked operational docs for the installed version. Do not search private
service configuration or old provisioning scripts for credentials.

From the actual execution checkout, run `discover --query "task keywords"`, then
`start --workstream ALIAS-OR-NATIVE-ID`. Add `--scope` when needed. Select candidates
against the existing user task, ownership, scope, exclusions and acceptance criteria;
a matching title or reference checkout does not grant ownership. Broaden an overly
specific search before concluding enrollment is missing. Missing snapshot candidates
do not prove no provider issue exists: ask the authorized coordinator to inspect the
native inventory, preserving the packet needed to reconcile an existing record.

Record what context is absent. An unenrolled environment requirement, invariant or
acceptance criterion is project-information debt unless the supported model cannot
represent it. Offline orientation is useful last-known context; it cannot establish
current remote state or authorize a remote mutation.

## Choose your role

- For implementation, assessment, review or successor work, read
  [the worker path](references/worker.md).
- For coordination across workers, recovery, provider reconciliation or bounded
  continuation, read [the orchestrator path](references/orchestrator.md).
- For reviewing this Project Intent source before integration, read the repository's
  `docs/INTEGRATION_GATE.md`. The source-seal helper in this skill is specific to the
  Project Intent repository, not a general export tool for consumer repositories.

Follow the user's existing authorization. Routine continuation within that scope
does not require the human to type IDs or relay messages. Record the particular
missing authority only when the next action actually exceeds it; enrollment,
publication and session attachment do not independently expand it.
