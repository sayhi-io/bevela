# Provisional local session connector

For additive Codex/Qwen conversation references in ordinary worker enrollment,
see [runtime session identities](RUNTIME_SESSIONS.md). Those references are
separate from the operator attachment and delivery mechanism described here.

This optional CLI adapter lets an authorized local operator attach an existing
Codex session and issue one bounded continuation. It is separate from Mission
Control's read-only HTTP API. It is not the mature SparkOps execution bridge;
admission, runtime placement, credentials and fleet orchestration remain task 6.

The local OS account and a private operator configuration are the authority
boundary. A worker's presence, matching worktree, session UUID, or discovered
assignment alone grants no dispatch authority. The adapter creates no workstream,
lease, delegated provider identity, or permission to change another owner's code.
Only explicitly authorized operators should have access to the connector config
and its state directory. This cooperative same-user boundary is not protection
against a malicious process already running under that same account.

Configuration lives outside Git, owned by the operator with mode 0600:

```json
{
  "operator": "local-operator",
  "authority_ref": "reference to the user's bounded coordination instruction",
  "state_directory": "/private/project-intent/connector-state",
  "allowed_targets": [
    {
      "scope": "sayhi/project-intent",
      "workstream": "PI-MISSION-01",
      "session": "exact-consenting-session-uuid",
      "checkout": "/exact/authorized/worktree"
    }
  ]
}
```

The state directory must be private (0700). The allowlist is exact: scope,
canonical alias, UUID and resolved Git checkout. Attachment additionally pins
host and common Git directory. The selected rollout is explicit; only its first
session metadata line is read and its UUID/checkout must match. A historical
session created from another directory requires the allowlist's explicit
`session_origin_cwd` alongside its designated `checkout`. Both facts are retained;
queueing does not change the target process directory. The continuation names the
designated checkout so the worker can orient there. No broad transcript scan occurs.
Attachments expire after one hour and must be explicitly renewed by reattachment.

After `discover` and `start`, the operator uses:

```bash
project-intent session-attach --scope SCOPE --workstream ID \
  --session UUID --checkout /exact/worktree \
  --connector-config /private/connector.json --rollout /explicit/rollout.jsonl

project-intent session-continue --scope SCOPE --workstream ID \
  --session UUID --checkout /exact/worktree \
  --connector-config /private/connector.json \
  --request-id stable-request-id --message-file /private/continuation.txt \
  --delivery queue
```

The CLI resolves existing enrolled intent before dispatch and includes last-known
assignment revision, scope, exclusions, acceptance, boundary/claim and environment
fields. Workers still run `start` for current applicable architecture and freshness;
the continuation envelope is not a complete refreshed architecture slice.

`queue` is the default for an already open thread. The installed local Codex
command must emit a receipt naming exactly that target. `queued` means accepted
delivery, not observed execution or completion. Unknown CLI output, missing
capability, transport failure and timeout are explicit. No session is automatically
resumed merely because queue delivery succeeded.

`--delivery resume` explicitly runs noninteractive `codex exec resume` for a known
dormant session, using existing local Codex configuration. It does not override
sandbox or approval flags. Do not resume your own active thread or a thread with
an existing writer. A completed exact-session turn can be observed; task acceptance,
tests, readiness and production authority still require their own evidence.
Resume is bounded to 300 seconds; timeout is uncertain, not proof the work did
nothing. Child execution may already have produced side effects or child processes.
Inspect the target before any further continuation. No automatic queue/resume
fallback or retry occurs. This is deliberately not a background job supervisor.

Each request ID is durable local operational state. It records a digest before
delivery, so a crash after sending cannot silently trigger resending. Reusing the
same ID/content returns the receipt without invoking Codex; changing its target or
message is rejected. An uncertain receipt remains uncertain on retry. New IDs must
not be used to bypass uncertainty without checking the target. State stores digests,
target, authority reference and delivery metadata, not message bodies or transcripts.

Subagents may inherit `CODEX_THREAD_ID` from a parent process. They must use a
distinct explicit presence-only enrollment identity unless their own Codex UUID is
independently established. Never attach parent telemetry merely from that variable.

Reference: [Codex noninteractive mode](https://developers.openai.com/codex/noninteractive).
The local `codex queue --help` is the implementation-specific capability evidence;
queue support is not assumed portable to all Codex installations. The subprocess
backend is replaceable through the `Backend` protocol; no Codex dependency enters
the provider, normalized read model, or HTTP service.
