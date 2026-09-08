# Workstream Map — projection experiment

Status: owner-validated prototype, not deployed or independently reviewed.
Assignment: sayhi/project-intent:PI-MAP-01 / SAYINT-14.
Source base: f57251e38e59744abe820dbecba4e5817aea81ad, canonical main.

## Boundary

An additive `/observatory#map` view consumes the same authenticated
`GET /api/v1/observatory?scope=…` result as the conventional observatory.
No new API response fields, provider metadata types, lifecycle states, worker
processes, coordination semantics, execution behavior or durable layout were added.
The real experiment enrollment uses the existing Workstream contract. Its exported
snapshot is retained with private evidence, not substituted for the checked-in cache.

Native SVG and ordinary DOM provide a deterministic scope-separated grid, not a
force graph. Size, position, ordinal labels and curves carry no priority, distance,
health, ownership, ordering or architectural-strength meaning. No ambient motion.
No browser dispatch actions. The classic page and all conventional views remain.

## Inventory and visual grammar

These are exact fields from `project_intent/model.py:project`, not a new contract.

| Existing normalized fact | Projection / interpretation |
| --- | --- |
| `scopes[].id,label,source.captured_at,provider_status,execution.status` | Separate scope regions, source labels; selected API scope controls access, not client layout |
| `workstreams[].key,scope_id,title,statement,id` | One soft bounded surface; title/ID and full context on selection |
| `workstreams[].state` | Literal lifecycle label; default includes active/blocked/ready, optional other states |
| `workstreams[].provider_lifecycle` | Separate provider label in seam detail; not live execution |
| `workstreams[].boundaries[]` | Solid-outlined numbered perimeter ports and full-text boundary index |
| `workers[].status,heartbeat_at,expires_at` | Fresh lease count only when active and unexpired, and heartbeat not future; API disconnect suppresses live markers |
| `workers[].touching_seams[]` | Filled inner marker at matching port; fresh declaration, not detected edit |
| `workers[].approaching[]` | Hollow dashed inner marker at matching port; not a lock or physical movement |
| Worker-only touching/approaching boundary | Dashed perimeter port, explicitly distinguished from durable Workstream boundary |
| `workers[].session,working,checkout` | Seam inspector shows actual declaration and checkout; conventional detail retains paths, exclusions and branch/HEAD |
| `convergence[].scope,boundary,workstreams,meaning` | Undirected band ONLY for the selected server-projected convergence group; no invented overlaps or cross-scope links |
| `architecture[].key,kind,statement,revision,state,boundaries,workstreams` | Inspectable invariant/precedent only when exact boundary matches AND API-computed Workstream applicability intersects visible members |
| `workstreams[].claims[].invariant,status,architecture_revision,evidence_revision,subject,verification` | Literal revision/evidence comparison under the applicable invariant; current declaration does not prove conformance; stale does not mean failed |
| `workstreams[].readiness,completion_evidence,handoff_summary,local_reports,report_coverage` | Workstream-level expandable evidence and reports; not seam adjudication |
| `workstreams[].divergences,divergence_coverage` | Existing declarations shown verbatim in Workstream context; no proposal rendered as a violation |
| `workstreams[].integration_dependency` | Literal declared text; no guessed graph edge from alias-looking prose |
| `workstreams[].pull_requests[].relationship,url` | Workstream-to-PR reference, explicitly not Workstream-to-Workstream dependency |
| `initiatives[].workstreams` | Explicit membership shown as membership, not integration success |
| `attention[].scope,workstream,kind,message` | Existing attention rows in inspector; surface count opens the normal attention list |

Transient `workstream-map-facts.js` indexes only reference these records. Same text
in different scopes yields different boundary selections. Worker-only ports do not
create a new normalized convergence group. Backend `approaching_sessions` is not
blindly attached to every member: markers require that Workstream's own worker.

## Navigation and accessibility

Three bounded modes: authorized scope overview; selected Workstream; selected
boundary surfaces plus a detail dialog. No infinite zoom, no drag editor. Only one
convergence group is connected at a time to avoid an all-edges hairball. Stable
lexical ordering keeps repeated observations understandable. Index ordinals are local
navigation aids and may change with filters; they are not stable semantic IDs.

DOM boundary buttons and SVG center/port buttons support Tab, Enter and Space.
Ports have full boundary accessible names and tooltips. Dialog has a named heading,
native modal focus behavior, close button and Escape. Encodings differ by outline,
fill and text, not hue alone. Motion is absent, with reduced-motion overrides.
Mobile uses a stacked bounded-scroll index and one-column surfaces. Up to twelve
ports appear per surface; remaining boundaries stay in the index and full context.
Conventional detail remains the precision/fallback surface.

