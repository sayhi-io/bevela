# Runtime conversation references

PI enrollment has always used `CODEX_THREAD_ID` as its `session` key when invoked
with `--codex`. A runner or Qwen worker can instead use an independent PI session
key. Registrations and scoped read projections now carry an optional
`runtime_session` reference to distinguish these identities:

```json
{
  "session": "runner-example",
  "runtime_session": {
    "runtime": "codex",
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "host": "worker-host",
    "instance": "local-codex"
  }
}
```

`runtime` is `codex` or `qwen-code`; `id` is the exact native thread/session ID.
`host` is captured from the enrolling checkout's local host. The optional
`instance` is an opaque local registry name distinguishing app servers or daemons
on that host. It contains no URL, socket path, token or credential. A future
transport adapter must resolve it through its own trusted configuration and check
the actual target. Omitted instance means unspecified, not the default app server.
IDs are references declared by the enrolling worker, not authenticated identities,
proof of current reachability, or delivery/continuation authorization.

## Enrollment

Existing `enroll ... --codex` now records the Codex reference automatically while
retaining the existing own-session telemetry behavior. For an independent PI
runner ID, add the runtime reference explicitly, without connecting telemetry:

```sh
project-intent enroll --scope SCOPE --workstream TASK --session RUNNER_ID \
  --runtime codex --runtime-session EXACT_THREAD_ID \
  --access inspect --working 'Review the assigned contract'

project-intent enroll --scope SCOPE --workstream TASK --session RUNNER_ID \
  --runtime qwen-code --runtime-session EXACT_QWEN_SESSION_ID \
  --runtime-instance local-qwen --access inspect --working 'Review the assigned contract'
```

Workers performing edits supply their usual `--access edit --touching-path` flags.
The runner may attach the reference after it learns the native ID; subsequent
renewals and release preserve it when the flags are omitted. A different runtime,
conversation, host or instance requires a separate PI session, including after
expiry/release. This preserves attribution of the old session. An existing unknown
reference may be supplied once. Runtime IDs do not replace the PI session key used
by reports, repairs and leases.

Registrations without references remain valid. Existing Codex telemetry metadata
plus a known checkout host projects an unambiguous legacy reference without reading
a transcript. A UUID-shaped PI session alone is insufficient to infer Codex.
Non-Codex workers and subagents must not adopt an inherited `CODEX_THREAD_ID` as
their own conversation identity.

The reference is included in enrollment receipts, scoped observatory sessions,
discovery, nearby workers and last-known integration context. Expired/inactive
workers retain the reference together with their existing freshness/status fields.
Consumers must not interpret a historical reference as a live destination.

## Qwen equivalence

Qwen Code exposes native session IDs and explicit resume options in its
[Python SDK](https://qwenlm.github.io/qwen-code-docs/en/developers/sdk-python/).
Record the ID supplied by that runtime. The model name, a Qwen HTTP inference
endpoint, a channel name and a PI runner ID do not establish a Qwen Code session.
For raw model calls or a harness without a native conversation handle, leave the
reference absent. This change neither discovers Qwen sessions nor implements
Qwen delivery, continuation, capabilities, or daemon activation.

## Delivery and MVP boundary

Codex's [SDK](https://learn.chatgpt.com/docs/codex-sdk) and
[app-server](https://learn.chatgpt.com/docs/app-server) expose programmable threads.
The September 2026 SDK addition of `ExternalMessage` supplies a way to deliver
external context without granting user authority. This is distinct from the
host-specific `codex_tui.send_message_to_thread` tool and from PI's existing
provisional subprocess connector. No introduction date or backend implementation
for that exact host tool is established by the SDK release note.

Adding the reference does not implement transport routing, durable message receipts,
acknowledgments, scheduling or HTTP writes. Those belong in a separately bounded
adapter, with request identity and delivery/acknowledgment/outcome kept distinct.
The existing `session-continue` connector is unchanged and still uses its explicit
operator allowlist. Its `session` argument remains the native Codex target ID,
not a PI runner alias; it does not resolve this new reference automatically.

### Historical MVP inspection (2026-09-10)

The following records the inspection at that time, not current bridge or deployment
status. Subsequent adapter work must be assessed using its own evidence.

Inspection on 2026-09-10 of the standalone bridge and the SparkOps SPARKINT-35
candidate found a concrete remaining integration gap: the bridge's execution client
still selects `/api/development-actions/codex`; the new SparkOps contract requires
`POST /api/actions/requests`, requester-bound lookup by `request_id`, and the
bounded consumer receipt by server-generated `action_id`. Native coding profiles
and the consumer schema must replace the prototype request/admission assumptions.

A focused first execution MVP is one authorized ChatGPT request producing one fresh
SparkOps coding Job, a bounded patch/summary, and a recoverable requester-scoped
receipt linked to PI work. The inspected candidate supports fresh execution only
and exports no resumable provider session (`provider_session_id` is null); do not
invent a Codex reference for that result. Identity support for existing workers
and the fresh-job launch path can progress separately.

Remaining proof before calling that MVP ready:

1. Reconcile the bridge client and fixtures with the new Actions contract.
2. Review/integrate the native candidate and establish the restricted execution
   profile, eligible worker and authenticated MCP route.
3. Validate the actual isolated container/provider path. The supplied SparkOps
   handoff reports simulated Docker responses and no real provider canary.
4. Run one ChatGPT-to-Job canary, including lost-response recovery, and observe
   the resulting receipt and PI evidence.

Source tests, deployment and an actual ChatGPT invocation are separate evidence.
Live peer messaging alone does not establish readiness of this execution path.
