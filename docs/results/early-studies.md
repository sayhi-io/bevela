# Early Project Intent studies

Curated historical evidence, newest first, ending with the stopped repair study
before the first seven-seam batch. This page records completed observations,
invalid attempts and unresolved questions; it does not authorize further trials.
The evidence index names retained artifacts and their SHA-256 digests without
publishing raw transcripts, session identifiers or private filesystem paths.

## Reading the measurements

- All dates and launch times below are **UTC**. Times displayed to the second
  are truncated from recorded timestamps, not inferred from directory names.
- Microstudy seconds are the condition's worker execution window, ending when
  its two native processes finish. They exclude subsequent observer analysis.
- Status/release team time includes the study's implementation and succession
  phases. Review time is separate. The measured acceptance/review path adds
  recorded setup, gates and review; it excludes unmeasured scheduling gaps.
  These columns are not the later studies' frozen final-project metric.
- Acceptance, process completion and source review are different outcomes.
  A reviewer process exiting successfully does not mean it accepted the candidate.
  Unavailable or unscored measurements are not zero.
- Control means ordinary native workers; PI means the assigned PI-enabled arm,
  even when a worker failed onboarding. Mechanisms below are observed behavior
  or explicitly labeled hypotheses, not isolated causal effects.
- Research labels are editorial behavior stages, not software release numbers.
  **v0.01** denotes the `86ffbc5` baseline, **v0.02** onboarding recovery matching
  `b896b73`, and **v0.03** the first stopped repair candidate atop `ace04ef`.
  Earlier Status pilots are **prebaseline**, not retrospectively v0.01.
  The later v0.04/v0.05 seven-seam stages are outside this page.

## 2026-09-09 — stopped repair candidate (v0.03)

Archive: `20260909-seam-repair-b-v3`. Model: `gpt-5.6-luna`, Medium.
Five PI-only trials were planned; there was no newly run control arm.
The source was an uncommitted, hash-bound candidate atop `ace04ef`, not the
later committed integration-context version.

| Trial, newest first | UTC start | Worker window | Recorded disposition |
| --- | --- | ---: | --- |
| 3 | 2026-09-09 01:55:58 | 92.842s | Both processes exited 0; acceptance unscored |
| 2 | 2026-09-09 01:54:17 | 101.443s | Both processes exited 0; acceptance unscored |
| 1 | 2026-09-09 01:52:12 | 124.535s | Both processes exited 0; acceptance unscored |

Trial 4 raced the stop marker and was terminated; partial evidence remains
separate. Trial 5 never started. The planned analyzer required all five completed
trials and did not produce a final acceptance result. Do not count three process
completions as three successful repairs or run the old analyzer to fill the gap.

Observed friction: producers in trials 1 and 2 ended with known receipt-failure
reports while peers repaired the consumer; trial 3 encountered a same-seam claim
denial despite different declared paths. These observations do not establish
fully coordinated repair. **Next question, proposed:** can acknowledged,
path-bounded agreement avoid overbroad claims and verify actual repair closure?
Later seven-seam candidates did change repair/context behavior, but their different
fixture is not a retrospective acceptance verdict for these three trials.

Evidence: `STOPPED.md`, `plan.json`, and each completed trial's
`pi/summary.json` in the evidence index.

## 2026-09-09 — onboarding recovery (v0.02)

Archive: `20260908-onboarding-ab-v2`; its date prefix is not the UTC execution
date. Model: `gpt-5.6-luna`, Medium. Both original tasks survived in **2/2 control
and 2/2 PI conditions**; all four PI workers enrolled and released.

| Pair, newest first | UTC start (earliest worker) | Control | PI | Control window | PI window |
| --- | --- | --- | --- | ---: | ---: |
| 2 | 2026-09-09 01:16:07 | Both tasks preserved | Both tasks preserved | 52.105s | 74.034s |
| 1 | 2026-09-09 01:14:13 | Both tasks preserved | Both tasks preserved | 55.901s | 113.791s |

The four recorded changed core-module hashes match `b896b73` and its merge
`ace04ef`. This supports an onboarding-recovery behavior label; successful
enrollment alone does not establish precise declarations or a coordination benefit.

