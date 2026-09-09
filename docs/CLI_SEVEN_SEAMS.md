# Seven-problem native Codex study — v1

Status: fixture and recorder implementation only; no model result is claimed.
This supersedes neither the old microstudy nor its frozen evidence.

## What changes

Two native Codex workers share one disposable checkout and start concurrently.
One migrates seven data representations while preserving public helpers; the other
implements seven customer-facing labels that consume the changing data. There are
seven integration problems, not seven sequential trials or seven workers:

| Problem | Concurrent pressure |
| --- | --- |
| Prices | Integer cents versus dollar totals and labels |
| Stock | On-hand/reserved records versus sellable counts |
| Weights | Integer grams versus kilogram totals and labels |
| Discounts | Basis points versus percentages and discounted dollar prices |
| Delivery | Stored hours versus displayed days |
| Contacts | Structured records versus email strings and named-contact labels |
| Orders | Explicit paid/pending/refunded states versus booleans and status labels |

Discounted prices also depend on the changing price contract: the problems are not
seven statistically independent observations. Each worker receives its own complete
task up front. The shared README describes existing public behavior, not the peer's
future work. PI's scoped inventory contains those actual tasks, so peer intent comes
through PI rather than an extra shared test plan supplied by the recorder.
No mid-run requirement injection, prescribed task order, repair owner,
barrier, test-failure notification, follow-up message or model adjudicator exists.
Workers can naturally inspect code, use existing helpers, add tests and coordinate.
Avoiding a conflict through a sound implementation is a legitimate outcome.

The treatment is the explicitly selected Project Intent code, skill and local task
inventory. No production provider writes, fabricated live registrations or observer
enrollment occur during preparation. Workers enroll themselves during actual runs.
The current local agreement protocol still relies on peers reading context; this
study does not add a hidden messaging or scheduling service to make it work.

## Run only when authorized

From the source worktree with its own .venv:

```bash
.venv/bin/python experiments/seven_seams.py prepare --pi-source /absolute/selected/pi/source
```

Select another explicitly requested model at preparation with `--model MODEL` and
`--effort medium`. These settings are frozen in the plan before workers launch;
the default remains Luna at medium. Model comparisons keep identical task inputs.

Preparation returns a new private temporary directory. It copies exact fixture,
prompts, checker, recorder and selected PI source/skill/docs into that directory,
records hashes, and launches no model. Do not use a path under an unrelated checkout
as the optional parent. The default temporary directory avoids inherited workspace
instructions. No credentials, private service configuration, environments or prior
trial artifacts are copied into the worker checkout or PI source bundle.

For exactly one trial, explicitly run:

```bash
.venv/bin/python /returned/trial/recorder.py run /returned/trial
.venv/bin/python /returned/trial/recorder.py check /returned/trial
```

The invocation remains native Codex exec --json --sandbox workspace-write, model
gpt-5.6-luna, medium effort, with each ordinary task prompt passed directly and the
remaining native configuration/environment inherited. There is no replacement agent
loop or execution timeout. The recorder writes exact argv, native version,
stdout/stderr, process IDs/timing, and literal before/after bytes and modes. A
started marker prevents overwrite/retry. It never starts another trial automatically.
Actual duration and model behavior are unknown until measured; 30 seconds is not
an imposed deadline or a promised runtime.

## Results

The check command refuses unfinished runs. It inventories byte differences first,
then evaluates an isolated copy of completed output against the original contract,
including declared current-data behavior. Cached Python bytecode is excluded from
that verification copy; original bytes remain untouched. It reports each problem's
producer and consumer checks, plus how many preserve both tasks, from 0/7 to 7/7.
Problem-specific failures remain visible rather than becoming one opaque verdict.
The post-run probe has a bounded execution timeout, not a worker deadline. Probe
failure/timeout is an evaluation error, not a model-task success or failure verdict.

Record known-but-deferred breaks, competing repairs, acknowledgment and stale
handoffs separately from functioning output by inspecting actual completed logs.
Claim counts or enrollment success alone do not establish effective coordination.
Process exit zero also does not establish preservation of the seven contracts.

This remains PI-only as requested. The old one-problem control is historical context,
not a matched numerical baseline for this new fixture; do not compare its success
percentage directly with a seven-problem score or claim an A/B win. Runs are not
hermetically read-isolated from the local host and native configuration is inherited.
The recorder does not claim general correctness, security qualification, or a causal
PI benefit. Source changes, merge and shared release activation remain separate.
