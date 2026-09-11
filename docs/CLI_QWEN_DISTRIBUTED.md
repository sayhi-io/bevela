# Qwen Code · distributed candidate 2 · study v1

Status: **all ten projects completed their predetermined boundaries**. All are
unaccepted, including partial/timed-out projects; none was replaced. See the
[final report](results/qwen-distributed.md) and [v1 measurements](results/qwen-distributed-measurements.json).

This is a new, explicitly user-authorized Qwen stratum. It does not reopen the
completed Sol calibration or reinterpret its stopping rule. Candidate 2's source,
four role tasks, public objective, architecture and fifteen-group checker are
unchanged. No reference implementation is visible to workers. No PI implementation
or production service is changed for this study.

## Frozen comparison

- Five ordinary projects (B) and five PI projects (C), four concurrent native
  Qwen Code workers per project: Catalog, Orders, Settlement and Reporting.
- Exactly the existing component task prompt for each owner in both arms.
  All workers can inspect the complete shared repository and public checker.
- Sequential project order: `B1 C1 C2 B2 B3 C3 C4 B4 B5 C5`.
- Fresh disposable project and native home/session UUID for every worker.
- No evaluator assignments, feedback, repairs, follow-up prompts or model fallback
  after launch. Native CLI tools, including native delegation, remain native
  capabilities; four workers means four top-level processes, not an assertion
  that the CLI cannot create its own subagents.
- A 1,800-second native-process boundary per worker, versus 900 seconds in the
  historical Sol study. This is a separate slower local-model stratum, not a
  matched speed comparison with Sol. Timeouts and failed projects remain evidence.
- Stop the batch on an infrastructure/transport or verified model/control identity
  problem; preserve that run instead of consuming remaining projects on a known
  broken adapter. Ordinary coding failures do not stop subsequent projects.

## Runtime and reasoning

The dedicated SparkOps Twin Plane `qwen-distributed-study` installs Qwen Code
through SparkOps' existing typed tool-install API. It is configured against the
already running local `qwen38-27b-dflash2` service, with thinking enabled and a
230,000-token context. Its installed version is **0.23.2**, the stable npm version
observed on 2026-09-09. No other plane's runtime or active worker is upgraded.

The installed plane is `plane_9fda23887b353d70223403d6` on dgx3. Its managed npm
prefix is:

```text
/var/lib/sparkpyro/digital-twins/twin_planes/plane_9fda23887b353d70223403d6/tooling/npm-global
```

Use that prefix as `--runtime` when freezing a new study, not a legacy checkout's
tool installation. The managed slot is `primary`, backend `sparkpyro_local`,
pointing at the existing local inference endpoint. Installation, configuration and
probe used audited short-lived local operator access; issued tokens were revoked
and were not copied into experiment profiles. The adapter itself requires only a
native runtime prefix and an approved credential-free compatible endpoint.

The experimental adapter snapshots only that plane's installed npm tool prefix,
not its credentials or workspace. Each disposable trial mounts the exact snapshot
read-only and runs its native `qwen` entry point. This follows the existing test
suite's native-process execution model; it is not a claim that these experiment
processes are SparkOps Actions or managed workspace prompt-run receipts. Bevela
imports no SparkOps runtime package.

The serving model reports context length **262,144**, reasoning parser `qwen3`,
and tool parser `qwen3_coder`. It rejects `reasoning_effort: high`, explicitly
accepting `low`, `medium` and `xhigh`. The user's high-effort request therefore maps
to **server `xhigh`**, with `enable_thinking: true`. This is not a Codex-equivalent
effort calibration. Actual request fields and observed reasoning are recorded.