**Observed/hypothesized explanation for the tie:** ordinary code inspection and
post-change checks sufficed in both arms; PI additionally recovered discovery and
command-quoting friction. **Next question, proposed at that stage:** distinguish
reliable onboarding from reliable ownership/reconciliation at a shared boundary.
The subsequent repair-candidate batch ran, but stopped without final scoring.

Evidence: `20260908-onboarding-ab-v2/results.json` and `plan.json`.

## 2026-09-08 — unchanged label-task microstudy (v0.01)

Model: `gpt-5.6-luna`, Medium; PI release `86ffbc5`.
One producer migrates prices to integer cents while another worker adds dollar
receipt labels in the same checkout. “Both tasks preserved” requires cent storage,
correct checkout totals and correct dollar labels, not merely passing worker tests.

**Denominator:** one label pilot plus repeats 1–13 = **14 unchanged pairs**.
Control preserved both tasks in **11/14**; PI in **9/14**. Do not add the 14-pair
aggregate as another experiment. Counting the different full-render pilot yields
15 edit-enabled pairs across **two task variants**, not 15 repetitions of this task.
The read-only launch is invalid and excluded.

All rows are newest first. Repeats 4–13 were ten additional pairs; repeats 1–3
were the preceding three-pair batch.

| Repeat | UTC start (earliest worker) | Control | PI | Control window | PI window |
| --- | --- | --- | --- | ---: | ---: |
| 13 | 2026-09-08 23:02:56 | Receipt broken | Both tasks preserved | 27.738s | 82.730s |
| 12 | 2026-09-08 23:01:45 | Both tasks preserved | Both tasks preserved | 46.289s | 70.768s |
| 11 | 2026-09-08 23:00:33 | Receipt broken | Receipt broken | 32.438s | 72.294s |
| 10 | 2026-09-08 22:59:13 | Both tasks preserved | Both tasks preserved | 55.199s | 79.336s |
| 9 | 2026-09-08 22:57:55 | Both tasks preserved | Both tasks preserved | 45.316s | 78.658s |
| 8 | 2026-09-08 22:56:40 | Both tasks preserved | Both tasks preserved | 45.874s | 74.332s |
| 7 | 2026-09-08 22:55:36 | Both tasks preserved | Receipt broken | 31.814s | 64.360s |
| 6 | 2026-09-08 22:53:47 | Both tasks preserved | Receipt broken | 49.416s | 108.659s |
| 5 | 2026-09-08 22:51:55 | Both tasks preserved | Both tasks preserved* | 45.091s | 111.919s |
| 4 | 2026-09-08 22:50:46 | Both tasks preserved | Both tasks preserved | 44.433s | 68.852s |
| 3 | 2026-09-08 22:41:24 | Both tasks preserved | Both tasks preserved | 46.443s | 67.487s |
| 2 | 2026-09-08 22:39:30 | Cents migration undone | Both tasks preserved* | 62.732s | 91.742s |
| 1 | 2026-09-08 22:37:02 | Both tasks preserved | Receipt units wrong | 50.305s | 95.619s |
| Label pilot | 2026-09-08 22:22:54 | Both tasks preserved | Receipt units wrong | 46.418s | 70.617s |

*The PI receipt worker failed enrollment in repeat 2 and repeat 5. Keep both
outputs in the assigned-PI group; do not label them fully enrolled coordination.*

Repeats 4–13 alone: **8/10 control, 7/10 PI**, with six ties where both succeeded,
two control-only successes, one PI-only success and one shared failure.
Median condition windows were **45.203s control / 76.495s PI**; batch elapsed
**813.020s**, from 22:50:46.450 to 23:04:19.471 UTC. Repeats 1–3 alone were
**2/3 versus 2/3**. These small samples do not show an aggregate PI benefit.

### Mechanisms and next questions

These are explanations to test, not claims that PI alone caused the differences.

