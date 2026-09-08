# PI live-cutover dependency map — 2026-09-06

Observed current config and running provider source without printing secrets.
20 configured scopes, two local principals (operator, sparkops-reader), separate
provider key files per project. Current service and provider unchanged.

| Input | Current custody | Migration boundary |
|---|---|---|
| Durable snapshots | state/project-intent snapshots under operator workspace | Copy exact scope-bound caches to dedicated state; already proven offline |
| Provider keys | 18 project-coverage token files plus SAYINT/SPARKINT files | Dedicated provider principals/explicit read roles; root-controlled credential inputs |
| Worker enrollments | state/project-intent/enrollments directories | Exact cooperative registration exports, not broad home ACL |
| Presence | PI presence directories and SparkOps .git presence directory | Explicit read-only materialization with freshness/failure semantics |
| Reports | Per-scope enrollment report directories | Exact bounded report exports, preserving attribution and offline distinction |
| Inference observation | Enrollments bind paths under operator .codex/sessions | Export existing normalized usage observations; do not expose transcripts |
| Workspace inventory | Canonical repos under operator home | Narrow repository metadata observation, not source-tree traversal permission |

Live Store.view currently reads raw local enrollment/presence/report inputs and
invokes codex_activity against session files. Copying registrations alone will not
preserve inference coverage. No broad /home or SparkOps state access granted.
No new normalized export adapter implemented by this inspection.

## Provider credential feasibility

Running It's a Plan0.16.0 source has project-role resource/action matrices in
apps/api/src/shared/permissions.ts; owners bypass them. Migration0078 assigns
external agents explicit project roles. This provides a native least-privilege
mechanism to evaluate, not a reason to fork the provider or assume current keys
are read-only. Existing OPERATIONS.md explicitly warns current agent keys may
have broader rights.

Next credential test: separate non-owner external service identity with read-only
work-item/initiative/project-metadata permissions per required project; prove all
adapter GETs succeed and mutation permissions are denied. Do not downgrade worker
or orchestrator identities in place, or reuse operator ownership to claim a
read-only service identity. Current grant matrices and a tested replacement
credential set remain unverified. No provider roles or keys changed this turn.

## Current disposition

PI remains on existing runtime. Dedicated-account offline canary passed; live feed
and native credential positives remain gates. No silent loss of live coverage to
make the hardened candidate appear ready.
