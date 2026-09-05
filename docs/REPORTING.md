# Supported reporting and provider reconciliation

Workers use the credential-free scope map. From their actual checkout:

```sh
project-intent report --workstream ALIAS-OR-NATIVE-ID --session OWN-SESSION --input report.json --submit
project-intent report-status --workstream ALIAS-OR-NATIVE-ID
```

The report packet has `summary` (required string), optional `readiness` (named string
dimensions), `next_step`, `evidence` (`[{"ref":"path-or-url","sha256":"64 lowercase hex"}]`),
and `assertions` (each `invariant`, `revision`, `subject`). References/hashes are worker
assertions, not independent verification. Never include secrets or transcripts.
Reports are content-addressed immutable payloads; a correction is another report.
Repeated identical submission preserves its identity. Reports never overwrite provider
readiness. `start` and the normalized API expose them separately as `local_reports`.

Without `--submit`, publication is `local`. With it, `pending`. An authorized operator:

```sh
project-intent publish-report --config /private/config.json --scope SCOPE --report-id SHA256
```

The private config must explicitly grant `operator.allowed_scopes`, supply
`operator.journal_directory`, and set each applicable scope's `report_directory`.
Workers' optional `report_directory` defaults to an adjacent directory named after
their enrollment directory plus `-reports`. The service reads the configured directory.
Provider credentials never enter worker reports or the web API. Current deployment is
a cooperative same-user workspace, not credential isolation against hostile local code.

Publication adds a native comment and reports `published`; it does not certify the
claim or alter readiness. Before a network mutation, state becomes `uncertain`.
Retries search all bounded provider activity pages for the exact report marker.
If found, the receipt becomes published. If absent after an ambiguous attempt, no
automatic resend occurs: an operator must reconcile the provider outcome. This prefers
a visible stopped report over duplicate comments. Local file locking serializes this
publisher, not independent remote writers. Local tampered payloads are ignored/refused.

Operator enrollment/reconciliation:

```sh
project-intent provider-list --config /private/config.json --scope SCOPE
project-intent reconcile --config /private/config.json --scope SCOPE --input confirmed.json
project-intent export --config /private/config.json --scope SCOPE --output .project-intent
```

Inventory includes unannotated native issues. A packet contains exact `scope`,
`confirmed: true`, `native_identifier`, `expected_digest` from inventory, and `record`
(the full existing Project Intent metadata contract). Changed metadata requires a new
revision; old completion evidence and conformance assertions must remain. Full prior
metadata is preserved in a native history comment. Never infer user assignment or
native member identity from text similarity.

Explicit creation omits `native_identifier`, includes a meaningful `title`, and uses
the SHA-256 of canonical JSON null as `expected_digest`:
`74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b`.
Check the full native inventory first. Existing alias/title candidates stop duplicate
creation. Native lifecycle starts Todo independently of declared execution/readiness.
Create uncertainty requires operator reconciliation and is journaled before requests.

The provisional provider lacks atomic compare-and-swap. Expected digests detect edits
already visible when the command reads; operators must serialize concurrent native
metadata editing during reconciliation. These commands do not assign native users,
change native lifecycle, provision environments, launch sessions, or expose UI writes.
The SparkOps admitted execution consumer bridge remains deferred.