| Observation | Evidence-backed behavior / suspected explanation | Next question (proposed, not answered causally) |
| --- | --- | --- |
| Control-only success: label pilot | Control repaired the consumer after a failure; the PI producer detected the failure but deferred to the other workstream, leaving incorrect labels. | Can guidance require reconciliation of a known cross-boundary regression without granting unrelated ownership? |
| Control-only success: repeat 1 | PI retained incorrect receipt units. This audit does not assign a more specific causal mechanism than the preserved output supports. | Which read/check/write ordering left the unit mismatch unresolved? |
| Control-only success: repeat 6 | Control detected raw-cent labels and adapted; PI producer saw the receipt failure but left it for the other owner. | Can one acknowledged repairer close an observed break before completion? |
| Control-only success: repeat 7 | Control producer inspected the new consumer and migrated both sides; PI deferred the known consumer failure. | Can declared boundaries remain advisory rather than become repair barriers? |
| PI-only success: repeat 2 | Control receipt worker restored dollar storage, undoing the producer's task. PI ended correct despite one failed enrollment. | Can integration checks preserve both task contracts without rollback? |
| PI-only success: repeat 13 | Control validated before migration and never rechecked the receipt; fully enrolled PI receipt worker corrected a post-migration failure. | Does persistent seam coverage explain recovery better than advance context alone? |
| Both fail: repeat 11 | Both retain broken receipt behavior; control's earlier assertions did not cover the final migrated state. | Will final-state consumer coverage detect the late change? |
| Both succeed: repeats 3–5, 8–10, 12 | Current-code adaptation and ordinary validation can suffice; this is not uniquely PI behavior. Repeat 10 also removed a new regression test because of declared overlap. | Can coordination retain useful coverage while avoiding ownership overreach and excess context? |

No retries, corrective feedback or task-source changes occurred within the stated
repeat batches. Separate condition directories and inherited native configuration
were not hermetic host-read isolation. The later onboarding and repair changes
were completed development steps, not proof of the hypotheses above.

Evidence: `20260908-seam-micro-repeat-results.md`,
`20260908-seam-micro-ten-more-results.md`, its analysis and plan JSON, and
per-repeat summary artifacts. Label-pilot behavior is also preserved in the
historical worker-study documentation; its two summary artifacts bind timing.

## 2026-09-08 — earlier micro calibration pilots

Model: `gpt-5.6-luna`, Medium. These are not additional unchanged label repeats.

| Pilot, newest first | UTC start | Control window | PI window | Disposition |
| --- | --- | ---: | ---: | --- |
| Full render | 2026-09-08 22:20:22 | 59.592s | 132.632s | Different, larger receipt task; timing calibration, no newly assigned acceptance score here |
| Read-only | 2026-09-08 22:19:01 | 27.556s | 44.314s | Invalid launch: neither condition could edit |

**Suspected explanation:** native permissions caused the first failure; task size
and onboarding/execution overhead contributed to missing the short timing target.
**Next questions then proposed:** does explicit native workspace-write permit real
editing, and does a smaller label task expose the shared-unit boundary cheaply?
Both changes were subsequently exercised in distinct preserved pilots; they were
not repairs to the original candidate outputs. The roughly 30-second target was
still unmet in the label pilot.

Evidence: `20260908-seam-micro-render-pilot` and
`20260908-seam-micro-readonly-pilot`, each arm's `summary.json`.

## 2026-09-08 — release Study03 v2 (v0.01)

Archive: `20260908-luna-release-03-v2`. Model: `gpt-5.6-luna`, Medium.
All four arms completed evaluation. **Control accepted 1/2; PI accepted 0/2.**
The frozen PI manifest's 15 recorded Python modules match `86ffbc5`.
This was a multi-owner release/succession task with a scheduled shared revision,
not the later two-worker micro fixture.

| Arm, newest first | UTC execution marker | Final acceptance / review | Team time | Review time | Measured path through acceptance/review | Correction sessions |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| B2 control | 2026-09-08 21:28:16 | Accepted | 640.450s | 86.829s | 739.159s | 0 |
| B2 PI | 2026-09-08 21:09:48 | Rejected | 1018.678s | 75.156s | 1156.921s | 1 |
| A2 PI | 2026-09-08 20:58:08 | Rejected | 597.265s | 88.632s | 700.175s | 0 |
| A2 control | 2026-09-08 20:46:02 | Rejected | 598.281s | 113.372s | 723.727s | 0 |

The execution markers precede native worker execution; they are not first-token
timestamps. B2 PI's measured path includes recorded interrupted setup/recovery.
Its correction session is part of the old protocol, not comparable to later
no-guidance trials.

Final review findings:

- **A2 control:** output append precedes checkpoint persistence; interruption can
  cause duplicate export pages on restart.
- **A2 PI:** default retroactive retention differs between storage and worker;
  independently recorded mechanical aggregate also fails on an undelivered file.
