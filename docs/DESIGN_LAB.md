# Mission Control design lab

Presentation-only variants selected by `?design=plan`, `?design=studio`, or
`?design=console` on `/observatory` or `/workstream-map`. Unknown values and no
flag retain the current design. The header selector updates the URL and preserves
the current hash/view. Theme selection remains independent. The normalized API,
authorization, live-presence meaning, provider truth and reports are unchanged.

- Plan: dense list rows, labeled sidebar, neutral surfaces, right-side detail.
- Studio: warm editorial gallery, horizontal navigation, spacious tiles.
- Console: cool compact operational panels and monospace metadata.

Plan takes conceptual direction from It's a Plan's `DESIGN.md` (local inspected
v0.16.0 source and upstream https://github.com/croffasia/itsaplan/blob/main/DESIGN.md):
borderless-first layouts, neutral surfaces, typographic hierarchy and calm density.
No provider UI source, branding, assets or runtime code is copied or required.
This is an original Mission Control presentation, not an It's a Plan fork.

## Visual identity

`identity-facts.js` deterministically derives a mirrored 5×5 geometric mark from
the exact JSON pair `[scope_id, workstream.id]`. Title, lifecycle, array position,
presence and telemetry do not affect it. Cards, Workstream details, report history
and Workstream Map reuse the mark. Renaming an alias/ID changes the mark; an explicit
future identity migration would need to address that. Marks and colors can collide:
they are visual aids, not unique IDs, fingerprints or security verification.

Inline local SVG, no remote avatar requests or persisted visual metadata. Visible
names remain the accessible identity; redundant SVG marks are aria-hidden.
No initials, person silhouettes, status-dependent avatar colors or animation.

## Boundaries

Existing default remains the fallback. Files are sibling presentation adapters;
`design-lab.js` accepts only three exact flag values. The API never receives the
design flag. Native links, keyboard disclosures, scope filtering, map selection,
report provenance and readiness distinctions remain the existing mechanisms.
No new actions, dispatch, fields, provider states or inference sources.
