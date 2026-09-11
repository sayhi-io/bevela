# Qwen steering · distributed candidate 2

One fresh pilot, four native Qwen Code workers: Catalog, Orders, Settlement and
Reporting. This is the **15-group distributed candidate 2**, not either seven-seam
fixture. PI and native steering are on; thinking and confidence phrase are off.
Qwen Code 0.23.2, `qwen38-27b-dflash2`, 230k context, native compaction, 1,800-second
worker limit. There are no retries, successors or post-launch evaluator messages.

```sh
.venv/bin/python -m experiments.qwen_distributed_steering freeze /absolute/new-project \
  --runtime /absolute/verified-qwen-runtime --endpoint http://resolved-host:8078/v1
.venv/bin/python -m experiments.qwen_distributed_steering run /absolute/new-project
```

The four role prompts, objective, architecture, starting component source and
public acceptance checker are unchanged. All ordinary execution instructions are
retained, with the same compact PI template and filtered Qwen CLI used in the
seven-seam steering study. No backend implementation is modified or activated.
Local fixture inventory still derives exclusively from its public tasks and
architecture. Historical inputs/results remain untouched.

## Adapter difference

The original steering hook supports checkout-root files. This version uses a small
separate path reader for nested component files, with directory-descriptor traversal
and no-follow opens to reject symlink escape. Its frozen allowlist contains the
12 existing component Python/CONTRACT.md files. It does not read acceptance.py,
evaluator results, reference implementations, transcripts or tool-response bodies.
New files outside that list are not observed.

All remaining hook behavior is reused unchanged: native prompt/post-tool hooks,
PI context refresh, deduplication, 12 notices per session, 6,000 characters per
notice, no permission changes, no repair assignment, no stop gate or automatic
resumption. A hook can observe a worker's own edits; it does not infer authorship
or semantic impact. Delivery is not proof of attention. Nested-file support is a
new **research adapter version**, not a change to the earlier frozen hook.

## Evidence and interpretation

Freeze checks preserve task/checker bytes, PI source, adapter source, runtime,
settings and exact session bindings. Preflight checks isolated native version and
fresh worker homes. Four processes launch through the existing distributed
recorder; 100ms source observation and native transcripts capture work without
feeding evaluations back to workers. Final verification occurs after worker exit.

`result.json` distinguishes source acceptance from autonomous completion (correct
native identities/controls, successful workers, complete recording, no transport
errors). Failed, timed-out and partial results remain. Per-worker transport usage,
durations, source history and steering journals remain local.

This pilot is not a matched steering-only A/B: the historical distributed Qwen
cohort used thinking/XHigh and long instructions. Differences in outcome cannot
be attributed solely to steering. A follow-up would keep this thinking-off profile
fixed and vary only steering if needed; none is queued automatically.

## Explicit 500-call follow-up

`experiments.qwen_distributed_cap500` runs one fresh project using the same
candidate, prompts, compact PI, nested steering, runtime and 30-minute boundary.
Its only worker-facing setting change is `model.maxToolCallsPerTurn: 500`.
This replaces the native adaptive default with an explicit hard cap; other native
guards remain unchanged. It does not resume or repair the earlier checkout.

```sh
.venv/bin/python -m experiments.qwen_distributed_cap500 freeze /absolute/new-cap500-project \
  --runtime /absolute/verified-qwen-runtime --endpoint http://resolved-host:8078/v1
.venv/bin/python -m experiments.qwen_distributed_cap500 run /absolute/new-cap500-project
```

The versioned wrapper leaves the original recorder and hook bytes intact, freezes
the cap, rejects settings drift/replay, and checks each worker's actual native
settings. Tests compare the two settings objects (only the cap differs), fixture,
checker, tasks, instructions and static PI bundle. Fresh generated checkout/session
bindings differ as expected. The cap does not guarantee completion: repetition
guards, the time limit, coding errors and integration defects remain possible.

### Session-turn follow-up

`experiments.qwen_distributed_turn500` uses the same `freeze`/`run` commands and
fresh-project semantics. Relative to cap500 it changes only `model.maxSessionTurns`
from 150 to 500, keeping `maxToolCallsPerTurn: 500` and the 1,800-second boundary.
PI, steering, thinking-off controls, runtime, prompts, source and acceptance stay
unchanged. The wrapper freezes and verifies both limits; historical runs are not
resumed, edited or replaced. This removes another observed cutoff, not a promise
of 15/15 correctness. Only one new project is authorized by this follow-up.