- **B2 PI:** output/checkpoint durability gap and failed mechanical aggregate for
  an undelivered file.
- **B2 control:** accepted; no blocking finding in the recorded independent review.

**Observed/suspected explanation for the ordinary-arm advantage:** one ordinary
candidate preserved the release contract while three candidates retained distinct
durability/default-policy/delivery gaps. More PI context did not guarantee their
reconciliation. The record does not isolate why the model made those choices.
**Next question, proposed:** can simpler natural seam pressure separate live
coordination from scheduled revision, succession and evaluator complexity?
The later microstudy did run, but was a new design, not a matched repair of v2.

Use completed `results.json`; `launch-report.json` still describes a running
study and is not final evidence. Likewise, reviewer process `passed` and
candidate `accepted` fields must not be conflated. Favorable individual test
commands do not override a failed aggregate or source-backed rejection.

Evidence: `results.json`, `freeze.json`, and each scored arm's
`execution-start.json`.

## 2026-09-08 — release Study03 v1, invalidated

Archive: `20260908-luna-release-03`. Luna Medium; frozen modules also match
the v0.01 baseline. Scored A-control began **2026-09-08 19:50:23 UTC**.
Invalidation was recorded at **20:10:33.981 UTC**. A-aware, B-aware and B-control
never started as scored arms. Earlier control/aware rehearsals were unscored.

**No valid A/B acceptance count or performance comparison.** The browser
navigation oracle sometimes sampled an empty loading-state row count, then
waited for zero rows after ten correct rows appeared. This was an evaluator
failure, not evidence of model or PI failure. The interrupted review is not a
completed acceptance decision; no comparable final team score is assigned here.

**Next question then proposed:** can stable pre-navigation expected IDs remove
the oracle race without weakening assertions? **Completed follow-up:** the
separate repaired eight-test suite passed 80/80 checks over ten calibration
repetitions against unchanged candidate code; a new v2 freeze subsequently ran.
Those 80 checks are evaluator calibration, not 80 model trials or retroactive
acceptance of the invalidated sequence.

Evidence: `invalidation.json`, scored A-control's `execution-start.json`,
and the historical invalidation account in `CLI_AB_LUNA_RELEASE_03_STATUS.md`.

## 2026-09-06 — Status Study02, prebaseline

Archive: `20260906-status-shared-contract-02`.
Model: `gpt-6-astra`, Medium. Two concurrent owners, fresh integration successor
and fresh source reviewer per arm; two matched pairs, not four different studies.

| Arm, newest first | UTC execution marker | Common acceptance | Review | Team time | Review time | Measured path through acceptance/review |
| --- | --- | --- | --- | ---: | ---: | ---: |
| B control | 2026-09-06 06:09:11 | Passed | Accepted, zero blockers | 646.051s | 177.880s | 832.207s |
| B PI | 2026-09-06 05:56:20 | Passed | Accepted, zero blockers | 561.698s | 182.314s | 753.259s |
| A PI | 2026-09-06 05:42:00 | Passed | Accepted, zero blockers | 621.560s | 211.150s | 841.849s |
| A control | 2026-09-06 05:28:33 | Passed | Accepted, zero blockers | 548.174s | 150.542s | 706.979s |

Every arm passed five common API groups, nine native-browser tests, regression
and syntax gates. **2/2 accepted per treatment**, zero feature-correction rounds
and zero human feature clarifications. These are not 7-seam scores.
A nonblocking review observation about absent handoffs arose because source-only
review bundles deliberately omitted untracked handoffs; actual successors had them.

**Observed/suspected explanation for the tie:** complete shared requirements,
ordinary notes and Git already supported interface alignment and succession.
The timing direction reversed between pairs. PI added structured observations,
not a demonstrated quality or efficiency advantage.
**Next question then proposed:** does genuinely incomplete successor context make
queryable project state useful after stronger isolation and worker validation?
The later release study explored succession/revision, but was a different task.

Workers/reviewers could not run the native browser under their sandbox; the
external evaluator did. Some PI roles read global skills outside the frozen
context. These limitations preclude a clean causal interpretation.
The report identifies harness HEAD `f57251e` plus uncommitted frozen evaluation
files; that alone is not a complete PI behavior-source seal. Keep the study
prebaseline rather than infer the later `86ffbc5` release from chronology.

