# Opt-in PI steering · Qwen v1

[First pilot result](results/qwen-steering.md): **7/7 in 94.860s**, one project.

Experimental worker integration, not a production PI deployment. The general
backend remains unchanged. Historical passive recorders, task prompts, fixture,
checker and compact instructions remain byte-identical.

```sh
.venv/bin/python -m experiments.qwen_steering freeze /absolute/new-batch \
  --runtime /absolute/verified-qwen-runtime --endpoint http://resolved-host:8078/v1 \
  --steering on --runs 1
.venv/bin/python -m experiments.qwen_steering run /absolute/new-batch
```

`--steering off` is the default. The flag and run count are frozen before launch;
`run` cannot override them. Both settings retain PI and the compact, filtered CLI.
This toggle compares **PI pull-only versus PI with automatic context delivery**,
not PI versus no PI. Same native thinking-off configuration and 230k context.

### Ten-repeat stability cohort

`experiments.qwen_steering_repeat` freezes ten independent one-project batches
before any model launch, then executes them sequentially. Two workers remain
concurrent inside each project. This wrapper changes no worker-facing treatment:
it compares runtime, source, prompts, checker, settings and PI bundle hashes with
the selected pilot. Only the generated steering configuration differs, with each
project's exact fresh checkout/session bindings independently checked.

```sh
.venv/bin/python -m experiments.qwen_steering_repeat freeze /absolute/new-cohort \
  --runtime /absolute/verified-qwen-runtime --endpoint http://resolved-host:8078/v1 \
  --pilot /absolute/pilot-project
.venv/bin/python -m experiments.qwen_steering_repeat run /absolute/new-cohort
```

The cohort refuses replay; failed correctness runs remain in sequence, while an
infrastructure/evaluator failure stops execution without replacing the trial.
Using single-project inner batches preserves the existing steering recorder's
bytes and avoids treating fresh session-binding hashes as changed PI behavior.

## Delivery and observation

The native Qwen Code 0.23.2 `UserPromptSubmit`, `PostToolUse` and
`PostToolUseFailure` command hooks inject `additionalContext`. This is a supported
extension point, not a model-transport rewrite. See the
[official hook contract](https://qwenlm.github.io/qwen-code-docs/en/users/features/hooks/).
The ordinary byte-preserving model relay remains unchanged.

At these boundaries, the hook:

1. Checks the exact configured checkout and native session identity.
2. Reads the session's existing PI `start` projection, without auto-enrollment.
3. Hashes a frozen allowlist of up to 64 existing checkout-root Python files.
4. Emits bounded related-task/worker declarations initially and when those
   declarations change, plus file names whose bytes changed since this session's
   last observation. No manual change summary is needed to detect those changes.
5. Reminds the recipient to inspect changed source/callers and validate integrated
   behavior, preserving scope and existing repair agreement rules.

PI supplies semantic relationships for the declaration context. **File-change
observation is project-scoped, not a new semantic impact analyzer.** It currently
observes all allowlisted source files, including changes made by the receiving
worker. It does not infer authorship, affected symbols, which peer should repair
the change, or whether a change is correct. New files outside the frozen list,
nested components and other checkouts are not monitored by this first adapter.

The backend's declarations remain declarations. Automatic file observations are
separate experimental evidence, not PM comments or worker-authored reports. No
separate agent, reporting model, scheduler, work queue or automatic assignment is
introduced. The integration reads only allowed source and PI context, never the
observer's checker, verdict, reference solution, peer transcripts or tool-response
body. The common task prompt receives no extra solution facts.

## Bounds and failure behavior

- Identical state produces no repeated notice. Heartbeat timestamps are excluded
  from change detection so routine polling does not cause notification loops.
- At most **12 notices per session**, 6,000 characters per notice, 16 changed
  paths per notice, four related tasks and four workers; omission counts remain
  explicit. Task statements are excerpted to 400 characters and worker summaries
  to 240; these are not substitutes for full `start` context. Source reads are
  bounded to 1 MiB per allowlisted file.
- Per-session state is locked across parallel native hooks. Notices and elapsed
  hook time are logged in the worker's isolated home, not source or PM records.
  Emission is not proof the worker understood or followed a notice.
- Hook errors fail open, emit a diagnostic to stderr, and do not block native
  work. Missing hook evidence must not be represented as successful steering.
- No permission approval/denial, tool rewriting, Stop-hook gate, waiting for
  peers, repeated completion request, or automatic resumption of exited workers.
  A worker that finishes before a later change cannot receive that later notice.
- State persistence precedes return: a crash can lose a notice rather than blindly
  resend it. This is bounded cooperative research instrumentation, not a hostile
  multi-tenant boundary or reliable exactly-once message service.

## Validation

Focused tests cover toggle-off, change detection without reporting, duplicate
suppression, declaration refresh, session/checkout fencing, missing/symlink files,
notice budget, immutable trial inputs and actual runtime hook settings.

A separately enabled native integration test runs the **real CLI against a
scripted local provider**, proving both initial context and post-write file-change
notice arrive in native model requests. This test uses no model inference and is
not a benchmark correctness result:

```sh
QWEN_STEERING_TEST_RUNTIME=/absolute/verified-qwen-runtime \
  .venv/bin/python -m unittest tests.test_qwen_steering_native -v
```

Future studies should distinguish improved delivery from correct interpretation,
and record hook cost, emitted/suppressed notices, worker edits, rework, project time
and final acceptance separately. Do not interpret a hook message as authority or
credit an acceptance win to steering without checking the actual worker behavior.
