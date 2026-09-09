# Native Codex: concurrent seam microtest

> Historical source recovery. Historical one-seam protocol and calibration summary, superseded for new seven-problem work by CLI_SEVEN_SEAMS.md. These pilots are not a matched baseline for later fixtures.
>
> Status and authorization statements below describe their original writing;
> they are not current launch permission or new validation claims. See
> [Results](../RESULTS.md) for the maintained result index. Archive references
> identify private evidence, not public downloads; no raw artifacts are included.
> This sanitized documentation copy is not a replacement for a historical sealed
> input. Original frozen source and evidence remain unchanged in their archives.

This replaces Study03 as the proposed test of PI's practical value. The old
release studies and evidence remain historical, not evidence for this design.

Question: does PI help ordinary concurrent Codex agents accommodate one another's
code/data changes on shared or related architectural surfaces?

## Two tiny tasks, one changing surface

The fixture is 19 lines of Python plus a short README. Each condition has
one shared disposable checkout and two ordinary Codex sessions:

- Change catalog prices from dollar floats to integer cents, preserving checkout totals.
- Add the dollar price to the existing receipt label function.

The changed consumer and the data migration meet at the money representation surface.
They need not edit the same file to affect one another. Neither prompt tells its
worker about the other task or supplies a coordination procedure. Existing code
and normal Codex behavior determine how the workers proceed. There is no planted
wrong solution, forced stale read, scheduled mutation or designated winner.

Both conditions get byte-identical product inputs and per-task prompts. Control
is simply native `codex exec --json --sandbox workspace-write` with Luna/medium.
That is the native edit-enabled sandbox; other installed user configuration,
environment and tools are unchanged. The second condition
adds PI setup and a normal onboarding instruction in its AGENTS.md. The real
installed PI CLI provides its scoped task inventory and semantic convergence;
workers—not the recorder—declare their actual paths, touched/approaching seams,
working context and release state. Both task records share `shop/money`; their
specific `shop/prices` and `shop/receipt` surfaces remain distinct.

PI's initial inventory contains the two assigned tasks, not fabricated claims of
worker activity or prewritten warnings/solutions. There are no observer-driven
updates during execution. This uses PI's supported local snapshot/live presence
path, not provider publication or enrollment on the production Mission Control map.

## Recorder, not another agent harness

`experiments/seam_microstudy.py` only prepares directories, starts the native
processes, records their bytes and timing, and copies the resulting files after
both writers exit. No custom model loop, forced phases, worker replacement,
shared coordination notes, revision broadcast, prescribed checkpoints, integrator,
correction rounds, mandatory commits, output schema, reviewer or coaching.

The recorder does not disable ordinary Codex behavior: an agent may naturally
inspect, test, plan or delegate. The run inherits user configuration and installed
skills. In particular, if control independently uses PI, that is contamination to
report, not a reason to secretly suppress native capabilities or call it a clean
no-PI run. Separate condition directories are not a security sandbox; this is a
local cooperative comparison, not proof that cross-condition access was impossible.
Use a temporary directory outside a workspace with mandatory PI instructions.

Target: **approximately 30 seconds for a concurrent pair of conditions**, not a
30-second kill switch. Two short changes keep task size small; model/service latency
and native verification can still overrun. There is no forced stop, retry or silent
exclusion of slow runs. Live timing must establish the target; it is not guaranteed.
No context-window/compaction override, stripped Codex home or custom sandbox is used.
The initial launch pilot inherited read-only exec defaults and could not edit;
its unchanged artifacts are not an effectiveness result. Both conditions now
explicitly select native workspace-write, with no elevated permissions.

## Run

From this checkout, using its environment:

```bash
.venv/bin/python -m experiments.seam_microstudy prepare
# Prints a fresh private directory, e.g. /tmp/pi-seam-EXAMPLE.
.venv/bin/python -m experiments.seam_microstudy run /tmp/pi-seam-EXAMPLE
.venv/bin/python -m experiments.seam_microstudy diff /tmp/pi-seam-EXAMPLE
```