Evidence: `RESULTS.md`, `RESULTS.json`, and per-arm `started.json`.

## 2026-09-06 — Status Pilot01, prebaseline

Archive: `20260906-status-cli-pilot-01`.
Model: `gpt-6-astra`, Medium. PI CLI source is reported as `617f5957`,
tree-identical to merge `f57251e`; not the later v0.01 baseline.

| Arm (aware launched after control) | Actual UTC launch | Common acceptance | Independent review | Parallel implementation | Successor | Sum of measured implementation and successor |
| --- | --- | --- | --- | ---: | ---: | ---: |
| PI-aware | Unavailable in retained execution summaries | 11/11 | Accepted, zero blockers | 390.02s | 93.64s | 483.66s |
| Ordinary | Unavailable in retained execution summaries | 11/11 | Accepted, zero blockers | 320.02s | 95.80s | 415.82s |

The manifest's **2026-09-06 01:18:05.404 UTC** timestamp is preparation, not
execution. The native launch command used ephemeral sessions; retained execution
summaries expose monotonic durations but no UTC start fields. Do not substitute
file modification times, identifier-derived dates or preparation time.
The sums above exclude source review, setup and observer work and are not a
continuous batch stopwatch. One integration overlapped aware implementation.

Both arms met the same acceptance rubric. Their own source-test counts
(49/49 ordinary, 41/41 PI) are different suites, not comparative quality scores.
No post-review feature correction was needed.

**Observed/suspected explanation for the tie and ordinary timing advantage:**
both arms had the full task contract and ordinary notes; no uniquely PI-supplied
fact was shown to change a decision. Additional onboarding/reporting could add
work, but its isolated cost was not measured.
**Next questions then proposed:** fix environment/handoff recording, counterbalance
order and test a harder shared contract. Study02 subsequently ran those broader
shared-contract/succession tasks; it also produced a quality tie.

Both arms encountered a missing writable Git-common-directory allowance; observer
Git-state handling remained evaluation administration, not zero total human work.
The final-message output path also shortened some saved handoffs. These are
harness defects, not evidence that workers failed to produce detailed handoffs.
Node VM checks did not establish native visual/accessibility validation.

Evidence: `RESULTS.md`, `manifest.json`, and the four execution summaries.

## Coverage and unresolved claims

This is a source-bound curation, not a new model adjudication. It does not turn
unscored repair outputs, invalid launches, unscored rehearsals or calibration
checks into accepted projects. Preparation-only inventories are not model trials.

The later [Low-effort A/B/C comparison](seven-seams.md), outside this page, is
**A: Luna Low ordinary 0/7, 2/7; B: Sol Low ordinary 3/7, 4/7, 3/7;
C: Luna Low + PI 7/7, 7/7**. It compares PI assistance with both ordinary
configurations; the model groups remain separately labeled.

No additional model execution, source repair or raw-evidence rewrite was performed
to prepare this page. Proposed next questions remain proposals unless explicitly
identified above as completed follow-up experiments.

## Evidence index

Artifact names are relative to their retained evaluation archive, not public
download links. SHA-256 binds the source bytes reviewed; it does not independently
certify every historical claim. Timing summaries may contain private information
in the retained archive; only their names and digests are published here.

