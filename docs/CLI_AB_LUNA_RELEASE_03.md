# Study 03 Luna release: preregistered CLI A/B protocol

> Historical source recovery. Historical v1 preregistration, superseded for execution by the v2 addendum and later native-seam studies. The v1 scored attempt was invalidated; see CLI_AB_LUNA_RELEASE_03_STATUS.md.
>
> Status and authorization statements below describe their original writing;
> they are not current launch permission or new validation claims. See
> [Results](../RESULTS.md) for the maintained result index. Archive references
> identify private evidence, not public downloads; no raw artifacts are included.
> This sanitized documentation copy is not a replacement for a historical sealed
> input. Original frozen source and evidence remain unchanged in their archives.

Status at writing: protocol prepared for the parent's remaining freeze and unit
checks. This document is the preregistered protocol, not a mutable execution
record; it contains no candidate result, efficacy claim, acceptance result, or
claim that the study has launched. Live execution outcomes belong in the runtime
`results.json` at
`archive:20260908-luna-release-03/results.json`.
No candidate workers have launched at writing.
The companion product contract is
[`experiments/LUNA_RELEASE_CONTRACT.md`](../experiments/LUNA_RELEASE_CONTRACT.md);
the current preparation runner is
[`experiments/luna_release_study.py`](../experiments/luna_release_study.py).
The current repository source is uncommitted and has not been deployed; only
future disposable source exports are eligible for evaluation.

## 1. Question and estimand

The study asks whether adding narrowly scoped Project Intent context and
coordination records changes the effort and quality of a matched, multi-owner
release exercise, while holding the task facts, source, tools, model, time
limits, concurrency, acceptance tests, and review policy constant.

The primary estimand is the between-condition difference in total measured
effort to an independently accepted integrated delivery, including declared
setup/enrollment overhead, owner work, revision work, integration, correction
rounds, and evaluator administration. An unfinished or failed arm remains an
observed outcome; it is not replaced, repaired silently, or converted to a
success. If neither arm reaches acceptance, the pair is informative about
failure and procedure feasibility but does not yield a positive productivity
claim.

This is a bounded two-pair experiment on one inherited incident-history feature.
It cannot establish general Project Intent superiority, a causal effect across
tasks, or a percentage improvement. Any later report must preserve the
distinction between preparation evidence, rehearsal evidence, and scored
results.

## 2. Fixed source and task

Every arm receives source-only disposable clones of the same two repositories:

* Status starts from accepted Study 02 A-control integration commit
  `782f969409079d743f6b43fb562df79b76b7d21a`.
* The separate support-tools repository starts from its help-only export CLI
  scaffold, with package metadata, no prior implementation, no remote, and no
  earlier transcript.

The release request, acceptance files, ordinary notes, role boundaries,
revision schedule, and exclusions are copied identically. Status storage, API,
and browser are separate worktrees of the Status repository. Export is a
separate worktree of the support-tools repository. No candidate receives the
canonical checkout, a previous trial arm, an unrelated worktree, provider
credentials, or another arm's transcripts/artifacts.

The full product contract is visible to both conditions from the beginning,
including the scheduled revision-2 rule. Initial workers implement revision 1
only, but they are not kept unaware that revision 2 will be activated at the
fixed checkpoint. It requires:

* legacy API compatibility and an opt-in `history-v2` snapshot response;
* immutable matching/public values and ordering for an unexpired snapshot;
* opaque cursor and snapshot validation, filter binding, retention, and truthful
  `410 history_snapshot_expired` behavior;
* the browser's accessible filters, URL/navigation state, refresh, loading,
  empty, error, race, and duplicate-load behavior;
* a separate JSONL export client that resumes through a checkpoint, never
  duplicates accepted pages, retries transient failures in a bounded way, and
  never silently restarts on expiry;
* regression, API, browser, and export validation plus detailed source-bound
  handoffs.

Revision 1 is the initial implementation stage with the configured retention
default of 30 minutes. The already-disclosed scheduled revision 2 changes
retention to 10 minutes and applies the shorter effective expiry retroactively
to already-issued snapshots; it may not extend any earlier expiry. All other
requirements remain fixed. Revision-1 evidence does not establish revision-2
acceptance.

