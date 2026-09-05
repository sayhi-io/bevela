# Deferred task 6: SparkOps execution consumer

Status: deferred mature buildout. It does not block the immediate supported reporting,
provider reconciliation, optional local session connector, skill, and integration
gate. Direct agent coordination is currently user-authorized; it must be reported
honestly and does not establish SparkOps execution admission.

Project Intent is an independent shared SayHi capability. The mature integration
lets SparkOps consume a bounded assignment/context request and contribute execution
facts. It should reuse SparkOps execution and session machinery after tracing an
operational path, rather than introducing a second runtime manager here.

| Responsibility | Owner |
| --- | --- |
| Durable initiatives, workstreams, assignment, architecture, dependencies, comments | PM provider |
| Scoped context, revision applicability, coordination requests, convergence and freshness | Project Intent |
| Execution admission, environment selection, credentials, placement, spawn/resume | SparkOps or another execution consumer |
| Run/session status, artifact and execution receipts | Execution consumer, correlated by Project Intent |
| Human observation and future explicitly authorized requests | Mission Control through the appropriate boundary |

## Boundary to validate later

A context request identifies scope, native workstream identity, selected architectural
revisions, allowed task paths/seams, exclusions, acceptance and environment requirements.
It is a declaration of intent, not a credential or admission grant. SparkOps selects
and admits execution using its existing authority and environment contracts, then
returns a correlated run/session receipt. Environment Catalog defines environments;
the product or lab determines what passing evidence means.

Existing terminal-session attachment is separate from new execution. A known UUID,
log file or worktree alone cannot show SparkOps controls a session. The mature path
must establish the writer/ownership relationship and handle already-open sessions,
retries and restart recovery without duplicate execution. Evidence and readiness
return through supported reporting; provider comments hold durable history.

Trace one real SparkOps path through admission, launch, session persistence and result
reporting before choosing adapter interfaces. Existing runtime placement, provider
session mapping, Codex app-server connector, and replay protection are candidates;
their existence alone does not prove an operational end-to-end integration.

Acceptance is one admitted assignment with its relevant context; one continuation of
the correct existing run without duplication; and attributable execution/report
receipts with explicit freshness and uncertainty. Preserve provider neutrality and
the ability to support a different execution consumer.

## Availability and scope

SparkOps loss makes SparkOps execution observations/capabilities unavailable. Project
Intent runtime, persistence, architecture, provider-backed cache and Mission Control
remain independently useful. Project Intent/provider loss leaves workers bounded
orientation from last-known repository snapshots and locally available presence;
snapshots cannot authorize remote PM mutation. Provider credentials stay outside
repositories and product credentials are not inherited.

The present HTTP interface stays read-only. This decision does not implement a
distributed scheduler, automatic dispatcher daemon, infrastructure provisioning,
production credential plane, or public mutation API. Any later command uses the
authority of its owning system, with scope isolation before execution or projection.
