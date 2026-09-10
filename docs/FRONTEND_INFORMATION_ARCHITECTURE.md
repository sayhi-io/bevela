# Mission Control frontend information architecture

This contract borrows interaction principles from established planning products,
not their proprietary visuals. One authorized response can support several views,
but each view must expose only the fields needed for its own decision. Scope and
Refresh remain global; presentation settings and coverage qualifications use
progressive disclosure; record detail remains contextual.

## Page jobs

| View | Primary question | Visible information |
| --- | --- | --- |
| Overview | What needs attention now? | An asymmetric command deck: global metrics and current execution dominate; judgment, bounded releases, and convergence stay compact |
| Developers | What activity is currently observed? | Fresh registrations, bounded releases, and latest recorded evidence in three scan lanes |
| Calendar | What dated evidence was recorded? | Compact week or month grid, evidence-type counts, and selected-day records |
| Map | Where do declared boundaries meet? | Boundary index, topology, convergence, and focused boundary detail |
| Work | What work is enrolled? | A dense Workstream inventory with initiatives held in a narrower provider-context rail; execution and lifecycle remain separate |
| Architecture | What must remain true? | A comparison ledger of declarations, states, revisions, statements, and applicability |
| Environments | What substrate is required? | A requirement matrix comparing Workstream, profile, and limitations; never inferred capacity or admission |
| Handoffs | What evidence was handed over? | A chronological worker-report feed with durable provider handoffs in a secondary rail |
| Sources | What was observed and how complete is it? | A repository coverage table with scope/provider freshness and limitations in a diagnostic rail |

Overview summaries must not reappear wholesale on destination pages. In particular,
global metrics and attention are Overview-only; recent releases are summarized on
Overview and analyzed on Developers; convergence is summarized on Overview and
explored on Map; Handoffs contains evidence, not a duplicate activity dashboard.

## Display and disclosure

- Keep scope and Refresh visible because they change or refresh the evidence set.
- On destination views, replace the generic Mission Control masthead with the
  current view's title and purpose instead of repeating that identity again in the
  content column. Overview retains the product masthead.
- Put theme selection behind the Display menu because it changes presentation, not
  evidence.
- Keep short evidence-type counts and the dated-record total in Calendar's global
  connection strip. Put coverage qualifications behind a native details control
  while retaining their full truthful wording.
- Open Workstream/report detail contextually instead of expanding every property in
  the scanning surface.
- Use three columns only for comparable records or lanes that benefit from parallel
  scanning. Collapse to two and one column at narrower widths; do not force a global
  three-column shell.
- Do not use a generic card grid as the default representation. Match shape to
  evidence: lanes for activity, rows for inventory, a ledger for constraints, a
  matrix for requirements, a timeline for reports, and tables for provenance.

## Type scale

The product UI uses a compact hierarchy based on a 14px body:

- page title: 28px / 32px;
- section title: 20px / 24px;
- body and controls: 14px / 20px;
- secondary descriptions and metadata: 12px / 16–18px;
- 10px uppercase labels only for brief eyebrows and evidence-kind labels.

Use relative units where shared foundations permit them, maintain one logical page
heading target, and keep explanatory lines near 60–80 characters where practical.

## Source principles

- [Notion database views](https://www.notion.com/help/views-filters-and-sorts) let
  the same database support multiple locally configured layouts, visible properties,
  filters, sorts, and page-opening modes.
- [Notion layouts](https://www.notion.com/en-gb/help/layouts) bring important
  properties forward and move secondary properties to a details panel; its
  [calendar documentation](https://www.notion.com/help/calendars) includes weekly
  layout selection.
- [Linear custom views](https://linear.app/docs/custom-views) and
  [display options](https://linear.app/docs/display-options) treat views as focused,
  durable subsets with view-local layout, grouping, ordering, and property controls.
- Jira documents view-specific field selection for its
  [list](https://support.atlassian.com/jira-software-cloud/docs/customize-list-view-by-adding-or-removing-fields/)
  and date-backed records for its
  [calendar](https://support.atlassian.com/jira-software-cloud/docs/what-is-the-calendar/).
- [Microsoft Planner](https://support.microsoft.com/en-us/Planner/create-a-plan-in-microsoft-planner)
  gives Grid, Board, Charts, and Calendar distinct consumption jobs.
- [Atlassian typography guidance](https://atlassian.design/foundations/typography/)
  uses a compact product scale, a 14px default body, and 12px sparingly for secondary
  information.
