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
Measured overview chips now show the current value on the left and a thin curved
sparkline in the same 32px-high row, stopping before the session-history button.
Each curve uses only that exact session's existing 15-minute samples, never a
Workstream total. The zero-based vertical scale adapts to the visible peak; curves
are for within-session trends, not cross-session magnitude comparisons. There are
no axes, fills, markers or animation. Missing/invalid values, lease boundaries and
gaps over 120 seconds break the line; a single sample shows its value without
inventing a curve. Unmeasured/disconnected observations retain explicit text.
The first active session (reporting first, then present, with exact ID ordering)
gets the strip's width. Other active sessions are counted on the history button
and remain individually inspectable there, avoiding overlapping labels or
zero-width curves on narrow cards. The shown value is not their combined rate.
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

Original validation: five pure Node worker-group tests plus five map tests and82existing Python
tests. The original real-data browser probe checked full-size charts absent, session keyboard detail,
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

## Compact sparkline validation

`node --test tests/worker-groups.test.cjs` covers exact session rates and curved
path generation, including explicit gaps, invalid samples, zeros and bounded
smoothing. The credential-free deterministic browser probe serves checkout assets
and an explicitly synthetic API fixture without contacting a service:

```sh
# Optional checkout-owned Playwright installation: see docs/OPERATIONS.md.
BROWSER_EXECUTABLE=/path/to/headless_shell .venv/bin/python \
  tests/throughput_sparkline_browser.py --output /private/evidence/sparklines
```

It checks 320/390/800/1440px layouts in both themes, exact-session inspection,
keyboard focus restoration, overflow-session history, and unavailable/zero states.
The probe disables GPU and software-GPU startup; SVG/CSS use CPU page rendering.
This avoids a DGX headless compositor stall without bypassing normal browser
actionability checks. It adds no application animation or runtime dependency.
Fixture screenshots are layout evidence, not observations of worker performance.
