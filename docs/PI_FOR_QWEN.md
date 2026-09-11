# PI for Qwen · experiment profiles

A separate research entry point for Qwen Code, not a production PI fork. Toggle
settings between batches without editing PI or cloning a new benchmark for each
combination. Every batch still freezes its exact configuration before execution.

[First completed profile: one Medium, thinking-on, confidence-on PI project](results/qwen-confidence.md)
scored **0/7**, with no timeouts. This route enables controlled experiments; it is
not a demonstrated improvement to Qwen's performance.

[Next profile: one thinking-off, confidence-off PI project](results/qwen-thinking-off.md)
scored **7/7 in 2m 27s**, with zero reported reasoning tokens. One run per profile
does not establish reliability or isolate a causal PI benefit.

[Ordinary thinking-off follow-up](results/qwen-ordinary-thinking-off.md) scored
**0/7 in 44s** with the same frozen fixture, prompts, runtime and model settings.
Both thinking-off conditions now have one project; no repetitions are implied.

[Single-worker diagnostic](results/qwen-single-worker.md): **3/3 accepted**, no PI
or thinking, median **47.9s**. Its [versioned launcher](CLI_QWEN_SINGLE_WORKER.md)
gives one fresh session the existing combined task; it does not change the
two-worker profiles or historical evidence.

[Compact PI startup](results/qwen-compact-pi.md): **1/3 accepted**, scores
**0/7, 0/7, 7/7**, thinking off. The [260-word prompt](../experiments/qwen_compact_pi.md)
replaces the 543-word startup plus mandatory full-document reads in a separate
[versioned route](CLI_QWEN_COMPACT_PI.md). Backend behavior stays unchanged;
shortening instructions did not eliminate discovery/repair workflow loops.

For future compact-prompt runs use `experiments.qwen_compact_pi_v2` with the same
`freeze`/`run` arguments; `freeze --runs 1` freezes exactly one project (default 3).
Its Qwen-only CLI removes the legacy `presence` command
from help/command choices and rejects attempts before any write. Generated
onboarding and refresh commands keep that filtered entry point. The general PI
backend still provides `presence` for other callers. Prompt text stays at 260
words; no additional warning is added. This is a CLI-adapter change, **not** a
backend corruption fix or a tested model-performance improvement. v1 evidence
and its launcher remain untouched. [One completed v2 trial](results/qwen-compact-pi-v2.md)
scored **0/7 in 76s** without loop/timeout: consumer skipped PI and producer left
the now-stale consumer unchanged. No automatic steering was added.

This is a cooperative interface, not a security boundary: backend source remains
inspectable in the disposable runtime. It hides the command from the supported
Qwen workflow, not from an agent deliberately inspecting or invoking backend code.

An independent [steering route](CLI_QWEN_STEERING.md) adds a frozen
`--steering on|off` flag, default off. Native Qwen hooks can deliver PI context and
bounded source-change notices without workers writing manual change summaries.
This is a new worker integration; the passive studies and general backend stay
unchanged. It does not assign repairs, gate completion or resume exited sessions.
[First steering pilot](results/qwen-steering.md): **7/7 in 95s**, both workers
enrolled and the consumer reconciled changed source; 18 notices, no timeout or
loop guard. One run does not establish reliability.

| Switch | Choices | Default |
| --- | --- | --- |
| `--thinking` | `on`, `off` | `on` |
| `--confidence` | `on`, `off` | `on` |
| `--pi` | `on`, `off` | `on` |
| `--effort` | `medium` only | `medium` |
| `--runs` | 1–5 sequential projects | **1** |
| `--context` | 32768–230000 | 230000 |

High/XHigh are rejected. The native generic effort is Medium, or `none` with
thinking disabled; the explicit provider request retains Medium and uses
`chat_template_kwargs.enable_thinking` to switch thinking. Confidence-on with
thinking-off is rejected: this intervention targets repeated deliberation.

Confidence-on appends exactly this sentence to each unchanged role prompt:

> You are very knowledgeable. An expert. Think and respond with confidence.

It is an experimental prompt intervention, not a correctness guarantee. It adds
no task facts, solutions, ownership instructions or evaluator feedback. PI's own
skill, inventory task facts, runtime and original seven-seam checker stay unchanged.

## Run a profile

From the checkout-owned environment, substitute a new disposable evidence directory,
the managed Qwen Code installation prefix, and a freshly resolved model endpoint:

```sh
.venv/bin/python -m experiments.qwen_profiles freeze /absolute/new-batch \
  --runtime /absolute/managed/npm-global --endpoint http://resolved-host:8078/v1 \
  --pi on --thinking on --confidence on --effort medium --runs 1
.venv/bin/python -m experiments.qwen_profiles run /absolute/new-batch
```

For thinking-off, freeze with `--thinking off --confidence off`. For the original
thinking behavior without the phrase, use `--thinking on --confidence off`.
No ordinary run is implicitly paired or scheduled. Each project still has two
concurrent native workers; separate projects never overlap within a batch.

`run` accepts no setting overrides. A changed profile requires a fresh batch.
Results retain the complete `qwen_profile`, per-worker transport/usage and native
receipts, protected source hashes, score and acceptance separately. Failed projects
are not replaced, and uncertain/incomplete transport stops batch progression.

The route instantiates private copies of the existing Python recorder modules and
supplies configuration hooks. It does not change those historical modules' source
or global state. Recorder dependencies, this route, runtime and effective prompts
are hash-bound; the ordinary native Qwen Code loop remains the execution harness.
Filesystem isolation, fresh sessions, native compaction, 30-minute worker deadline,
passive observation and observer-only final acceptance are inherited unchanged.

Configuration freedom is **between** frozen runs, never mid-trial tuning. Compare
each setting explicitly; don't pool different profiles or turn one success into
proof that a prompt trick works. Confidence may change calibration as well as
verbosity, so correctness and reduced repetition must be evaluated separately.
