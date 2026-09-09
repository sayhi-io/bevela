# Seven seams: identical-objective self-organization, v4

New study; does not replace the predefined producer/consumer concurrency study or
its evidence. User overrides: **original seven-seam fixture, Luna medium**, not
refund torture or Luna low. Three repetitions each of A single ordinary, B three
ordinary, C three PI, D single PI: twelve projects, twenty-four native sessions.
Only one project at a time; B/C workers start together, without an edit barrier.
Primary A/B/C complete before secondary D. Prespecified order A1 B1 C1 C2 A2 B2
B3 C3 A3 D1 D2 D3. No replacements or retries; ten-minute worker boundary.

## Frozen inputs and fairness

`experiments/seven_seams_self_organizing.py` reuses the original fixture bytes,
both complete original task texts, checker, passive source observer and scoring.
Every worker receives exactly its `PROMPT` constant, the user's umbrella prompt;
no worker number, ownership, seam allocation or ordering is added. The unchanged
task texts appear together in OBJECTIVE.md, with no worker-role headings.
The single PI inventory record PROJECT covers that same complete objective and
seven boundaries. Stock source-backed PI skill/template and operational docs only;
no previous experiment documentation, tests or results in the PI bundle.
Frozen PI commit: e384223962c55bbb7b4742f7cbced7bf1ae72f94. No PI changes mid-study.

The only arm difference is PI availability/instructions and worker count.
Ordinary Git, shell, current source, existing tests, docs and freely created
file-based coordination remain available. All arms begin with a committed fixture
so ordinary Git diff works. All can invoke the identical unchanged acceptance.py;
the observer scores a separate frozen checker against an archived final checkout.
These two setup improvements distinguish this version from the previous study,
which had an unborn Git repository and observer-only checker: do not pool results.
No worker steering, evaluator feedback, reassignment, intervention or repair agent.
Workers may themselves check, communicate through project files/PI and repair.

