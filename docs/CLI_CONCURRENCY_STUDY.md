# Seven-seam concurrency versus context — v2

Completed: [results, all runs and measured timelines](results/concurrency.md).
See [all results](../RESULTS.md) for the newer self-organizing study and backend versions.

Prespecified bounded study: Luna (`gpt-5.6-luna`), **medium** effort as corrected
by the user. Exactly three fresh projects per condition, 12 projects / 18 native
sessions. The original seven-seam fixture, prompts, checker, examples and dynamic
acceptance checks are byte-identical. This is NOT the refund/migration fixture.
No Project Intent implementation changes, live activation or historical rewrites.

| Arm | Execution | Project Intent |
| --- | --- | --- |
| A | One session receives verbatim producer + consumer tasks | None |
| B | Two concurrent sessions, original producer / consumer prompts | None |
| C | Same two concurrent sessions and prompts | Frozen merged source + stock skill |
| D | Same single session and combined prompt as A | Same frozen PI; one combined assignment |

All checkouts contain both exact task texts in `tasks/`, with the same plain
AGENTS pointer. This deliberately equalizes factual availability: unlike historical
trials, future peer requirements are not discoverable only through PI. No requirement
is rewritten, no repair hint added, no order or ownership wall prescribed. A/D get
only the wrapper “Complete both tasks below in this session.” before both tasks.
C/D add the existing supported skill/template, local snapshot and presence/report
configuration. Only operational documents are bundled: architecture, operations,
read model, reporting, registration, session connector and repair coordination.
No prior evaluation protocols/results are included. Snapshot requirements are exact
prompt text, not evaluator facts. v1 preparation was rejected before any model launch
because the inherited full docs bundle contained historical evaluation material.
Both recorder modules are source-hash-bound per trial as well as in the batch seal.
The stock seven architectural labels remain PI indexing metadata, not new facts.
PI still makes context more salient, so this is not a pure dynamic-presence ablation.

Use one project at a time, rotating condition positions over repetitions:
`A1 B1 C1 D1 / C2 D2 A2 B2 / D3 C3 B3 A3`.
This avoids load from other benchmark projects. Within B/C both workers start
immediately through the existing native command; no artificial barrier, handoff,
scripted check, follow-up or forced repairer. Shared account/server load, cache
effects and wall-time drift remain limitations; report observed cached input.
Three repetitions are exploratory, not a stable population estimate.

Bound each native session at 600 seconds; terminate that process group only on
timeout and retain all evidence. No replacement or silent retry. No second model
stratum in this bounded study. Each repetition has a new disposable Git checkout
and fresh native sessions. No prior logs, solution, hidden checker or result is
supplied in its work directory or PI bundle. Native configuration is inherited;
this is not hardened host read isolation. Audit actual evidence access afterward.

## Measurements

- Setup: checkout, prompt copying and PI preparation, reported separately.
- Execution: first process launch timestamp through final process exit; never sum
  process durations for project wall time. Native process wall time includes tool
  waits, I/O and model latency, not just inference. Report active-worker timeline,
  aggregate worker seconds, peak workers, and aggregate/window concurrency factor.
- Final verification: after all workers exit, archive bytes and score a disposable
  copy with the unchanged checker. First *verified final* acceptance is this endpoint;
  do not claim an earlier transient passing state. Failed endpoints are not accepted
  completion times. Archive and verification durations are separately recorded.
- Integration/repair: spontaneous worker activity remains inside execution, not a
  separate evaluator phase. Identify observed intervals from completed logs, label
  mixed/unattributable time rather than invent a precise repair duration. External
  repair time and human interventions are zero by design.
- Compute: last native cumulative token counter per worker (not a sum of cumulative
  samples), input, cached input, output, reasoning output if available. Reasoning is
  a subset of output and cached input is a subset of input: do not double-count.
- Byte history: passive source snapshots on changes, sampled every 100ms and at
  file-change events. Content-addressed versions plus exact stdout/stderr and
  timestamped events stay outside work. This is not an atomic edit journal.
- Useful concurrency: inspect which workers produced retained, accepted changes
  while both were active; process overlap alone is insufficient. Count concrete
  overlapping edits, repeated replacements, fixes of stale assumptions, duplicated
  discovery, dropped work and obsolete tests only with log/source evidence. Same
  file touched twice is not itself duplicated work or a defect.
- PI overhead: count actual onboarding, enrollment, refresh and repair operations;
  retain failed commands. Tool start/end intervals measure command wall time, not
  all coordination reasoning. Report PI document/output bytes where attributable;
  exact PI-only tokens cannot be separated from mixed model requests unless native
  telemetry explicitly supplies that attribution. Never invent a token split.

Interpret per project, by condition. Report median termination times for all runs
alongside success-only times, individual failures and raw costs. A/D helps identify
PI effect without concurrency; B/C compares ordinary versus PI concurrent work with
equal available task facts. No guaranteed identification of context versus dynamic
coordination: inspect behavior and state when findings cannot separate them.

Native JSON events and turn usage follow the [official noninteractive Codex
interface](https://learn.chatgpt.com/docs/non-interactive-mode); verify actual local
session model, effort and counters rather than assuming documentation covers aliases.

Run from this checkout's `.venv` with `python -m experiments.concurrency_study`.
`prepare` and `run` are separate; a started marker forbids rerunning a project.
Model launches require passing fixture and recorder tests and a frozen input seal.
Raw evidence remains outside Git under versioned workspace state. Curated public
summaries and allowlisted measurements are tracked in `docs/results/`.
