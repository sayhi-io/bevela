# Worker path

Use `onboard --query "task keywords"` from the actual checkout for the read-only
first pass. After selecting an exact candidate, use `onboard --scope SCOPE
--workstream ID` to read intent, applicable invariant revisions, precedents,
environment requirements, readiness, handoffs and nearby work. It prints an
explicit enrollment template but never enrolls automatically. `start` remains the
lower-level orientation command.
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

Inspect nearby declarations and route around overlap when practical. Shared paths
or semantic boundaries are advisory convergence. When coordination is needed, send
a bounded request through the authorized orchestrator/provider route, preserving
the affected scope and desired response. Do not create a parallel chat history in
presence. Renew at meaningful transitions and before the one-hour lease expires.

Build and validate with the enrolled environment or the repository's documented
toolchain. If the environment or acceptance criterion is missing, report precisely
what cannot yet be established. Do not automatically solve missing project context
by expanding Project Intent.

## Reporting and successor

Read `report --help`, `report-status --help` and the source repository's
`docs/REPORTING.md` for the installed packet schema. Submit actual evidence, source
references, readiness dimensions and the next bounded action. Keep artifact hashes
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

Verify `report-status` and `start` reflect the available report accurately, then
release your registration with `enroll --workstream ID --session OWN-STABLE-ID
--inactive` (or your original `--codex` selection). Release records the end of
presence; it does not publish a report or mark durable work complete.
