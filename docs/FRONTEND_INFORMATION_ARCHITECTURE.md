# Mission Control interface

Mission Control is a read-only project observatory. The layout helps people find
recorded activity, understand current observations and inspect evidence without
turning records into a schedule or a completion claim.

## Design references and decisions

The September 2026 redesign reviewed the current official product interfaces and
documentation of [Linear planning](https://linear.app/features/plan),
[Linear timeline](https://linear.app/docs/timeline),
[Notion calendar views](https://www.notion.com/help/calendars), and
[Notion Calendar](https://www.notion.com/product/calendar).

Linear's narrow workspace navigation, flat record lists, consistent control
placement and separation of project planning from issue implementation inform
the shell and Work inventory. Notion's week/month switching, locally filtered
views and contextual record opening inform Calendar. These are interaction
references; no product screenshots, proprietary artwork or fabricated planning
fields are shipped.

The resulting interface uses one neutral visual system across all nine views:
a labeled workspace sidebar, one page title, a quiet connection/coverage strip,
a restrained terracotta selection accent and content separated by rules.
There is no equal-height card grid or appearance-variant selector.

Typography uses self-hosted Inter 4.1 from the
[Inter project](https://github.com/rsms/inter/tree/v4.1), including its SIL Open
Font License in `project_intent/web/INTER-LICENSE.txt`. The font is served through
the same authenticated static boundary as other assets. There are no external
font requests.

## Page jobs

| View | Primary content |
| --- | --- |
| Overview | Explainable metrics, current observations, four recent releases and a small attention rail |
| Developers | Three flat lanes: observed active registrations, reported inactive registrations and latest recorded evidence |
| Calendar | Date navigation and an activity list, with full evidence in a contextual inspector |
| Map | Declared boundaries, their relationships and scoped details |
| Work | Searchable workstream rows, available session rates, review/merge affordances and initiative context |
| Architecture | Constraint declarations, revisions and applicability in a comparison ledger |
| Environments | Requirement profiles and limitations in a matrix |
| Handoffs | A compact report feed with separate durable provider handoffs |
| Sources | Repository coverage and provider/execution provenance |

## Database-view refinement

An additional whole-site review uses Notion's [views, filters and grouping](https://www.notion.com/help/views-filters-and-sorts)
and [contextual page layouts](https://www.notion.com/help/layouts) as interaction
references. Overview and Calendar retain their distinct jobs; the other views
gain local database controls instead of another dashboard summary.

- Work adds lifecycle filters, title/execution sorting and optional project or
  lifecycle grouping. Provider initiatives move into a disclosure instead of
  consuming a permanently sparse side column. Full workstream data stays searchable.
- Developers adds search before the per-lane display limit and an explicit
  show-more action. The lanes still represent observations, never task stages.
- Handoffs offers worker-report and provider-handoff views, search, report
  publication filtering, date ordering and pagination. Undated provider handoffs
  stay accessible here. Full assertions and source records open in a side inspector.
- Architecture adds search and state filtering, with complete declarations and
  applicable workstream links in the inspector. Environments adds requirement
  search and a limitations filter, using descriptive work titles.
- Map keeps its existing focus controls; its legend and observation caveats are
  consolidated into a disclosure. No data model or relationship is changed.
- Sources separates repository inventory from provider/execution provenance in a
  view selector. Repository search and connection filters surface setup gaps.

The **Set up repository** guide is available only with the existing operator
inventory projection. It lists observed mapping/provider status, explicitly marks
worker-map configuration as unverified, and prepares a shell-quoted read-only
discovery command for the chosen scope and actual checkout. Its operator recipe
contains separately labeled configuration entries, not a complete replacement
configuration. It does not read private configuration, grant access, create provider
projects, write configuration, register workers or enable task creation/local Git.
One-click connection still needs an explicitly authorized backend enrollment flow
with validation, least-privilege access, atomic configuration changes and rollback.
The current read-only HTTP contract has not been expanded; only a static asset
route is added.

A true Gantt was considered and deferred: [Notion timelines](https://www.notion.com/help/timelines)
are plotted from explicit dates/date ranges. This projection supplies evidence
timestamps but no authoritative planned start/end dates or scheduled dependencies.
Neither first/last commits nor registration leases are substituted for a schedule.

Validation for this pass includes record membership/order (not counts alone),
search beyond rendered pages, undated evidence, keyboard focus across polling,
updated same-identity inspectors, unchanged-count announcement suppression,
repository command quoting, scoped failure clearing, and all nine views in both
themes at desktop and mobile widths. No frontend action performs an HTTP write.

Global metrics remain exclusive to Overview. Operational caveats and source
coverage stay accessible through disclosures and the Sources view. Technical
identifiers are secondary to a record's description. Native work references are
preferred where available; full keys remain available in context and search.

## Calendar and evidence

- Week is a seven-day strip; Month provides six Monday-first weeks.
- Each date shows its total dated records and a small type-composition strip.
  The accessible date name retains exact counts by evidence type. These marks
  indicate records, never task duration, utilization or scheduled work.
- The activity range can be Selected day, Visible week/month or All recorded
  dates. Selecting a date returns to Selected day.
- Search covers full summaries, scope, workstream title/statement/native reference,
  session, commit IDs/publication and PR metadata. A short visible preview never
  restricts the search index.
- Type filtering and newest/oldest/type/workstream ordering apply before pagination.
  Forty matching rows render initially. Show more reveals the next forty, and
  filters reset that display limit. Counts describe the complete matching set.
- Row titles contain a bounded first-clause preview; long hashes are shortened only
  in that preview. Opening a row reveals the complete original summary, timestamp,
  project/workstream, exact identifiers, source record and available contextual links.
- The inspector is a keyboard-accessible native dialog. Scope changes clear records,
  pagination and any open inspector synchronously. New scope failures cannot restore
  prior-scope evidence through a search, filter or sort action.
- Empty dates mean no dated evidence in the response, not inactivity. Local-only
  commits, worker assertions, PR observations and explicit inactive registrations
  remain distinct. No project relationship is invented for a local Git commit.

## Geometry and accessibility

Body and row titles use 14px type, controls 12–13px and secondary metadata 11–12px.
The page title is 22px; the date heading is 25px. Long evidence never determines
the height of a scanning row. Detail panels wrap unbroken identifiers.

At narrow widths, navigation becomes a labeled-for-accessibility icon rail and
activity rows stack type/time above their title. The same filters and complete
record details remain available. The optional inspector is the third surface only
when the user opens a record. Light and dark themes use the same geometry and
theme-specific foreground colors; the inactive label has normal text contrast.

Validation covers scoped real data across all views, deterministic week/month
navigation, all-date search, filters/sorts, pagination, full-summary disclosure,
work search, scope failure isolation, metric explainers, light-theme inactive
contrast and mobile containment. Font assets are included in authenticated route
tests and committed-release publication checks.