## 3. Conditions and information boundary

There are two conditions:

* **Control:** ordinary Luna medium CLI workers receive the full frozen
  repository documents, including the complete contract and disclosed
  scheduled revision 2, source, role assignment, peer checkout references,
  notes, tools, acceptance suite, and time budget. They do not receive Project
  Intent context, live scope maps, or another arm's records.
* **PI-aware:** otherwise matched Luna medium workers receive exactly the same
  full material and, in addition, the scoped Project Intent orientation and
  communication/reporting channel for their own arm. The PI channel is an
  information and coordination aid, not an execution authority, permission
  grant, scheduler, or hidden requirements channel.

The aware condition may create or update its explicitly scoped live PI records
through the authorized preparation/run path. Those records are retained as
operational provenance only. The arm's analysis input is an offline copied
snapshot and local report bundle, with the scope, capture time, revision, and
freshness stated. It must not query live provider state during outcome analysis.
There is no per-arm PI reporting quota; a quota failure is not to be invented.
An uncertain native write is an operational failure requiring reconciliation,
not a successful enrollment and not a candidate-quality result.

Both conditions have the same ordinary notes directory and the same opportunity
to read peer notes. Aware workers may use only their own arm's scoped PI
context. No task-specific coaching, stronger model, private precedent, hidden
review finding, or cross-arm relay is permitted. Missing PI/provider context is
reported separately from product defects and from model failure.

## 4. Owners, stages, and fixed concurrency

Each arm has four concurrent initial owners:

1. `storage`: snapshot persistence, migrations, `src/state.mjs`, storage tests;
2. `api`: `src/worker.mjs`, API integration/validation, and API tests; it
   coordinates against the storage interface and does not edit storage-owned
   files;
3. `browser`: `src/ui.mjs`, `src/history-browser.mjs`, browser modules/tests;
4. `export`: the support-tools repository and export CLI/tests.

All four owners see the full frozen request and all declared role boundaries.
They may agree on interfaces through ordinary notes and read-only peer
checkouts, but may not edit peer files or wait indefinitely for a response.

The fixed sequence for each arm is:

1. Initial concurrent implementation of revision 1.
2. A scheduled revision-2 event after the initial checkpoint, regardless of
   which condition appears stronger. The checkpoint is all initial owners
   terminated or reaching their predeclared limit, never an outcome-selected
   interruption.
3. Concurrent revision-2 work: `storage` is a fresh successor session in the
   same role/checkout with the exact source, handoff, notes, and tests; `api`,
   `browser`, and `export` use their actual resumed session continuity as
   supported by the runner. The successor/resume distinction is recorded, not
   described as one uninterrupted conversation.
4. A fresh integration owner integrates delivered work in both repositories,
   runs the common checks, and records exact heads, interfaces, failures, and
   delivery state. Integration may resolve genuine conflicts but may not
   independently implement missing owner features.
5. If the integration owner records concrete failures, at most two bounded
   correction rounds are dispatched only to the named owners. Each request must
   state the observed failure and preserved constraints, not a coordinator-made
   solution. Integration revalidates after each round. An empty correction list
   ends correction.
6. A fresh, independently blinded review evaluates the source-bound delivery
   bundle and evidence using the same rubric for both conditions.

No owner is launched after seeing which arm is winning. A missing handoff,
timeout, transport error, invalid correction request, or failed integration is
retained as such and passed to review.

## 5. Rehearsal, freeze, and scored order

Run one paired, unscored rehearsal before the four scored arms. The rehearsal
exercises setup, source copying, tool capture, sandbox boundaries, prompts,
base acceptance gate, handoff collection, PI-aware offline snapshot/report
capture, artifact bundling, and review blinding. It is not used as an outcome,
not tuned into a result, and does not justify changing the frozen task after
scored execution begins. Any harness defect found in rehearsal is repaired and
the changed inputs are re-frozen before score collection.

Before the first scored arm, freeze and hash:

* both source baselines and all acceptance/fixture files;
* this protocol, the product contract, runner, isolation launcher, prompts, and
  model/tool configuration;
