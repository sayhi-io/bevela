# Developers Board and work calendar

Mission Control exposes two complementary read-only activity views over the same
already-authorized observatory response.

The **Developers Board** answers “what is happening now?” without creating a task
queue. Working now contains only fresh active registrations at the projection's
observation time. Recently released uses the explicitly bounded recent-inactive
feed. Latest recorded evidence selects the newest timestamped local worker report
or provider handoff for each Workstream. A report does not itself establish
delivery, and provider lifecycle alone never makes a card look active.

The **Calendar** answers “what recorded evidence exists for this date?” Its default
week view provides a compact seven-day scan; the month control switches to a
Monday-first six-week range without changing the evidence set. The date grid sits
above the selected-day evidence so a short calendar cannot leave an artificial empty
column beside a long evidence list. Selected-day records use responsive cards that
form additional columns only when the available width and record count make them
useful. It indexes
provider handoff timestamps, local worker-report creation timestamps, bounded recent
inactive-registration timestamps, usable enrolled pull-request observation timestamps,
and optionally observed local Git commit timestamps. PR entries describe when a PR
state was observed, not when Git-provider lifecycle transitions necessarily occurred.
Commit entries use Git committer time, not inferred work duration. Dates use the
browser's named local time zone. An empty date means no dated evidence exists in the
currently authorized, selected response; it does not mean nobody worked. The calendar
does not index the 15-minute process-local throughput history or live provider data
not already included in the scoped API.

Local Git evidence is an explicit operator opt-in. It is read only from named immediate
repositories under one configured absolute root after principal scope filtering. The
observer reads local branch and remote-tracking refs without fetching. It exports the
repository name, full object ID, committer timestamp, bounded subject, and a conservative
`local-only`, `remote-tracking`, or `unknown` publication label. It does not export local
paths, author names/emails, branch names, bodies, diffs, tags, or remote credentials.
Several commits may relate to one Workstream, but the calendar leaves them at repository
scope instead of inventing Workstream attribution.

Neither view is a Gantt chart. Project Intent does not currently expose authoritative
planned start/end dates or dependency schedules, so drawing duration bars would
invent planning semantics. A future Gantt view requires those fields to be explicit
provider-owned intent with their own scope and freshness contract.

Both views preserve scope filtering because they derive only from the response that
the server has already authorized. Changing scope clears the rendered views before
the replacement request completes so retained data from another scope cannot remain
visible after a failed fetch.

Mission Control's global metrics and attention entry point belong only to Overview.
The recent-release feed and convergence preview also remain Overview summaries;
Handoffs owns durable reports and provider handoffs, while Map owns the full boundary
projection. This prevents activity views from repeating the same dashboard blocks
under different navigation labels. The complete page-purpose and disclosure contract
is recorded in `FRONTEND_INFORMATION_ARCHITECTURE.md`.
