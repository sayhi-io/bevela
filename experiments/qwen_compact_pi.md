# Project Intent

Shared context, not authority or a lock. Honor your task's scope/exclusions; peer
assignments aren't ownership walls. Work in this checkout.

Define this helper in each shell call that uses PI:
```sh
pi() { python3 -B -I ../pi-source/project_intent/_worker_cli.py --worker-config .pi/worker.json --scope {{SCOPE}} "$@"; }
```

1. **Find:** `pi onboard --query "task keywords"`. Inspect acceptance/exclusions;
   choose the actual task, not merely a text match. If unmatched, `pi discover`
   without a query; inspect scoped inventory before authorized `task-register`.
   Never invent an assignment. Use `pi docs`/`--help` for missing syntax; search
   only checkout/returned docs, not private state or other sessions.
2. **Enroll before editing:** `pi onboard --workstream ID`, then
   `pi enroll --workstream ID --session "$QWEN_SESSION_ID" --access edit --touching-path FILE --touching-seam SEAM --working "bounded change"`.
   Repeat path/seam flags as needed; declare approaching/avoided areas. Renew your
   own enrollment if already active. Paths are files, not seam names.
3. **Reconcile:** read `integration_context.related_work`, even without active
   peers. Refresh with `pi start --workstream ID`; inspect current affected source.
   Update `--working` with changed symbols/fields/units and replacements.
4. **Competing repair:** consult `pi docs`' repair guidance; claim bounded paths,
   obtain the named peer's acknowledgment, then only the agreed repairer edits.
   Sharing a seam alone needs no claim; unrelated work stays free.
5. **Finish:** refresh; inspect changed imports/callers and released-peer summaries;
   validate both sides together. Don't leave a known regression for another role.
   Unverified/pending integration is not complete. Release your enrollment using
   `--inactive --working "result, checks, remaining work"`; report durable evidence
   when needed. Missing tracking is explicit, not success or permission to bypass
   admission. No need to wait for unrelated work.