* model alias, actual resolved model/version, reasoning setting, context
  limits, CLI version, Node/Python/browser versions, and tool hashes;
* owner order, concurrency, time limits, revision event, successor/resume rule,
  correction cap, review rubric, redaction rules, and failure policy.

The scored order is fixed and counterbalanced as requested:

| pair | first arm | second arm |
|---|---|---|
| A | `A-control` | `A-aware` |
| B | `B-aware` | `B-control` |

The four scored arms are sequential, with no overlapping candidate workers or
unrelated evaluation subprocesses. Fresh workers and reviewers do not inspect
earlier scored artifacts or the opposite arm. Pair labels are replaced with
opaque labels for independent review. Reviewers may still infer provenance from
content; that blinding limitation is recorded.

## 6. Equal budgets and instrumentation

All arms use Luna at medium reasoning effort and the same model alias/configured
toolchain. The current runner declares the following wall-time limits per
worker/session: initial 1,800 seconds, revision 1,800 seconds, integration
1,200 seconds, each correction 900 seconds, and review 900 seconds. The
predeclared limits apply equally to control and aware arms; actual termination,
timeout, truncation, exit code, and transport status are recorded separately.

Measure, without pooling away failures:

* setup/enrollment/export time and troubleshooting time;
* per-owner, successor, integration, correction, and review wall time;
* observed input/output/reasoning token usage and truncation where available;
* actual model/version, accepted reasoning setting, context capacity, tool
  versions/hashes, process exit and timeout state;
* human interventions, their reason, duration, and whether they altered source,
  prompts, scheduling, or only recorded an operational failure;
* commits, changed files, handoff completeness, interface/rework/duplicate
  work, correction count, validation commands and actual outputs;
* acceptance defects by contract area, regressions, integration failures,
  successor recovery, and review findings;
* PI setup/record/report overhead separately from steady-state worker effort;
* whether the final delivery is accepted, incomplete, failed, or indeterminate.

Token counts or model throughput are never fabricated from a configured quota.
If telemetry is absent, record it as unavailable. There is no quota-based
stopping rule or quota-based success criterion. More tests, more notes, or more
PI records are not quality scores.

## 7. Model, tool, and environment limitations

The current runner names the Luna model alias `gpt-5.6-luna` and requests
medium effort. The exact control and PI-aware condition preflights passed with
the actual model, browser, Git commit, separate final output, and same-session
resume checks. The aware preflight also passed its scoped PI lifecycle. These
are preparation-gate results, not candidate or product results; their retained
records are:

* `archive:20260908-luna-release-03/arms/preflight-control/preflight.json`;
* `archive:20260908-luna-release-03/arms/preflight-aware/preflight.json`.

A pinned underlying weight/version is unavailable. This is an explicit model
reproducibility limitation: record the resolved model metadata and accepted
settings, do not imply immutable weights, and do not pool this study with a
future run using a different pinned model revision.

An independent review of the first preflight implementation found that the
resume subcommand could fall back to its context default despite retaining the
Luna/medium model and effort settings. The original-context check reported
`190000` tokens while the resume check reported `258400`; those old attempt
artifacts are preserved. The correction reapplied all configuration after the
resume subcommand and added typed own-session metadata checks for model, effort,
and effective context. Both exact runtime validations then passed with Luna
medium, effective context `190000`, and the same original thread. Evidence is
retained at:

* `archive:20260908-luna-release-03/arms/preflight-control/resume-validation.json`;
* `archive:20260908-luna-release-03/arms/preflight-aware/resume-validation.json`.

The initial configured context window is `200000`; the CLI exposes 95% of that
as effective `190000`. `auto_compact=160000` was requested, but its effective
runtime behavior is not separately observable. These are preflight correction
and instrumentation facts, not candidate or product results.

Capture tool binaries and hashes, browser version, Node/Python versions,
context-window settings, and install output. A tool installation failure,
invalid model setting, CLI transport failure, or missing browser is a harness
failure; retain it and distinguish it from an owner failure. The evaluation
uses local disposable repositories and normal model transport only. No
production endpoint, scheduled check, monitored service, external Git, provider
credential, or host skill is an experimental input.

