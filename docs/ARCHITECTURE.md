# Independent capability, explicit participation

## Ownership and parallel extraction

This repository owns the normalized Project Intent read model, independent runtime,
offline client and Mission Control. No SparkOps/Cloud/Projects/Verify/application
package is imported or called. The original SparkOps prototype is preserved as the
default for its existing consumers. New consumers opt in through this package/API.
Removing the prototype requires separately validated migration, not this tranche.

PM provider = durable organizational intent, lifecycle, assignments, architecture
declarations, comments, evidence references and relationships. It's a Plan is a
provisional adapter, not the product boundary. The `Provider` protocol emits the
existing version-1 snapshot envelope. `SnapshotProvider` is an offline adapter;
unknown adapters fail closed. No replacement PM database or comment system exists.

Project Intent = applicability, revision comparisons, scoped projections, freshness,
attention and semantic convergence. Its cache owns availability of last-known
observations, not an alternate authoritative roadmap. Git owns code/history.
SparkOps or another substrate may contribute execution observations. A requirement
references the owning Environment Catalog; it never allocates an environment.

## Scope and access

Scope IDs are opaque exact strings (`sayhi/sparkops`, `sayhi/project-intent`). The
slash is naming, not permission inheritance. A configured principal receives an
explicit allowlist. Filtering happens before counts, attention, detail, initiatives,
handoffs and convergence. The HTTP boundary performs authentication on every read;
the importable projection also requires explicit allowed scopes. No browser-selected
scope, provider membership, or forwarded header grants authority.

For the first adapter, each registered provider project maps to one scope. Existing
SPARKINT records remain where they were incubated; new platform intent is in SAYINT.
This is a deliberate migration boundary, not a claim that old records changed owners.
An offline snapshot already bound to another scope is refused, not relabeled.

Invariant/precedent applicability defaults to boundary intersection inside its own
scope. Cross-scope applicability requires an explicit provider-stored `applies_to`
entry with target scope and boundary list, AND the reader must be authorized for the
source and target scopes. No global architectural injection by matching seam name.
Product-only readers need their own enrolled constraints or explicit access to the
shared architecture scope. Unknown/ungranted architecture is not inferred.

It's a Plan native initiatives belong to one provider project. Native membership
is preserved; explicit `initiative_refs: [{scope, id}]` in the provider's existing
Project Intent field can relate another scope's Workstream without creating a new
database. Only authorized visible members appear; provider total progress/health is
not reused as a cross-scope metric. The real platform extraction initiative links
PI-MISSION-01 to the old SparkOps-incubated INTENT-DOGFOOD-01. This is a declared
relationship, not automatic cross-product discovery or a scheduling action.

## Semantics retained

Readiness dimensions remain independent and provider-declared. Evidence binds an
invariant revision and source subject. A differing accepted revision means
`reconciliation-required`; historical evidence is retained. `revision-current`
does not mean verified conformance. No architecture score is computed.

Convergence is deterministic same-scope semantic-boundary overlap among declared
active/blocked/ready work, with separately observed approaching leases. It is not
a conflict, lock, ownership grant or integration approval. No lexical cross-scope
convergence is inferred. Explicit integration relationships are separate.

Divergences are only provider-declared proposals or review findings. The observer
does not discover unexplained drift from code. Empty declarations mean unrecorded,
not verified zero divergence. Attention shows explainable conditions, not every
event. Missing evidence becomes attention when implementation is declared complete;
new unfinished work is not flooded with missing-claim warnings.

Presence is an optional scoped cooperative file feed with bounded leases. Invalid,
truncated or unavailable feeds report coverage limitations. No live lease means
unknown worker activity, not proof nobody is working. Environment availability and
occupancy remain unknown: the first adapter supplies requirements, not measurements.

## Deliberately deferred

Public/multi-host deployment, federated identity, delegated remote worker authority,
provider failover, production backup/restore proof, distributed presence transport,
executable environment integration, autonomous dispatch scheduling, architecture
inference and generalized acknowledgments remain deferred. The bounded cooperative
local repair acknowledgment in [repair coordination](REPAIR_COORDINATION.md) selects
one volunteer repairer without changing PM ownership or granting execution authority.
It is not generalized messaging, a filesystem lock, or distributed fencing. The browser has no
mutation endpoints. Authorized local reporting/provider reconciliation and explicit
session continuation are described in REPORTING.md and SESSION_CONNECTOR.md; their
cooperative local-account model is not tenant isolation from hostile local code.
The mature SparkOps execution-consumer bridge remains deferred in
[task 6](SPARKOPS_CONSUMER_BRIDGE.md). UI affordances cannot bypass those boundaries.

## Worker discovery and granular execution scope

Three distinct coordinates remain explicit: product scope, durable workstream, and
session execution checkout. Provider-native identifier and declared member names
are now retained alongside our stable aliases; either identifier can select existing
intent. No alias migration, owner invention, native lifecycle rewrite or provider
mutation is needed for worker discovery. Native lifecycle is exposed separately from
the provisional custom state; normal unannotated PM issues are still outside this
enrolled subset. Discovery is candidate selection, never automatic task assignment.

The worker CLI observes its own Git root, common directory, branch and HEAD with
read-only commands. The server never executes Git or inspects another checkout.
Checkout metadata is a timestamped local observation, not an authenticated host
attestation. Same host/common-directory identifies related local worktrees for
advisory comparison; this does not establish cross-host repository equivalence.
Remote URLs/credentials and code diffs are not collected.

Paths are declared relative files/directories; current semantic seams, approaching
seams, inspect/edit intent and exclusions remain separate. Edit declarations require
paths; unknown legacy granularity is visible. Path overlap is checked only for the
same local repository and lexical directory containment, never by arbitrary matching
filenames across repositories. Same-scope semantic overlap remains useful even with
no pathname overlap. No overlap is a lock, authorization, automatic review finding,
or permission to take over another worktree. The consumer compares only local scope
entries available in its credential-free worker map, not undisclosed global work.

`start` provides the actual checkout, applicable intent and nearby local registrations;
`enroll` publishes the session's selected boundary and reports nearby declared overlap.
`onboard`, `start` and enrollment also return scoped `integration_context`: related
task contracts regardless of enrollment, and applicable last-known worker summaries,
including released/expired observations with explicit status. The read-only refresh
command preserves the selected scope/configuration/checkout. This is a focused
projection of existing records, not code-change detection, verified integration,
automatic notification, a new message store or a completion lock. Workers must
reconcile current affected imports/callers; another checkout is never an edit target
merely because it appears here. Missing presence coverage remains unknown.
Workers must reconcile a different native delegate/reference against the actual user
assignment. Reference paths can be inspection material and never silently become
execution locations. Missing durable enrollment is explicit. The opt-in local
`task-register` capability records already user-assigned work after live native
inventory review; discovery and session enrollment remain read-only/local respectively.
It reuses operator reconciliation with a separate narrow scope/checkout policy,
preserves native owners, and refreshes the shared cache before reporting onboarding
ready. It is not a new PM store, assignment authority, scheduler or HTTP write route.
Existing machine/session registrations remain backward compatible.