| Source artifact | SHA-256 |
| --- | --- |
| `20260909-seam-repair-b-v3/STOPPED.md` | `fe2b3bd2f170c72d7920fece132869df1070ede46b5466f988e8ea6cb3a31b8b` |
| `20260909-seam-repair-b-v3/plan.json` | `5f3069666bdd0f4a22d92ba79fe9c010e0962aa31a530d82889734e73a3675ae` |
| `20260908-onboarding-ab-v2/results.json` | `578a0ba53ca6d935da2baefee694abeafec88fa10e6fc7d1c6ca9bd550bf40c1` |
| `20260908-onboarding-ab-v2/plan.json` | `399b1cd0849f1b55be43440a3e7b0ba243843e84b9ebd588ddbde8d9c3d8ed87` |
| `20260908-seam-micro-repeat-results.md` | `e9783db494a01bd7af18b9963dd8073908aa6d8dab474ad6217bd55acb129397` |
| `20260908-seam-micro-ten-more-results.md` | `404361ea515487b68787f0365d714386d76f9c6d00c4de12ab0114136a771041` |
| `20260908-seam-micro-ten-more-analysis.json` | `b2f96d706baf31fb2d839d66982cae73fe56eccf479c9f64ba9c13865d744b83` |
| `20260908-seam-micro-ten-more-plan.json` | `f98ad9b40cfa01662c27604a0c507460e4dceaf82af50b41f94b3cb61c4bc524` |
| `20260908-luna-release-03-v2/results.json` | `2af81efa200e2bd80116b5f503448a60b388bd9bcd60fdcafb95c845cc3b3db8` |
| `20260908-luna-release-03-v2/freeze.json` | `66b1e38f77a7390e4ac9b91d1b3ac4181ae515995eeb2f1125fc9aa65a5b9767` |
| `20260908-luna-release-03/invalidation.json` | `66d27f1fd8863022b7004b19a425a73703d3bd849e83d99ddd043e4576544637` |
| `20260906-status-shared-contract-02/RESULTS.md` | `ca3a78235a957fc83e81c7d04dad7b5ff1a9e230b3c7b642e9a38e14990ddeec` |
| `20260906-status-shared-contract-02/RESULTS.json` | `0bb1c9dfce4d2d0e7544f95300a3b2e836d44ce4df67de3727336da5e037ba26` |
| `20260906-status-cli-pilot-01/RESULTS.md` | `b2631f9b9153ce798f843a69341dfdb9c185d6597b277e7b3dd8539584099028` |
| `20260906-status-cli-pilot-01/manifest.json` | `020a5293cb58c60bd510c4b90df40c48d22eb13c23814262bec38fb9b9b27c4c` |
| `20260908-seam-micro-repeat-1/control/summary.json` | `6affa7f7ac68868806f5c3858ea87bcd91ae636e2469f6870d3a78f3c3ecf4d0` |
| `20260908-seam-micro-repeat-2/control/summary.json` | `24f6656098457906e6b36b2dc04204cc7ab1891a7237fc37d8f8133df85fd495` |
| `20260908-seam-micro-repeat-3/control/summary.json` | `016178cc733737e04f028df145521ad36a9ef1035f05f7d5d9cba024cc2d38ce` |
| `20260908-seam-micro-repeat-4/control/summary.json` | `15a5cf5e6de1924bfbf037d10d1e6b4a0a80db2e76ae94b88741b306e967c6c1` |
| `20260908-seam-micro-repeat-5/control/summary.json` | `eda974dc07f3da8bd86f3054db12c3b6dcc5dc55f8c4584943cba618bef40e8b` |
| `20260908-seam-micro-repeat-6/control/summary.json` | `c96be2c099f0a6b18069e1a1265a717bb962feeb7a893d3bc6d1ee84b710eed1` |
| `20260908-seam-micro-repeat-7/control/summary.json` | `c40ce41b26df4cfb13f06d148dae24f9cc0fb0c7a9f5075e23cc53e53d8ba6da` |
| `20260908-seam-micro-repeat-8/control/summary.json` | `de9f30fb32d4024278bc3594678ebf8ada171df17c8cd5789aa12cb8db751783` |
| `20260908-seam-micro-repeat-9/control/summary.json` | `e7b551005ff93b437efed4802d03e9ba8244daa38006f0bfe6f5a6708c4ed1a7` |
| `20260908-seam-micro-repeat-10/control/summary.json` | `b6740da7b9e8a3043213bdb0751e5c36124fabf13371944d851dd2f5807900cc` |
| `20260908-seam-micro-repeat-11/control/summary.json` | `bae15f06b4af395ef55ff6660c52179fda0cb2705637f7e22f2be69430c6f3cb` |
| `20260908-seam-micro-repeat-12/control/summary.json` | `4daebd4c6246b4c633349fe2f89b38df8d7b8c206ea8d14d6f7c05fbc9f6c02f` |
| `20260908-seam-micro-repeat-13/control/summary.json` | `e592760e5c64b2b001d50a0dabd82b6d41b9937e0376a753c1ff9d26c8f71908` |
| `20260909-seam-repair-b-v3/trial-1/pi/summary.json` | `9a32bc08b2fa7ef76677c5d209baedc225cb71a99701bc9837b5a01959e884eb` |
| `20260909-seam-repair-b-v3/trial-2/pi/summary.json` | `c7671d43bc498d40f38bd4bf6b4675d2b512382c7e00059dd78f6a568f559f65` |
| `20260909-seam-repair-b-v3/trial-3/pi/summary.json` | `ddc4e9e148b1045dc778ac7e8e3992bc35aefaf397c38bf2888ba2ac0f514b53` |
| `20260908-seam-micro-readonly-pilot/control/summary.json` | `3f2741365f1a130b6786b1c2184338ca5a7eb1e6a0da52481483afba4cae638a` |
| `20260908-seam-micro-readonly-pilot/pi/summary.json` | `e5acb547c34dec589040e5ae615bee0af02d36b2fdb904238dccfbe8065ca90e` |
| `20260908-seam-micro-render-pilot/control/summary.json` | `fd7e8cb1e0a7cd7fca3809fb7ab1d55436b36ff5eb671e36712c5f4f62acba60` |
| `20260908-seam-micro-render-pilot/pi/summary.json` | `6c204bd6ab9ca0169fcbcfda5c18374814f2f070beb26bc030f4e43738415bcd` |
| `20260908-seam-micro-label-pilot/control/summary.json` | `b8aa8567e5bc5631f8e3391644b7e6dabd0acc95938e4fbfd9971a5502ba0fe1` |
| `20260908-seam-micro-label-pilot/pi/summary.json` | `451508d3cc40ab35526957de19bf139753fbf18df7d78ef1eed53bf87f42e994` |
| `20260906-status-shared-contract-02/A-control/started.json` | `ba183ce1fc4c29eff63f9a47ec628447c20f6ed941b8d4627c33350b102ce87e` |
| `20260906-status-shared-contract-02/A-aware/started.json` | `7b94418e019f78ab5214128532c736aa1c5b01906466f969a4eb33886e94ffc2` |
| `20260906-status-shared-contract-02/B-aware/started.json` | `628c18a66e7fe99a743574a059ddc710091a78b222d55aaabede03332a692dcc` |
| `20260906-status-shared-contract-02/B-control/started.json` | `aa7a20cb7f3041defdf7478dfb3b521a66dc90d82c1ded07e0c466135a3c6f78` |
| `20260908-luna-release-03-v2/arms/A2-control/execution-start.json` | `18265ba36c29b9956fd859ce807d117a75e979cc029e1757d8f0e30f0c0a3e54` |
| `20260908-luna-release-03-v2/arms/A2-aware/execution-start.json` | `ede2b37d98eb136e526b596268ef2c4b829fbbf558825109cc698affdf198528` |
| `20260908-luna-release-03-v2/arms/B2-aware/execution-start.json` | `60f334d4b10ad8fd002d75c9a49dcb33753715d280daceddbce6f44b352dbfb1` |
| `20260908-luna-release-03-v2/arms/B2-control/execution-start.json` | `24fc0fc97fe69d12a5a8e2acbe4cb46130c8dc5280a2e62b0d6cb6b3274713fc` |
| `20260908-luna-release-03/arms/A-control/execution-start.json` | `c32f2285c334d46b5f7d75099c61d3b33c7363a9ec69e79006e36509010308eb` |
| `20260906-status-cli-pilot-01/control-execution.json` | `ca0d1427b52ec2d8ebef059982e548f4f144ee56e66f234aa6b26ca8c75b4e84` |
| `20260906-status-cli-pilot-01/control-integration-execution.json` | `3e7d88180f2386ae5a3b09c35c229d6cc7480daa4a521ad52d279a65f07202d1` |
| `20260906-status-cli-pilot-01/aware-execution.json` | `7aa91c204c0fa12b843f0dc45e9634b9c3cf916642425c32aa9514a9374dc55e` |
| `20260906-status-cli-pilot-01/aware-integration-execution.json` | `a755f9bb46b761b0759f03e74655147612c356fc1ce46a150bddf3c9c7991c25` |
| `docs/CLI_AB_SEAM_MICRO.md` (historical authored account) | `4e96a2fc1c7346b51b28d89260c6ea31ed429c84fe6579a752b171f2286a91fa` |
| `docs/CLI_AB_LUNA_RELEASE_03_STATUS.md` (historical authored account) | `355e2d2c90886cf359969dc7a97f29ca08c70508ec202565ec4a9571b2e77d97` |
