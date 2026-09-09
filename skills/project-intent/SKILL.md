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
README and linked operational docs for the installed version. Run `project-intent docs`
for exact installed document paths (also returned by `onboard`). Read only available
paths. On older installations without `docs`, resolve this skill directory's symlink
and use its source release's `../../docs/`; do not append `docs/` inside the skill.
Missing documents are an installation gap, not a reason for a workspace-wide search.
For onboarding troubleshooting, restrict searches to the task checkout's documentation
and these installed paths. Do not search other sessions, transcripts, evaluation
archives, home directories, private service configuration or provisioning scripts.
An explicitly assigned audit of such evidence is a separate task, not this fallback.

From the actual execution checkout, prefer `onboard --query "task keywords"` for the
read-only first pass, then rerun `onboard --scope SCOPE --workstream
ALIAS-OR-NATIVE-ID` for the selected candidate. It combines discovery with the
same orientation that `start` provides and prints an explicit enrollment template;
it never enrolls or assigns a worker automatically. `discover` and `start` remain
available as lower-level commands. Add `--scope` when needed. Select candidates
against the existing user task, ownership, scope, exclusions and acceptance criteria;
a matching title or reference checkout does not grant ownership. Ranked partial
matches include matched/unmatched terms; they are suggestions, not confidence or
assignment. If the query is empty of useful matches, run `discover --scope SCOPE`
**without --query**, preserving the same `--worker-config` and `--checkout` options,
and inspect that scope's cached inventory before considering task registration.
Use the returned `inventory_recovery` command when available. Do not drop the scope
to broaden a search. Missing snapshot candidates do not prove no provider issue
exists. Only if no inspected candidate fits, use the configured
`task-register` route to inspect live native inventory and record the task the user
already assigned. Read [task registration](../../docs/TASK_REGISTRATION.md) in this
skill's source release for its packet and preview/submit flow. Reuse an existing native
record when appropriate; do not invent new work or borrow unrelated assignments.
Workers perform this bookkeeping themselves under the configured local capability;
no routine human ID lookup or separate coordinator queue is required. If that route
is unavailable, report the precise tracking gap. It does not itself revoke otherwise
authorized work; honor any explicit enrollment/admission prerequisite.

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

For a checkout instruction template, adapt
[worker instructions](assets/worker-instructions.md) with the actual CLI and local
scope/configuration. Version new evaluation inputs separately; never rewrite prior
trial instructions or outputs to apply this guidance retroactively.