Isolation is an allowlist/cooperative filesystem boundary, not hostile-tenant
security. The runner uses explicit read-only and writable paths, but shared host
kernel/process resources and network behavior may remain observable. Network
isolation is therefore a limitation: do not claim that candidates were unable
to communicate with arbitrary network services unless the captured launcher
proves that restriction. The protocol permits no external service use beyond
normal model transport, and any observed network access is logged as a protocol
deviation or environment limitation. Canonical repositories are not mounted in
candidate sandboxes.

Git isolation is likewise cooperative rather than hostile-owner isolation.
Peer checkout files are read-only, while the shared Git common metadata needed
for normal linked-worktree commits is writable. Prompts explicitly forbid
changing or deleting peer branches. After every owner stage, `check_owner_refs`
records the expected and actual owner-branch HEADs; any discrepancy is retained
as a procedure failure, not silently repaired or attributed to a candidate.
Shared Git metadata and shared network/process resources are accepted study
limitations and must be disclosed in the final report.

## 8. Preflight and failure handling

During the unscored paired rehearsal, the browser refresh oracle incorrectly
expected the original incident set after the fixture deleted incident-060 and
inserted a backdated row. The test was corrected to distinguish old-snapshot
replay from an explicit refresh against the changed dataset, and to wait for a
new snapshot identifier. All eight corrected browser tests passed against an
unchanged committed rehearsal candidate. No candidate code or worker prompt was
repaired or coached. Original rehearsal acceptance files, failures and correction
work remain intact and unscored. Calibration evidence is retained under
`archive:20260908-luna-release-03/calibration/refresh-oracle`;
the fresh `baseline-calibrated-control` baseline gates use the corrected suite.
This rehearsal artifact is not a product-quality or PI-efficacy result.

Unstarted `B-aware` native setup also returned an uncertain receipt for SAYINT-39.
Read-only reconciliation found the exact saved browser record already present;
reusing the original packet settled the journal without creating another issue.
Setup resumed only after verifying unchanged clean baseline worktrees, unchanged
acceptance/contract inputs, and identical saved native packets. The remaining
records were then prepared normally. Original evidence was not replaced.
Its setup timing is explicitly filesystem birth time through completed recovery
(one-second resolution), including the interruption and coordinator work on the
setup recovery path. This differs from other arms' monotonic active setup time;
report it separately and do not attribute that harness-development pause to Luna
quality or a general PI productivity effect. Steady-state worker time remains a
separate metric. No scored worker had launched when this occurred.

The standalone older neutral preflight's first attempt failed its strict final
marker check. It is preserved at
preparation ID `pi-codex-worker-v2-eqt9khn4` as harness-preparation evidence only and is
not a score, condition run, or candidate result. The later exact condition
preflights above are the gates relevant to this Luna study.

Before scored launch, validate the untouched Status baseline and support
scaffold with the common tests. Expected new-feature failures must be explicit;
existing regression tests must pass. Also exercise the actual worker/harness
path in rehearsal: local HTTP/browser navigation where required, a disposable
Git commit, source-bound handoff, separate final output, refusal to read
unrelated context, and the aware-only scoped PI commands. A deterministic
external check alone is insufficient for worker preflight.

At every stage:

* never overwrite an existing arm directory or artifact;
* never silently restart a timed-out or failed session;
* preserve stdout/events, stderr, prompt, command, status, usage, source head,
  dirty state, handoff, and reason for termination;
* mark missing telemetry, missing handoff, provider uncertainty, or invalid
  evidence explicitly;
* stop the affected arm when a required frozen input, source copy, identity,
  or PI record is uncertain, then retain the failure for review;
* continue other predeclared arms only when doing so cannot expose the failed
  arm's outcome or change their equal conditions;
* run `check_owner_refs` after every owner stage and retain any expected-versus-
  actual branch-HEAD discrepancy as a procedure failure;
* do not repair candidate source, acceptance files, prompts, or handoffs from
  the coordinator; corrections must come from the bounded owner process;
* do not relabel setup, runner, provider, or model failures as PI effects.

