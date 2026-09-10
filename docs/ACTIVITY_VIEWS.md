# Developers Board and work calendar

Mission Control exposes two complementary read-only activity views over the same
already-authorized observatory response.

The **Developers Board** answers “what is happening now?” without creating a task
queue. Working now contains only fresh active registrations at the projection's
observation time. Recently released uses the explicitly bounded recent-inactive
feed. Latest recorded evidence selects the newest timestamped local worker report
or provider handoff for each Workstream. A report does not itself establish
delivery, and provider lifecycle alone never makes a card look active.

The **Calendar** answers “what recorded evidence exists for this date?” It indexes
provider handoff timestamps, local worker-report creation timestamps, and bounded
recent inactive-registration timestamps. Dates use the browser's named local time
zone. An empty date means no dated evidence exists in the currently authorized,
selected response; it does not mean nobody worked. The calendar does not index the
15-minute process-local throughput history, source-control commits, or live provider
data not already included in the scoped API.

Neither view is a Gantt chart. Project Intent does not currently expose authoritative
planned start/end dates or dependency schedules, so drawing duration bars would
invent planning semantics. A future Gantt view requires those fields to be explicit
provider-owned intent with their own scope and freshness contract.

Both views preserve scope filtering because they derive only from the response that
the server has already authorized. Changing scope clears the rendered views before
the replacement request completes so retained data from another scope cannot remain
visible after a failed fetch.