Each process runs native Codex 0.153.4 with gpt-5.6-luna, medium, inside one external
mount/PID sandbox. Native internal sandbox is set to danger-full-access with approval
never because the outer sandbox enforces the actual filesystem boundary: writable
trial checkout, private native profile and temporary directory; system/PI/auth mounts
read-only. This changes permission presentation equally in every arm, not task facts.
Fresh native profile with default service tier and trusted trial Git root; unrelated
global plugins, memories and instructions are absent equally in every arm.
Prepared v1 and v2 were rejected before inference: nested bubblewrap could not launch,
and legacy Landlock passed a read probe but could not enforce the current workspace
write profile. V3 uses only the outer sandbox and preflights real native file writes.
V3's first launch exposed an omitted DNS symlink target. It was explicitly aborted
before any observed coding output; native session and failed source are preserved,
not counted as a model-performance trial or silently replaced. V4 also mounts the
resolved DNS configuration read-only and verifies name resolution before launching.
This infrastructure correction does not alter PI or the problem. Report the aborted
v3 launch separately, including observer intervention, elapsed time and missing usage.
Native profile separation follows the documented user configuration boundary:
[Codex configuration](https://developers.openai.com/codex/config-basic).
Linux mount/PID namespaces expose system tools, own native profile, shared trial
checkout and optional read-only frozen PI bundle, not old sessions/evidence or peer
transcripts. The existing authentication file is mounted read-only, never copied
into evidence. Network remains available for native inference; this is artifact
isolation, not a hostile-code/network security claim. CLI invocation, profile hashes,
source hashes, model/effort context and session IDs are retained.

## Preflight and execution

Before inference: focused and full unittest suites, unchanged source/checker hashes,
isolation checks with real shell/Git/tests/CLI, stock PROJECT onboarding read-only,
and independent implementation review. Freeze recorder and imported modules,
fixture/task/checker, PI bundle, protocol, launch order, profile and prompt hashes.
Exclusive start markers prevent rerunning a project/batch. A recorder error stops
the batch rather than starting a trial with unknown previous live-worker state.

## Endpoints and analysis rules (fixed before execution)

- Final score 0–7; each seam requires both original producer and consumer checks.
  Acceptance requires 7/7 plus all native processes exiting normally; retain all
  failures/timeouts and exact failing checks. Check whether completion claims precede
  a demonstrated failure; do not equate an early true pass with final durable success.
- Primary project time: first actual native launch through final post-exit frozen
  verification. Setup, worker interval, archival, verification separately. In-session
  repair is inside execution, classified from logs, not added again. No external repair.
- Earlier native acceptance calls and sampled time-to-first/durable accepted source
  are secondary post-hoc endpoints. Sampling every 100 ms is not an atomic journal;
  no claim of exact first possible correctness or perfect write attribution.
- Per-worker and aggregate native input/cache/output/reasoning, total tokens, duration,
  tool calls and intervals. Cached input/reasoning are subsets; last cumulative usage,
  never sum cumulative samples. Missing telemetry remains missing, not zero.
- Concurrency = aggregate worker-active seconds / project worker interval; include
  peak, start skew, actual intervals. Temporal overlap alone is not useful decomposition.
- Reconstruct first attempted work, successful retained edits, scope switches, explicit
  ownership and unowned work from actual actions/statements. Useful decomposition:
  different retained implementation contributions during overlapping active intervals;
  label ambiguous/simultaneous writes unknown. Time-to-decomposition is the earliest
  observed evidence of this, not a fabricated internal decision time.
- Count duplicate implementation episodes separately from duplicate inspection,
  stale failed patches, overwrite/revert cycles and integration repairs. No invented
  token-to-edit allocation, duplicate-work ratio or subjective coordination score.
- PI overhead: observed command invocations/groups, failures, enroll/release, refresh,
  paths/seams, repair operations; pair native call timestamps for wrapped tool time.
  Mixed calls/context cannot isolate exact PI tokens; report bytes and attribution limits.
- Main unit is accepted project: compare time and compute among equal accepted
  outcomes; failed work is not a cheaper correct project. Three observations/arm
  establish exploratory tendencies, not significance or broad model claims.

Report arm median table, all runs, per-worker telemetry, measured timelines and
concrete allocation/rework audit; address context versus concurrent organization
with D as secondary context comparison. No production activation, release, or PI
implementation changes are authorized by this study.

## Completed local study, 2026-09-09

Public evidence summary: [all runs, telemetry and timelines](results/self-organizing.md).
Raw archive ID: `20260909-seven-seams-self-organizing-luna-medium-v4`; raw native
streams and private runtime records remain outside Git.
All four arms reached 7/7 in all three repetitions. No multi-worker trial produced
an implementation split: one worker supplied the entire migration in every run.
Ordinary concurrent workers had six discarded full-project patches; PI workers
had five. First verified accepted-result medians were A 43.7s, B 41.3s, C 63.2s,
D 63.2s; final quiescent project medians were 53.4s, 72.3s, 101.7s, 86.1s.
The small ordinary first-pass difference has overlapping ranges and is redundant
racing, not evidence of useful decomposition. PI added context/coordination cost
without an accepted-result or productive-concurrency advantage in this sample.
Earlier rejected preparations and one 99.125s infrastructure-aborted launch remain
preserved separately; see the report before interpreting or reusing these results.

Run the batch CLI as a script so its frozen imports resolve independently:

```bash
.venv/bin/python experiments/self_organizing_batch.py prepare \
  --batch /absolute/new-evidence-directory \
  --source /absolute/task-source-checkout \
  --pi-source /absolute/frozen-pi-source
.venv/bin/python /absolute/new-evidence-directory/code/experiments/self_organizing_batch.py run \
  --batch /absolute/new-evidence-directory
```

Preparation never performs model inference. Execution starts the prespecified
twelve projects once; it is not authorized merely by reading these examples.