An arm may be classified as a harness/transport failure, product-incomplete,
contract-failing, accepted, or indeterminate only from retained evidence. A
failed rehearsal is preparation evidence and does not become a scored arm.

## 9. Evidence bundle, review, and analysis lock

For each arm, preserve a source-bound bundle containing source repository and
support repository heads, exact changed-file lists, all owner handoffs, notes,
integration delivery and correction files, commands/results, acceptance output,
events/usage, setup and environment manifests, and the PI-aware offline snapshot
and local report where applicable. Handoffs are included in the bundle even
when incomplete; their absence is itself evidence. Generated evidence and trial
instructions are not staged into the product repositories.

The reviewer receives neutral artifact names, hashes, the same contract and
rubric, and no condition labels, worker transcripts, live PI state, or prior
results. The evaluator retains the private mapping. Review covers functional
acceptance, legacy compatibility, API/browser/export cross-client consistency,
revision-2 retroactive expiry, accessibility/race behavior, source-bound
interfaces, regression results, handoff/successor usability, and unresolved
limitations. Review time and findings are equal-budgeted and separately
reported; blinding is imperfect if implementation content reveals provenance.

The analysis dataset is frozen after all four scored arms and reviews are
complete. No acceptance rule, correction interpretation, exclusion, or metric
is changed after unblinding. Report pair-level values and raw arm-level failures
before any summary. Treat setup, PI record overhead, and review as separate
components of the primary effort measure so a later report can show both
end-to-end and steady-state views. Do not claim statistical significance or
generalization from two pairs.

## 10. Current pre-freeze status and pending checklist

The latest runner and evaluation module implement the intended frozen-input
hashes, scored-arm order enforcement, preflight/freeze gates, independent
mechanical gates over immutable source archives, and source-bound redacted
review. Relevant implementation points are `inputs()`, `require_preflight()`,
`freeze()`, `require_frozen()`, `run_arm()` in
`experiments/luna_release_study.py`, and `gates()`/`review()` in
`experiments/luna_release_evaluation.py`.

The parent is still finishing freeze and unit checks. Before any scored arm is
started, retain and verify all of the following:

1. **Preflight evidence:** both condition preflight JSON files remain
   `passed: true`, including actual model/browser/Git/resume checks and the
   aware PI lifecycle checks. The old neutral failed attempt remains separate
   and unscored.
2. **Rehearsal review:** both paired rehearsal arms have retained evaluation
   review records before `freeze()` is allowed. Product/candidate blockers
   found in those reviews are retained as rehearsal evidence and do not require
   repair or acceptance for freeze; only unresolved **harness** blockers prevent
   freeze.
3. **Harness review and exact hashes:** `harness-review.json` exists with an
   empty `blocking_findings` list and `input_hashes` exactly equal to the
   current `inputs()` map, including this protocol, the runner, evaluation,
   contract, fixtures, isolation/review helpers, and acceptance files.
4. **Equality/order freeze:** every scored arm has equal Status/support trees,
   contract hash, and acceptance-file hashes; `freeze.json` records the fixed
   order `A-control, A-aware, B-aware, B-control`, equal limits, toolchain,
   PI-tool hashes, and frozen prompt hashes. No scored `execution-start.json`
   may exist before freeze.
5. **Unit and acceptance checks:** complete and preserve the parent’s remaining
   unit checks plus the independent API/export, browser, legacy API/browser,
   Status, and support-tools gates. A failed or skipped check remains a failure;
   it is not hidden by the source archive or review layer.
6. **Reference and review provenance:** retain every `check_owner_refs` result,
   with expected/actual owner-branch HEADs and any discrepancy classified as a
   procedure failure; also retain the source-bound handoff export, redaction
   audit, missing-handoff record, neutral review label mapping, mechanical gate
   logs, and reviewer decision. Live PI records, offline arm snapshots, and
   local reports remain distinct evidence types.
7. **Deployment boundary:** confirm that no canonical source is committed,
   deployed, or used as a candidate checkout; only disposable archived heads
   enter evaluation. Keep the unavailable pinned weight version and shared
   network/process isolation limitation in the final disclosure.

Until this checklist is complete, the study remains prepared but not frozen,
launched, or interpretable as an A/B result.