`run --arm control` supports an ordinary-control timing check. `--model`,
`--effort` and `--codex` are explicit options, not automatic substitutions.
Runs never overwrite a started condition. Do not reuse a pilot as a scored result
after changing its inputs. Preparation does not call a model or access credentials.

Native JSONL output is documented in [Codex non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode#make-output-machine-readable).

## Evidence and interpretation

Per worker: exact command/prompt, unmodified stdout JSONL and stderr bytes, process
exit code, UTC timestamps and monotonic start/end/elapsed time. Per condition:
wall time, process-overlap interval, complete before/after file copies (excluding
Git internals), byte lengths/hashes/modes and symlink targets. Uncommitted and
untracked files are retained. The shared final tree belongs to the condition;
it is not falsely attributed to one of its concurrent writers.

`diff` lists exact changed/added/deleted files, explicitly labeling PI setup
artifacts without hiding them. Byte differences are not automatically material.
First inspect product differences. If behavior is materially equivalent, no
separate shared-correctness adjudication is needed for this comparison. Otherwise
examine the differing seam behavior against each original task—not a new contract
invented by a reviewer. A normal process exit is not an acceptance verdict.

Process overlap alone does not establish that the vulnerable read/write windows
overlapped. The native logs must show what happened. No observed seam interaction,
unused PI, a control that used PI, failed model transport, or unobserved settings
must remain explicit limitations; never relabel them PI success/failure. Setup and
post-run diff time are outside worker wall time. PI onboarding during the task is
inside it. Four processes are started without waiting on outcomes; actual startup
skew and shared service load remain part of the observed timings.

## First native pilots — 2026-09-08

The three private archive IDs below identify calibration observations,
not public raw-artifact downloads. They are
not independent repetitions of one unchanged task. The original temporary paths
remain in commands and PI inventory as provenance; archived inventories must not
be used to relaunch workers against those paths.

- `20260908-seam-micro-readonly-pilot`: launch defect; native exec inherited
  read-only permissions. Neither condition could edit. Excluded from effectiveness
  interpretation, not hidden or retried in place.
- `20260908-seam-micro-render-pilot`: edit-enabled, larger full-receipt task.
  Control 59.592 seconds; PI 132.632 seconds. This motivated shrinking the receipt
  task to the existing label function, not changing native worker behavior.
- `20260908-seam-micro-label-pilot`: current tiny task. Control 46.418 seconds;
  PI 70.617 seconds. The 30-second target is **not yet met**.

In the label pilot, the control price worker finished in 46.418 seconds and its
receipt worker in 40.648 seconds. PI price took 70.617 seconds and PI receipt
43.358 seconds. Both conditions had real overlapping process lifetimes.

The final product diff has two files: `catalog.py` differs only by a comment;
`receipt.py` materially differs because control divides cents by 100 before
formatting and PI does not. `checkout.py` and `test_checkout.py` are identical.
Direct read-only invocation of the preserved output confirms:

| Output | Control | PI |
| --- | --- | --- |
| Stored prices | tea 1250, cake 725 | tea 1250, cake 725 |
| Checkout total | 19.75 | 19.75 |
| Tea receipt label | tea: $12.50 | tea: $1250.00 |
| Cake receipt label | cake: $7.25 | cake: $725.00 |

The native logs record the control price worker fixing the receipt after its tests
exposed the representation change. The PI price worker also detected the receipt
failure, but left it unresolved because it regarded receipt as the other
workstream's responsibility. Its final message expected that workstream to fix it;
the preserved final tree did not contain such a fix. This is an observed failure
to complete the cross-surface adjustment, not evidence that PI failed to surface
the relationship, nor a general causal claim from one pair. No corrective messages
or candidate repairs were sent. Both PI workers eventually released their presence.

Raw logs, per-worker timings, and original/final file bytes remain in each archive.
PI setup/presence and Python bytecode differences are retained too, separately
from the product-source comparison. No independent shared-correctness review ran.
