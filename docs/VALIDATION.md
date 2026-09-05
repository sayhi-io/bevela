# Real observatory dogfood evidence

This work is `sayhi/project-intent:PI-MISSION-01`, enrolled in the independent
SAYINT provider project/initiative. It uses existing SparkOps development records,
the real Environment Substrate enrollment, and its own platform assignment. No
fictional Verify/Projects state, architectural amendments, convergence, or findings
were created to populate the interface.

## Source and runtime boundary

Independent repository: `repos/sayhi-project-intent`; implementation worktree:
`worktrees/sayhi-project-intent/mission-control`, branch `agent/mission-control`.
This is new uncommitted source; no remote, source commit, push, merge or public
deployment is claimed. Workspace README/AGENTS and `bin/project-intent` now make
the independent implementation discoverable. The SparkOps prototype code remains
unchanged and usable by its current consumers.

The running local service is `http://127.0.0.1:8290`; all content/API reads require
the independent operator or scoped-reader credential. The PM provider remains a
separate provisional service. New cache, configuration and access material live in
`state/project-intent`, not inside SparkOps, Cloud, Projects, the origin, or their
runtime directories. Only explicitly configured presence feeds touch consumer
paths, read-only; feed loss leaves durable intent usable.

## Checks actually performed

- 20 standard-library tests passed using this checkout's `.venv`. An independent
  reviewer reran all 20 and approved bounded local use after corrections.
- Real live projection included two enrolled scopes, eight workstreams, eighteen
  invariant records and the platform-extraction initiative at the observation
  checkpoint. These counts are observed data, not assertions of complete SayHi
  inventory.
- Browser checked real-state rendering, Workstream detail, environment unknowns,
  scope switching, product-only credential rejection of platform scope, and a
  390px mobile viewport without horizontal overflow or uncaught page errors.
- A separate isolated HTTP instance served the real cached snapshots with provider
  status unavailable and all execution feeds absent. The browser still showed
  work, architecture and handoffs with explicit unavailable/cache labels. No actual
  SparkOps, SayHi application or PM service was stopped.
- Offline CLI orientation and cache reconstruction worked without provider/product
  network access. Snapshot-provider adapter, scope binding, malformed refresh
  preservation, interrupted HTTP reads and scoped aggregates have regression tests.
- JavaScript syntax and Python compilation checks passed. Browser test dependencies
  are not service runtime dependencies; no product environment was borrowed.

Screenshots and browser results are private local evidence under
`/tmp/sayhi-intent-observatory-4agTBJ/`: `mission-control.png`,
`workstream-detail.png`, `mission-control-mobile.png`, `outage-observatory.png`, and
`browser-results.json`. They are not checked in or publicly hosted. This directory
is temporary evidence storage, not a production retention service.

## Real review corrections

Independent review identified malformed input/refresh containment, scope relabeling
on offline refresh, public provenance filtering, presence status/truncation handling,
incomplete initiative paging, out-of-order UI scope responses, and timestamp sorting.
A second pass caught imported architecture freshness, interrupted HTTP-body handling,
and malformed environment-limit rendering. Each was corrected without changing the
original prototype or manufacturing a real provider invariant amendment.

Focused contract tests use isolated malformed/outage inputs where changing the real
provider would be unsafe or misleading. These are regression checks, not another
synthetic workstream lifecycle experiment. Browser outage checks use real snapshots.

## Remaining limits

No actual product outage drill, fleet integration, public access, production backup
restore, managed unattended service activation, cross-host presence, or substrate
availability proof. Provider credentials are outside Git but native privileges need
production qualification. Environment availability/occupancy is always unknown in
this first read adapter. Missing divergence declarations are not a code audit.

Source remains uncommitted and awaits source sealing/normal CI before merge. Platform
production activation is not authorized. Any later broader hosting must retain the
independent authentication, persistence and recovery boundary described in OPERATIONS.
