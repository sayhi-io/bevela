# Common browser acceptance interface

Supply this document and the shared product contract unchanged to every owner
and successor before launch. These selectors describe public UI semantics only.

- Native selects have accessible names `Incident component` and `Incident state`.
  Their all-values option has value `""`; other values match the public API.
- History rows live in `#incidents`; each row has `data-incident-id` equal to its
  public incident ID. This container holds history rows, not summary cards.
- Buttons have accessible names `Load more` and `Retry` when applicable.
- A persistent `#historyStatus` live region (`role="status"` or `aria-live="polite"`)
  announces loading, result counts, empty results, and errors. Its visible text
  includes `loading`, `no incidents` (or `no results`), and `error`, `failed`, or
  `unable` for those states respectively. Wording otherwise remains free.
- Page URLs use `component` and `state` query parameters, omitting all-values.
  Changing a filter creates a browser history entry. Navigation restores controls
  and the first matching page. A new filter selection clears obsolete rows/cursor.
- Filters and buttons retain focus when their results refresh. Native controls
  remain operable at a 375px viewport without document horizontal overflow.

The disposable server imports the candidate worker and candidate migrations with
an in-memory SQLite D1-shaped adapter. It never runs scheduled checks. Its 67
incidents span two components, both states, and tied timestamps. A third canonical
component has no incidents. The inert literal `<b data-history-marker="inert">`
in one summary tests text rendering without executable content.

Browser routing holds genuine local API responses to exercise reordered responses,
and injects a single network failure for retry. All other traffic uses the worker;
non-loopback traffic is blocked. No private cursor encoding is assumed.

Run from the study checkout (Node 22+):

```sh
.venv/bin/python -m pip install playwright==1.55.0
TRIAL_CHECKOUT=/absolute/disposable/candidate \
  .venv/bin/python experiments/incident_history_browser.py
```

The runner uses the installed Chromium headless shell under
`/home/meanaverage/sayhi/state/project-intent/browser-test`; override its exact
executable with `BROWSER_EXECUTABLE` if needed and record that change for both arms.
It launches and terminates its own loopback server on an ephemeral port.