Qwen Code's per-provider configuration sets contextWindowSize=230000,
max_tokens=32768, temperature=0.6, top_p=0.95 and no SDK request retries.
Native automatic compaction remains enabled, with threshold 0.85 and the same
local model. `AGENTS.md` and `QWEN.md` are configured as native context filenames.
Only the PI-specific Codex session identity sentence is adapted to
`QWEN_SESSION_ID`/`--session`; no new task facts or coordination strategy are added.
See the upstream [provider settings](https://github.com/QwenLM/qwen-code/blob/v0.23.2/docs/users/configuration/model-providers.md)
and [context settings](https://github.com/QwenLM/qwen-code/blob/v0.23.2/docs/users/configuration/settings.md).

Operational discrepancy: the lifecycle binding's historical semantic/heartbeat
observations are stale and do not establish present admission or readiness. The
existing model itself responds, the dedicated Twin Plane's native endpoint probe
reports inference ready, and a fresh Qwen Code smoke process produced a real tool
effect with reasoning and usage. The model was not restarted or re-placed. This
study does not relabel the stale lifecycle record as healthy.

All four top-level workers share the same already loaded model service; they are
not four separately reserved model instances. No exclusive GPU reservation is
claimed. Projects do not overlap with each other, but unrelated service load was
not excluded. Sequential execution does not eliminate all temporal effects or
serving variability.

## Isolation and recording

The worker mount namespace contains system tooling, only the current shared
project, its own fresh Qwen home, the frozen runtime and (C only) the frozen PI
source/context. Operator homes, prior projects, observer snapshots, references and
peer transcripts are absent. The network remains available for local inference
and normal CLI tools; this is not hostile-code network containment.

A per-worker loopback relay forwards request and response bytes unchanged. It
records model/effort controls, request timings, returned token usage and whether
reasoning occurred. It does not insert prompts, requirements or messages, change
response content, perform model retries or share context among workers. In-flight
connections are closed when a worker ends. Native stdout, stderr, final records,
session artifacts and tool calls remain separate from that transport observation.

The existing passive 100ms source observer records content-addressed source states.
Post-exit verification uses the observer's frozen checker on an isolated copy,
not a worker-modified checker. Acceptance requires all fifteen groups and required
component-local checks. Native completion and accepted integrated source remain
separate. Protected-input changes invalidate source acceptance.

Report each project’s final integrated score and failures, native completion,
project elapsed time, summed worker time, maximum concurrency and overlap factor,
input/output/reasoning tokens where reported, and cached input as a subset—not an
additional token charge. Missing usage stays explicitly incomplete. Reconstruct
concrete retained work, duplication, integration repairs and PI operations from
native events and source states; do not invent a coordination score.

There is no single-worker Qwen ceiling in this authorized 5+5 comparison. General
coding failures cannot automatically be attributed to concurrency or PI. Any
unchanged/worse PI outcome should state the observed limitation and what a later
test would need to distinguish, without retroactively changing this fixture.

## Run a new version, not the historical cohort

The current adapter/study are **v2**, with recording and sequencing corrections
made only after the ten v1 projects finished. These commands create a new batch;
they must not relabel or overwrite v1 evidence. Historical source is preserved
under `experiments/frozen/qwen-distributed-candidate2-v1/`.

```bash
.venv/bin/python -m unittest tests.test_qwen_code_adapter tests.test_distributed_fixture tests.test_distributed_study -v
.venv/bin/python -m experiments.qwen_distributed_study freeze /absolute/new/batch \
  --runtime /absolute/managed/npm-global \
  --endpoint http://approved-local-model:8078/v1 --model qwen38-27b-dflash2
.venv/bin/python -m experiments.qwen_distributed_study run /absolute/new/batch
```

Freeze stores fixture/checker, prompt, PI, adapter and runtime hashes before any
model project. A resumed batch skips only finalized projects and refuses an
already-started project without a final receipt. No silent retries or replacements.

## Sequencing amendment after B1

B1 hit its predeclared 1,800-second limit with three workers still active. Its
raw receipt retains 4/15 groups, incomplete usage, missing final native records,
and connection resets coincident with the recorder's SIGTERM boundary. The initial
batch guard classified those termination effects as infrastructure failure and
stopped before C1. No project was retried or replaced.

`experiments/qwen_boundary_resume.py` adds an explicit, auditable disposition for
that expected boundary only. It verifies the native model/session and every
request's thinking controls, requires the recorded timeout and expected signal,
rejects HTTP failures and earlier resets, and preserves raw receipts unchanged.
Only then may it advance to the next fresh, already-frozen project. This amendment
changes sequencing, not worker prompts, execution limits, PI, acceptance, or the
frozen native recorder. The batch records its rationale and controller hash.

Native Qwen Code can also emit provider-retry events even with SDK maxRetries=0.
Those native events and response-limit-sized completions are reported; they are
not evaluator retries. Interrupted requests have incomplete usage and cannot be
reported as exact total compute.

## Second sequencing amendment and recorder defect

C1 also stopped the sequencing guard at the same predeclared time boundary.
It retained a chunked-response `IncompleteRead` and native processes without final
records. Sequencing amendment v2 admits that specific exception only under the
same narrow checks: HTTP 200 before the cutoff, error at the termination boundary,
verified initial native session/model and request controls, expected termination
signal, complete recorder stream, and no earlier HTTP/transport failure. Generic
`OSError` and unexplained failures still stop the batch. Neither amendment changes
the frozen worker recorder, source, prompt, budget or acceptance contract.

The shutdown also exposed a recorder bug: closing an upstream HTTP connection from
the main thread while its handler reads a chunked response can raise an unlabeled
`AttributeError` in Python's response cleanup. Diagnostics are preserved, not
classified as a model coding failure. Handler termination remains a prerequisite
for advancing. The recorder stays frozen for this cohort; any cleanup fix must be
versioned for later runs, after all ten projects and their evidence replay finish.

Sequencing pauses are batch setup/inspection overhead, outside worker execution
windows. They are not human repairs to the project, but are reported explicitly
instead of treating this as an uninterrupted ten-project batch.

## Third sequencing amendment: native stream lifetime

C3's Settlement worker emitted Qwen Code's native `StreamLifetimeExceededError`:
its default **900,000ms upstream-wait cap** expired after 8,303 stream chunks.
The native CLI then emitted a retry event and made another request. The relay's
`BrokenPipeError` followed that native cancellation, before the overall project
cutoff. C3 remained a failed partial project and the v2 sequencing guard stopped.

Amendment v3 recognizes only a uniquely corroborated native cancellation: exact
native session/model/envelope, the specific 15-minute cap error, successful prior
HTTP response and recent stream activity, matching native retry, and the exact next
request with a successful response. Overlapping or ambiguously attributable
requests, unrelated errors and HTTP failures remain fenced. Controller and
classifier hashes, native-profile/event hashes and all original failures remain
in separate versioned dispositions. A subsequent HTTP 200 does not prove that
discarded output was recovered or useful work completed.

Neither the native stream cap nor the model's response/context limits were changed.
No evaluator retry occurred. This is an observed Qwen Code/runtime limitation in
this cohort, not evidence that PI caused the interruption. The v1/v2 sequencing
sources and receipts remain archived separately from v3.

## Post-cohort recorder v2 · not applied to these results

After all ten projects and final-checker replays finished, the current recorder
was versioned separately. The v1 public ledger and six exact source snapshots
remain unchanged. New v2 studies freeze their boundary-policy identity before
execution; the current sequencing policy is `qwen-native-boundary/v4`.

- Only the relay handler closes its upstream HTTP response; shutdown signals
  sockets and joins handlers. Unexpected handler/cleanup failures fence
  finalization even if diagnostic writing also fails.
- Native stream EOF and stream-error types are explicit. A successful process
  exit alone cannot certify a complete recorder stream or relay shutdown.
- Usage accepts only nonnegative exact integers, attributable to actual request
  IDs. Missing or malformed fields remain incomplete, not complete zero; cached
  and reasoning coverage are separate. The analyzer/exporter share validation.
- Endpoint validation refuses missing hosts, embedded credentials, queries and
  fragments. The current public export schema is v2; the historical ledger here
  retains its original v1 schema and exporter identity.

These are recording-integrity fixes, not task hints, PI improvements, additional
worker time or rescoring. No v2 model project is included in this report.
Future execution must use a fresh output directory and fresh input hashes.