## Real dogfood observation and evidence

Owner probe used the real configured provider and observation feeds, with copied
caches and a temporary authenticated loopback server serving this checkout. It did
not restart, deploy or alter the running Mission Control/SparkOps services. No fake
records or worker movement were used in browser evidence.

Private evidence directory:
`/home/meanaverage/sayhi/state/project-intent/reviews/workstream-map-20260906/`.
`observation.json` records the exact API result; `checks.json` lists rendered keys.
Screenshots: `sparkops-ha-dark.png`, `sparkops-ha-light.png`,
`sparkops-ha-mobile.png`, `boundary-detail.png`, `platform-all-lifecycles.png`.

Twenty Workstreams were available: ten Project Intent and ten SparkOps. Default
SparkOps view rendered DEV-CLI-CI-01, DEV-FRONTEND-CI-01, DEV-MCP-COMPAT-01,
ENV-SUBSTRATE-01, HA-HEALTH-GATE-01, HA-MIGRATION-GATE-01, INTENT-DOGFOOD-01,
MODEL-ONBOARDING-01, SPIRE-HA-01 and SPIRE-INTEGRATION-01.
Selecting `spire/ha-authority` isolated the two HA gate assessments and SPIRE-HA-01,
with two undirected segments representing their one normalized convergence group.
The inspector exposed seven applicable HA invariants and their claim comparisons.
There were no fresh SparkOps leases, so no SparkOps approaching markers were shown.
The experiment owner's genuine Project Intent lease was available in its own scope.
No signer/runner/connector records were invented from historical conversations.

Validation:

- 82 existing Python tests passed, including authentication and scope isolation.
- Five new Node tests cover lease expiry, touching/approaching distinction, outage,
  scope separation, no invented convergence, applicability and input immutability.
- Real browser probe passed dark/light, 390px no horizontal overflow, keyboard seam
  inspection/Escape, selected HA convergence, retained-state disconnection, removal
  of live markers, clearing on scope change, reconnect and other-lifecycle inclusion.
- No browser JavaScript errors. Screenshots inspected by the implementation owner.
- CI workflow now runs the Node tests; actual remote CI has not run for this branch.

Run unit gates with `.venv/bin/python -m unittest discover -s tests -q` and
`node --test tests/workstream-map.test.cjs`. The optional real browser probe is
`tests/map_browser_probe.py`; its documented environment variables point to private
config/access/output paths. Playwright is owner-only tooling, not a runtime dependency.

## Projection limitations and product implications

| Limitation / missing fact | Why it cannot be derived; decision |
| --- | --- |
| Seam-level coordination outcome / “mended” | Reports and handoffs lack a reliable seam/outcome binding. Show them at Workstream level; no stitches or reconciled state |
| Typed inter-Workstream dependency/integration edge | `integration_dependency` is text, PR relationship means PR linkage, initiative means grouping. Keep distinct literal detail; no guessed arrows |
| Seam-bound divergence | Divergence records do not guarantee a normalized boundary association. Expose Workstream proposal/findings, never infer their seam |
| Architectural truth from revision match | `revision-current` compares declarations, not implementation proof. Display verification caveat; no success glow or score |
| Worker-only convergence | Existing normalized convergence uses Workstream boundaries, not all presence-only ports. Show worker declarations without manufacturing convergence |
| Unobserved work or missing evidence | Enrolled subset and cooperative feeds do not cover every agent/repository. Explicit unknown coverage; no inferred inactivity or failure |
| Many boundaries or long titles | First twelve ports, text index, filtered focus and full conventional context; no extra provider visual fields |

These are expressiveness limits, not established requirements to change the model.
No model fixes were made. Future product work, if justified by real use, would need
an independent decision about durable relationship semantics rather than visual demand.

## Acceptance assessment / recommendation

Current data supports a useful scoped Workstream/seam view without schema changes.
It shows actual semantic convergence and inspectable architecture. Fresh worker
touching/approaching encoding is unit-tested, but a real concurrent approaching
episode did not occur during this observation and was not manufactured. Dependency,
integration and divergence are distinguishable as literal existing details, not
invented edge types. Unknown state stays unknown. Twenty enrolled Workstreams are
manageable with scope/focus filters; this is not evidence for unlimited scale.

**Iterate.** Retain this optional experiment for operator feedback. Faster human
recognition has not been measured in a comparative usability test; attractive
screenshots do not prove that claim. Independent review, source commit, actual CI
and deployment remain separate from owner validation. No production authorization.
