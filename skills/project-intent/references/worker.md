# Worker path

Use `onboard --query "task keywords"` from the actual checkout for the read-only
first pass. After selecting an exact candidate, use `onboard --scope SCOPE
--workstream ID` to read intent, applicable invariant revisions, precedents,
environment requirements, readiness, handoffs and nearby work. It prints an
explicit enrollment template but never enrolls automatically. `start` remains the
lower-level orientation command.
Before concluding no candidate fits, run `discover --scope SCOPE` without a query,
retaining the original worker-config and checkout options, and inspect the scoped
inventory. Do not substitute a workspace/transcript search. Then use the installed
`task_registration` path returned by `project-intent docs`: preview live native inventory, select an existing issue
or record the already user-assigned task, submit the reviewed choice, then onboard
and enroll. This records an assignment; it does not invent one or grant execution.
Keep uncertain receipts explicit and retry the original packet, never a renamed task.
Keep an explicit reference to the revisions and source being evaluated. Missing
conformance evidence is unknown; a later accepted revision requires reconciliation
with older evidence, not retroactive failure of the older claim.

Enroll your own session from your actual checkout. For a normal Codex thread,
`enroll --workstream ID --codex` selects its own session; for a worker without a
distinct supported Codex identity, use `--session OWN-STABLE-ID` for presence only.
Subagents may inherit a parent's `CODEX_THREAD_ID`: an inherited value alone is not
proof of a distinct worker identity. Never reuse a parent's thread identity or attach
someone else's telemetry.

Declare `--access edit --touching-path relative/path` for edit scope, or
`--access inspect` for assessment/review. Add current `--touching-seam`, prospective
`--approaching`, and `--avoid-path`/`--avoid` as applicable. Exact checkout, branch
and HEAD are observed locally; the workstream's reference checkout may belong to
another owner. A paused worker need not enroll merely to validate its handoff.

Use nearby context to account for the code/data your change affects. A neighboring
assignment or path declaration is not a prohibition on repairing your change's
consequences; respect actual user exclusions, not invented ownership walls.
Read `integration_context.related_work`, not just active registrations: a related
task can change a dependency before its worker enrolls. `last_known_workers` retains
released/expired summaries as declarations, not proof of current activity or success.
Declare actual files/directories in `--touching-path`; architecture labels belong in
`--touching-seam`, not invented filesystem paths.

For a contract change, keep `--working` concise and specific about the affected
symbols/fields/units and their replacements. At handoff include the resulting contract,
checks and any unresolved consumer impact, not just "done". This is a current work
summary, not a chat channel. A stable helper can insulate its callers from storage
changes; direct imports and field/unit assumptions still need reconciliation.

Before claiming completion on overlapping work, use the printed
`integration_context.refresh` command and inspect current affected imports/callers.
Initial reads and checks before a peer's relevant edit do not validate the combined
result. Where execution is authorized, exercise the affected producer and consumer
together (including module loading); helper-only tests may miss a broken caller.
If a peer's relevant change is still pending or checks cannot run, state that
integration is pending/unverified. Do not wait on unrelated work or override an
explicit restriction on testing; do not present unverified integration as complete.

Ordinary edits need no repair ceremony merely because they share a seam.
If workers might make competing fixes to a specific break, read
[repair coordination](../../../docs/REPAIR_COORDINATION.md): one worker accepts a
path-bounded repair plan and the named peer explicitly acknowledges it. Only the
agreed repairer edits those paths; independent paths on the same seam stay free.
Acceptance or a competing claim is not acknowledgment. Check current producer and
consumer behavior before closure, using the agreed validation scope. Before handoff,
reconcile the peer's actual result; neither a stale failure report nor leaving a known
regression for "the other assignment" establishes completion.
When further coordination is needed, send
a bounded request through the authorized orchestrator/provider route, preserving
the affected scope and desired response. Do not create a parallel chat history in
presence. Renew at meaningful transitions and before the one-hour lease expires.

Build and validate with the enrolled environment or the repository's documented
toolchain. If the environment or acceptance criterion is missing, report precisely
what cannot yet be established. Do not automatically solve missing project context
by expanding Project Intent.

## Reporting and successor

For a durable handoff, review, unresolved issue, or a task that explicitly requires
reporting, use `report` and the installed `reporting` document if its schema is needed.
Routine self-contained edits do not need a separate report just to end presence;
summarize the result/checks when releasing enrollment and in the normal task response.
Durable reports carry actual evidence, source references, readiness and next action. Keep artifact hashes
and invariant revision assertions explicit; a prose summary alone does not bind
evidence to every applicable invariant.

Local creation, pending publication, publication uncertainty and confirmed native
publication are different states. A worker can prepare and submit a local report
without provider credentials. An authorized publisher performs remote publication.
On an uncertain result, reconcile the native receipt before requesting a retry.

Keep implementation, independent review, commit, required CI, merge and production
readiness separate. Report owner assertions as assertions, and specify which exact
source the independent review covered. Include unresolved findings, evidence limits,
environment restrictions and successor instructions. Do not restart completed work
to make a card look live.

When a report was submitted, verify its status. Then
release your registration with `enroll --workstream ID --session OWN-STABLE-ID
--inactive` (or your original `--codex` selection). Release records the end of
presence; it does not publish a report or mark durable work complete.
