# Workstream groups and session observations

The observatory groups cards by the existing Workstream, not by inferred agent.
Title leads, scope/alias/lifecycle are secondary, and declared readiness remains
separate from the worker strip. Classic `/` retains its former presentation as
fallback; `/observatory` uses the sibling worker-groups presentation adapter.

Each icon is an exact `workers[].session` or explicitly bound activity session.
Fresh lease status and recent telemetry remain separate. A finite nonnegative
latest sample within 90 seconds may display reported tok/s only when its telemetry
status/report timestamp are also recent and any associated lease is active/unexpired.
Null samples, future/stale samples, expired/released/ambiguous registrations and
disconnected observation never receive a live-rate number. Zero is a measured zero,
not a missing value. This is output counter delta per reporting interval, not model
generation speed or an agent productivity judgment; there are no speed bands.

Clicking a chip opens exact identity, working declaration, checkout and existing
telemetry history. Previous registrations are collapsed by default. Historical charts
remain in session and full Workstream detail; no history retention behavior changed.
The same exact session appearing in several visible same-scope Workstreams is labeled
Shared with its visible membership count. Rates are never summed or allocated to
Workstreams. Similar strings, common checkout, matching working text and inferred
roles never establish shared identity. Task-specific presence aliases therefore stay
separate unless the read model actually binds them to one session. UI cannot resolve
that identity gap by guessing or attaching parent telemetry to subagents.

No schema, provider fields, worker processes, authority or telemetry transport changed.
App-server investigation is not required to consume current separate-session metrics;
any future app-server attachment needs its own explicit identity/coverage contract.

Keyboard buttons, named native modal, Escape/outside dismissal, focus restoration,
text labels alongside vector icons and mobile wrapping are supported. No animation.
Scope changes clear the panel; failed API refresh marks retained observations unknown.

Validation: five pure Node worker-group tests plus five map tests and82existing Python
tests. Real-data browser probe checks default charts absent, session keyboard detail,
light/dark,390px layout, failed-refresh live badge suppression, scope clearing and
reconnection, alongside the existing Workstream Map checks. Private evidence:
`state/project-intent/reviews/worker-groups-20260906/`.
Owner validation is not independent review, remote CI, a source commit or production
qualification. Prior source-sealed loopback release is retained for rollback.

Independent review found and owner corrected two UI defects: retained history no
longer captions an unavailable rate as current, and Escape restores the current
visible session chip after background refresh replaces the original opener. Reviewer
cleared the corrected source (worker-groups.js SHA256
f811ef62d925fd82295f3dbdf65eab8fd4fccf9a763168e452c5a3a269f629e5).
The real browser probe requires an actual reporting session for the nonempty history
check and asserts both Workstream and session identity on focus restoration.
