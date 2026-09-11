# Results

### What shared project state helps—and where it has not helped yet.

[Project Intent](README.md) · [Per-run measurements](docs/results/measurements.json) · [Methodology](docs/CLI_AB_EVALUATION.md)

We evaluate the **combined project**, not how busy a worker looks. Correctness,
project elapsed time, aggregate worker effort and useful parallel contributions
are separate outcomes. Failures, ties and interrupted attempts stay in the record.
[Coached controls are withdrawn](docs/CLI_AB_EVALUATION.md#withdrawn-coached-controls),
not counted as evidence for or against PI.

## Study history · newest first

Dates below are UTC. Completed groups follow actual execution order, not the date
their report was written. Detail pages preserve individual outcomes; recent run
tables use actual launch timestamps, including nearly simultaneous historical
launches. **Not run** is not a zero score. PI versions are research behavior stages,
defined [below](#pi-behavior-versions), not deployed release numbers.

| Executed | Study | Model / effort | Ordinary outcome | PI outcome | PI behavior |
| --- | --- | --- | --- | --- | --- |
| Sep 10 · recorded summary | [Qwen independent requests · candidate 2](docs/results/qwen-independent-requests.md) | Qwen3.8 DFlash2 · thinking off | **3/3 accepted**, 15/15 each | Steering on: **1/3 accepted**, 13/15, 13/15, 15/15; first two stopped at the 30-minute worker boundary. Owner-recorded outcomes, not a newly audited measurements export. | v0.05 backend unchanged; independent-request steering adapter v1 |
| Sep 10 · after cap500 | [Distributed steering · 500 calls / 500 turns](#qwen-distributed-500-limit-follow-ups) | Qwen3.8 DFlash2 · thinking off | No new matched control | **1/1 artifact accepted, 15/15 in 795.062s**; reporting worker exited 1, so `autonomous_complete=false` | v0.05 backend unchanged; cap500-turn500 adapter v1 |
| Sep 10 · after initial distributed pilot | [Distributed steering · 500-call cap](#qwen-distributed-500-limit-follow-ups) | Qwen3.8 DFlash2 · thinking off | No new matched control | **0/1 accepted, 14/15 in 1,076.096s**; partial-return pipeline failed | v0.05 backend unchanged; cap500 adapter v1 |
| Sep 10 · after ten-repeat cohort | [Distributed steering · initial pilot](#qwen-distributed-500-limit-follow-ups) | Qwen3.8 DFlash2 · thinking off | No new matched control | **0/1 accepted, 8/15 in 844.115s** | v0.05 backend unchanged; nested steering adapter v1 |
| Sep 10 · completed 00:44 UTC | [Seven-seam steering · ten repeats](#qwen-steering-ten-repeat-cohort) | Qwen3.8 DFlash2 · thinking off | [Earlier ordinary thinking-off control](docs/results/qwen-ordinary-thinking-off.md): **0/1 accepted, 0/7**; same fixture/runtime/task inputs, one run rather than ten control repeats | **10/10 accepted, 7/7 every project**; median 99.4s, range 48.0–303.2s | v0.05 backend unchanged; steering v1 repeated without treatment changes |
| Sep 9, 22:55–22:57 | [Qwen PI steering · first pilot](docs/results/qwen-steering.md) | Qwen3.8 DFlash2 · thinking off | No new control; preceding pull-only PI project scored 0/7 | **1/1 accepted, 7/7 in 95s**; both enrolled; 18 automatic notices, consumer reconciled migration. One pilot, not established reliability. | v0.05 backend unchanged; steering integration v1 |
| Sep 9, 22:42–22:44 | [Compact PI v2 · filtered Qwen CLI](docs/results/qwen-compact-pi-v2.md) | Qwen3.8 DFlash2 · thinking off | Not run | **0/1 accepted, 0/7 in 76s**; both workers finished. Consumer made no PI calls; producer left stale consumer unchanged. No loop or timeout. | v0.05 backend unchanged; Qwen CLI v2 |
| Sep 9, 22:01–22:07 | [Compact PI prompt · Qwen thinking off](docs/results/qwen-compact-pi.md) | Qwen3.8 DFlash2 · thinking off | Not run | **1/3 accepted: 0/7, 0/7, 7/7**; 130s, 84s, 103s. Two native loop-guard stops; no timeouts. | v0.05 unchanged; compact instructions v1 |
| Sep 9, 21:43–21:45 | [Qwen single worker · thinking off](docs/results/qwen-single-worker.md) | Qwen3.8 DFlash2 · thinking off | **3/3 accepted, 7/7 each**; 41.5s, 47.9s, 72.2s. One worker owns both tasks. | Not run; preceding PI pair took 146.7s for 7/7 | None; single-worker v1 |
| Sep 9, 21:36–21:37 | [Qwen thinking off · ordinary follow-up](docs/results/qwen-ordinary-thinking-off.md) | Qwen3.8 DFlash2 · thinking off | **0/1 accepted, 0/7 in 44s**; migration broke already-finished consumer imports. No timeouts. | Preceding same-profile PI project: **7/7 in 2m 27s**; one run per condition | None in ordinary; preceding PI v0.05 |
| Sep 9, 21:29–21:32 | [Qwen thinking off · one project](docs/results/qwen-thinking-off.md) | Qwen3.8 DFlash2 · thinking off | Not run | **1/1 accepted, 7/7 in 2m 27s**; zero reasoning tokens, no timeouts. One duplicate repair attempt rejected by native edit guard. | v0.05 unchanged; profile v1, confidence off |
| Sep 9, 21:14–21:22 | [Qwen confidence prompt · one project](docs/results/qwen-confidence.md) | Qwen3.8 DFlash2 · Medium, thinking on | Not run | **0/1 accepted, 0/7**; both workers finished. Stale consumer imports; producer left known break unresolved. Extended deliberation persisted. | v0.05 unchanged; profile v1, confidence on |
| Sep 9, 20:04–20:45 | [Qwen Code · original seven seams](docs/results/qwen-seven-seams.md) | Qwen3.8 DFlash2 · Medium | **3/3 accepted**, 7/7 each | **2/3 accepted**, 7/7, 6/7, 7/7; stale Contacts name in C2. All 12 workers finished, no timeouts. | v0.05 unchanged; Qwen session adaptation |
| Sep 9, 12:47–18:00 | [Qwen Code · distributed candidate 2](docs/results/qwen-distributed.md) | Qwen3.8 DFlash2 · thinking / server XHigh | **0/5 accepted**, scores 4, 6, 7, 5, 5 out of 15 | **0/5 accepted**, scores 4, 7, 5, 5, 5. 35/40 workers timed out across arms; PI enrollment incomplete. | v0.05 unchanged; Qwen-specific session instructions |
| Sep 9, 09:46–10:25 | [Distributed coherence · candidate 2 calibration](docs/results/sol-distributed.md#candidate-2--implementation-defined-return-contracts) | Sol Medium | **3/3 accepted**, 15/15 contracts; four retained implementations each | Not run: both allowed candidates saturated; bounded calibration stopped | v0.05 frozen, not executed |
| Sep 9, 08:51–09:21 | [Distributed coherence · candidate 1 calibration](docs/results/sol-distributed.md#candidate-1--prescribed-internal-contracts) | Sol Medium | Four fixed-role workers: **3/3 accepted**, 12/12 contracts each; four distinct retained implementations each | Not run: ordinary calibration saturated. Candidate 2 subsequently tested implementation-defined internal contracts. | v0.05 frozen, not executed |
| Sep 9, 07:31–08:18 | [PI protocol competence calibration](docs/results/sol-protocol.md) | Sol Medium | Not applicable: deterministic protocol scenarios, not software A/B | **8/9 completed workflows**; one reporting/release timeout. Qualified for software calibration, not error-free operation. | v0.05 unchanged |
| Sep 9, 05:51–06:07 | [Same objective, self-organizing workers](docs/results/self-organizing.md) | Luna Medium | Single: **3/3 accepted**; three workers: **3/3** | Single: **3/3**; three workers: **3/3**. Neither concurrent arm divided implementation usefully. | v0.05 |
| Sep 9, 05:47 | [Self-organizing v3 infrastructure abort](docs/results/self-organizing.md#integrity-failures-and-limits) | Luna Medium requested | One launch stopped after **99.125s**, no recorded coding output; source 0/7 | Not launched | v0.05 frozen, not executed |
| Sep 9, 04:56–05:18 | [Concurrency versus context](docs/results/concurrency.md) | Luna Medium | Single: **3/3 accepted**; two workers: **3/3** | Single: **3/3**; two workers: **3/3**. Distinct retained parallel contributions: **3/3 PI vs 0/3 ordinary**. | v0.05 |
| Sep 9, 04:33 | [Refund torture · PI](docs/results/refunds.md) | Luna Medium | Earlier matched fixture batch below | **0/7, 7/7, 7/7** | v0.05 |
| Sep 9, 04:24 | [Refund torture · ordinary](docs/results/refunds.md) | Luna Medium | **0/7, 6/7, 6/7** | Subsequently tested above | None |
| Sep 9, 04:16 | [Refund torture · higher effort](docs/results/refunds.md#luna-high-baseline) | Luna High | **7/7**, one project | Not run | None |
| Sep 9, 03:57 | [Original seven seams · stronger reasoning](docs/results/seven-seams.md) | Sol Medium; Sol High | Medium: **7/7, 7/7**; High: **7/7, 7/7** | Not run | None |
| Sep 9, 03:53 | [Original seven seams · A/B/C ordinary B](docs/results/seven-seams.md#low-effort-abc-comparison) | Sol Low | **3/7, 4/7, 3/7** | See Luna + PI configuration C below | None |
| Sep 9, 03:38 | [Original seven seams · A/B/C ordinary A](docs/results/seven-seams.md#low-effort-abc-comparison) | Luna Low | **0/7, 2/7** | See configuration C below | None |
| Sep 9, 03:32 | [Original seven seams · A/B/C configuration C](docs/results/seven-seams.md#low-effort-abc-comparison) | Luna Low | Subsequently tested above | **7/7, 7/7** | v0.05 |
| Sep 9, 03:17 | [Original seven seams · Spark XHigh](docs/results/seven-seams.md) | Spark XHigh | Not run | **3/7, 3/7, 0/7** | v0.05 |
| Sep 9, 03:11 | [Original seven seams · context refresh](docs/results/seven-seams.md) | Luna Medium; Spark Medium | Not run | Luna: **7/7, 7/7, 7/7**; Spark: **0/7, 3/7, 0/7** | **v0.05: backend changed** |
| Sep 9, 02:52 | [Original seven seams · initial batch](docs/results/seven-seams.md) | Luna Medium; Spark Medium | Not run | Luna: **7/7, 7/7, 7/7**; Spark: **0/7, 0/7, 3/7** | v0.04 |
| Sep 9, 01:52–01:57 | [Repair coordination · stopped batch](docs/results/early-studies.md) | Luna Medium | Not run | Three completed two-worker trials, **acceptance unscored**; fourth interrupted; fifth never started | v0.03 |
| Sep 9, 01:14–01:17 | [Onboarding recovery · two pairs](docs/results/early-studies.md) | Luna Medium | **2/2** preserve both tasks | **2/2** preserve both tasks; all four PI workers enrolled | **v0.02: backend changed** |
| Sep 8 | [Unchanged microstudy · ten more pairs, 4–13](docs/results/early-studies.md) | Luna Medium | **8/10** preserve both tasks | **7/10** preserve both tasks | v0.01 |
| Sep 8 | [Unchanged microstudy · repeats 1–3](docs/results/early-studies.md) | Luna Medium | **2/3** preserve both tasks | **2/3** preserve both tasks | v0.01 |
| Sep 8 | [Microstudy · label pilot and preceding pilots](docs/results/early-studies.md) | Luna Medium | Label pilot correct; different-task/launch attempts separate | Label pilot incorrect; other attempts separate | v0.01 |

Scores listed together in this overview follow **trial-number order**; linked
per-run ledgers provide execution chronology. The original seven seams and refund
torture are different fixtures. Their seven-point scores must not be pooled.
The earlier Status/release cases have been removed from this catalog and the
active experiment suite because their harness supplied coordination to the control.
Their original history remains recoverable; native failures and ties remain above.

## The low-effort A/B/C breakthrough

| Configuration | Accepted | Integrated scores |
| --- | ---: | --- |
| A — Luna Low, ordinary | 0/2 | 0/7, 2/7 |
| B — Sol Low, ordinary | 0/3 | 3/7, 4/7, 3/7 |
| C — Luna Low + PI v0.05 | **2/2** | **7/7, 7/7** |

**Luna Low with PI outperformed both ordinary configurations on integrated
correctness, including the stronger Sol model.** This compares adding PI to a
lower-capability configuration with increasing model capability without it. It
does not combine the configurations into one statistical average.

The next research question was not another Sol-plus-PI run: it was whether PI's
value comes from supplying useful peer context, coordinating concurrent work, or
both. The later studies below equalized task information and added single-worker
baselines. [Individual failures and timings](docs/results/seven-seams.md).

## Bounded calibration: capable workers, harder distributed work

Sol Medium completed **8/9** explicitly requested PI workflows within five minutes:
audits **3/3**, repair owners **3/3**, reviewing peers **2/3**. One reviewer timed out
after a reporting-command rejection; successful runs also exposed transcription
friction. This passes the frozen bounded gate, not a claim of perfect protocol use.

**Suspected limit in the preceding software studies:** low-effort failures can mix
coding difficulty with PI workflow difficulty, while the original fixture saturates
at higher capability. **The first software calibration examined** four independently
owned components with fixed, equal assignments, using Sol Medium throughout.
All three ordinary projects passed all twelve integration groups and retained
four distinct component implementations. **Suspected limit:** fully prescribed
internal contracts allowed independent implementation without much reconciliation.
**Candidate 2 tested** producer-defined internal payloads under equally visible,
fixed business requirements: **3/3 ordinary projects accepted all fifteen groups**.
Both allowed candidates saturated, so execution stopped before the single-worker
ceiling and matched PI evaluation. **Possible limit:** normal inspection still
resolved the available seams without difficult reconciliation. A future separately
authorized version should test unresolved semantic evolution, not weaken Sol or
cripple ordinary tools. No PI software effect is measured here.
[Software results](docs/results/sol-distributed.md) · [Protocol evidence](docs/results/sol-protocol.md) ·
[Frozen software-study plan](docs/CLI_SOL_DISTRIBUTED_SOFTWARE.md).

## Qwen steering ten-repeat cohort

**Ten fresh projects, ten accepted results, 7/7 every time.** This September 10
cohort repeated the successful seven-seam steering pilot with native Qwen Code,
model `qwen38-27b-dflash2`, thinking off, confidence off and PI/steering on.
Projects ran sequentially, with two concurrent role workers inside each project.
The pilot is separate and is not counted as one of these ten repeats.

There **is an earlier ordinary control**: [thinking-off B1](docs/results/qwen-ordinary-thinking-off.md)
on September 9 scored **0/7 in 44.072s**, with PI absent and both workers exiting
normally. Its frozen fixture and runtime manifests, producer/consumer prompts,
common task input and checker hashes match the ten-repeat cohort's first project;
model, context window and timeout match too. Thinking and confidence were off in
both. The repeat wrapper verifies the same treatment across the ten PI projects.

| Comparison | Projects accepted | Integrated scores | Project time |
| --- | --- | --- | --- |
| Earlier ordinary control, no PI | **0/1** | 0/7 | 44.072s, unaccepted |
| Subsequent PI + steering repeats | **10/10** | 7/7 each | Median 99.444s |

This is a **one-versus-ten historical comparison**, not ten newly paired control
runs. PI availability, compact instructions, filtered CLI and automatic steering
are a combined treatment; this comparison does not isolate steering alone. The
ordinary failure is not a faster accepted solution. The earlier PI-only thinking-off
run also passed 7/7, as recorded on the linked control page.

| Trial | Integrated score | Accepted | Project seconds |
| --- | ---: | --- | ---: |
| T01 | 7/7 | Yes | 303.185 |
| T02 | 7/7 | Yes | 105.218 |
| T03 | 7/7 | Yes | 114.269 |
| T04 | 7/7 | Yes | 94.821 |
| T05 | 7/7 | Yes | 82.371 |
| T06 | 7/7 | Yes | 133.303 |
| T07 | 7/7 | Yes | 98.036 |
| T08 | 7/7 | Yes | 100.851 |
| T09 | 7/7 | Yes | 48.037 |
| T10 | 7/7 | Yes | 73.076 |

Median project time was **99.444s**. This establishes repeated accepted outcomes
on this fixture with steering enabled, alongside a failed earlier ordinary control.
The single control run cannot estimate ordinary reliability, and these experiments
do not isolate steering's causal effect or establish reliability on different
projects. Acceptance was checked after worker exit;
project time is not time to the first correct intermediate state.

Source: the ten project `result.json` records and `completed.json` in local batch
`20260910-qwen-steering-repeat-v1`, inspected September 11. The completion receipt
records ten projects at `2026-09-10T00:44:42.876069+00:00`. These are summaries of
recorded outcomes, not newly executed trials or a full transcript/provenance audit.
[Frozen cohort method](docs/CLI_QWEN_STEERING.md#ten-repeat-stability-cohort) ·
[Original pilot](docs/results/qwen-steering.md).

## Qwen distributed 500-limit follow-ups

The harder distributed candidate 2 reached **15/15 artifact acceptance** after
the native tool-call and session-turn allowances were both set to 500. These
were three separate fresh four-worker projects, not repairs or resumes of one
failed checkout. All used `qwen38-27b-dflash2`, thinking off and PI/steering on.

| Fresh project | Native limit change | Integrated score | Artifact accepted | Project seconds |
| --- | --- | ---: | --- | ---: |
| Initial distributed steering | Initial native limits | 8/15 | No | 844.115 |
| cap500 | Tool calls per turn set to 500 | 14/15 | No | 1,076.096 |
| cap500-turn500 | Session turns raised from 150 to 500; call cap stays 500 | **15/15** | **Yes** | **795.062** |

The cap500 run failed `partial_return_pipeline`. The final run passed all fifteen
groups in **13m 15s**, but its reporting worker exited with code **1**; the other
three workers exited 0. Its recorder therefore retained **`accepted=true` and
`autonomous_complete=false`**. Correct final source and clean worker execution
are separate outcomes; do not erase either fact.

The changes were to **native execution allowances**, not to the notification
budget: the steering hook still allowed **12 notices per worker**. Three fresh
runs show this observed progression, not proof that the limit changes alone
caused it. There was no newly matched ordinary control for these pilots. The
earlier seven-seam cohort and this fifteen-group fixture must not be pooled.

Source: project `C1/result.json` and frozen plans in local batches
`20260910-qwen-distributed-steering-v1`, `20260910-qwen-distributed-cap500-v1`
and `20260910-qwen-distributed-turn500-v1`, inspected September 11. No original
results or frozen inputs were changed, and no models were rerun for this summary.
[Versioned methods and limit changes](docs/CLI_QWEN_DISTRIBUTED_STEERING.md).

## Latest Qwen follow-up: independent requests

The September 10 study-owner summary records **3/3 ordinary projects accepted**,
versus **1/3 with PI and steering**. The other two PI projects reached 13/15 at
the 30-minute worker boundary. Workers noticed peers but did not establish a PI
repair agreement. This is not evidence of a reliable PI advantage or proof that
PI caused the failures. [Recorded outcomes and evidence limits](docs/results/qwen-independent-requests.md).
The [proposed follow-up](docs/QWEN_STEERING_BACKLOG.md) remains on hold.
This later comparison changed to three different worker requests and already
used **500 tool calls per turn and 500 session turns**. It does not replace the
earlier ten-repeat success or the accepted four-worker distributed artifact.

## Earlier Qwen Code distributed comparison: no PI win

The requested five ordinary and five PI projects ran through native **Qwen Code
0.23.2**, with 230k context and thinking enabled, on distributed candidate 2.
Neither arm produced an accepted project; both had a median **5/15** score.
Projects ran sequentially, with four concurrent role workers inside each project.

**Possible limit:** 35/40 workers hit the 30-minute limit, native stream/reasoning
behavior constrained useful output, and only 7/20 PI workers initially enrolled.
**Next test should separate** native Qwen/tool throughput and PI protocol reliability
from coordination before another frozen comparison. The subsequent fleet recovery
and recorder-v2 fixes do not change this cohort's treatment or results.
[Every project, measured timelines and limitations →](docs/results/qwen-distributed.md)

## Earlier identical-objective comparison

Luna Medium, original fixture, identical complete objective for every worker.
Three fresh projects per condition; **all reached 7/7**. Time and token columns
are medians of per-project totals, not sums across repetitions.

| Condition | Accepted | Final project time | Worker-s | Tokens | Useful implementation split |
| --- | ---: | ---: | ---: | ---: | --- |
| One ordinary worker | 3/3 | **53.4s** | **53.4** | **105,244** | Not applicable |
| Three ordinary workers | 3/3 | 72.3s | 182.7 | 422,657 | 0/3 |
| Three PI workers | 3/3 | 101.7s | 276.2 | 991,981 | 0/3 |
| One PI worker, secondary | 3/3 | 86.1s | 86.0 | 295,317 | Not applicable |

One worker implemented the entire project in every run. The ordinary concurrent
arm discarded six stale full-project patches; PI discarded five. That single
episode difference across three projects is not a reliable duplication win.
The first verified durable 7/7 medians were **43.7s, 41.3s, 63.2s and 63.2s**,
respectively; final completion tails are not the same as first correctness.

**Suspected limit:** the task was short enough for one complete implementation,
and broad declarations did not become an agreed division of responsibility.
**Proposed next test:** a longer task with independently checkable contributions,
equal task information and no prescribed allocation, measuring whether useful
decomposition happens before redundant implementation. It has not been run.

[Full results, per-worker effort, PI overhead and measured timelines →](docs/results/self-organizing.md)

## What the preceding split-role study adds

With a predefined producer/consumer split, all Luna Medium arms again passed 3/3.
The PI pairs retained distinct contributions while both workers were active in
**3/3 projects**, versus **0/3 ordinary pairs**. PI pairs had no peer-stale patch
failures or peer-label rewrites; ordinary pairs had three and two, respectively.

That behavior did **not** produce a completion-time advantage. Median final project
times were single ordinary **81.6s**, ordinary pair **99.6s**, PI pair **141.4s**,
single PI **118.3s**. PI still required two demonstrated day-format integration
corrections and one self-inflicted cleanup-patch recovery.

**Suspected limit:** predefined roles supported distinct contributions, but the
short serial task could not repay coordination overhead. **Next completed test:**
the identical-objective study removed the predefined split; it did not produce
useful implementation decomposition. [Full split-role report](docs/results/concurrency.md).

## PI behavior versions

These are **retrospective research labels**, not package versions or claims about
which release was live on port 8290. A trial can test a frozen candidate before its
commit or activation. Fixture/recorder suffixes such as `v1`–`v4` are a separate axis.

| Behavior stage | Source identity | What changed |
| --- | --- | --- |
| **v0.05** | Candidate core `99ca17a18d28…`; later committed in [`ac1b691`](https://github.com/meanaverage/sayhi-project-intent/commit/ac1b69195cfc0fe532b57ab90741cc7a86f0c055), merged as `e384223` | Added related-task integration context before enrollment and retained released/expired peer summaries, plus refresh guidance. Used from seven-seam batch 2 through both latest studies. |
| **v0.04** | Frozen seven-seam batch-1 core `7b2a368931ce…` | Explicit named-peer acknowledgment and path-bounded repair agreement; did not yet include the later integration-context function. |
| **v0.03** | Frozen `seam-repair-b-v3` candidate | First local repair-claim candidate. Stopped trials exposed stale deferral and incomplete agreement behavior; not silently relabeled as v0.04. |
| **v0.02** | [`b896b73`](https://github.com/meanaverage/sayhi-project-intent/commit/b896b7360ceff0c7c153cb07995ad13e551cedf0), subsequently merged through `ace04ef` | Ranked partial discovery, scoped inventory recovery and clearer enrollment/instruction flow. |
| **v0.01** | `86ffbc5504dca87e5ed1ea1b2eabb8ac3383e5cb` baseline | Scoped onboarding/presence and task registration before the recovery and repair changes. |

Full backend and workflow fingerprints are in [measurements.json](docs/results/measurements.json).
Backend fingerprints cover sorted Python module SHA-256 values; skill/workflow
fingerprints are separate. Changing a README, fixture or sandbox does not by itself
increment PI behavior. The code did not change mid-study to improve a result.

## How to read the evidence

- **Accepted:** original seven seams require both producer and consumer checks in
  all seven groups. Refund torture uses its distinct seven-group checker. Early
  microstudies require both tasks to survive; unscored repair trials remain unscored.
- **Wall time:** recent project time runs from first native launch through final
  post-exit verification. Earlier seven-seam/refund tables report the worker window
  only, excluding later scoring. We do not sum workers to obtain project time.
- **Tokens:** input plus output; cached input and reasoning output are subsets.
  Counts include final verification/handoff tails inside workers, not exact compute
  stopped at first correctness. Tokens are not measured GPU compute or dollars.
- **PI overhead:** reports include onboarding, enrollment, refreshes and shell
  friction. Mixed PI-tagged tool-call time includes ordinary shell work; neither
  that time nor whole-request token counts cleanly isolates PI-only cost.
- **Fairness:** older PI arms exposed peer task context and broader docs; the later
  concurrency study equalized available tasks. Self-organization additionally
  gave all arms a committed Git baseline, visible unchanged checker and isolated
  native profiles. Do not pool these designs into one success percentage.
- **Failures and preparations:** concurrency v1 and self-organizing v1/v2 failed
  preflight without model trials. Self-organizing v3's one DNS-failed launch was
  explicitly stopped and archived; v4 corrected infrastructure before refreezing.
  Older invalidated, unscored and stopped attempts are in the historical ledger.
- **Privacy and reproducibility:** public summaries retain archive IDs and source
  hashes. Raw native conversations, authentication, registrations, runtime state
  and private paths stay outside Git. The reviewed fixtures, checkers, recorders
  and unit tests are tracked; publication does not authorize another model run.

## Source and detailed reports

| Report | Protocol / source |
| --- | --- |
| [Self-organization](docs/results/self-organizing.md) | [Protocol](docs/CLI_SEVEN_SEAMS_SELF_ORGANIZING.md) · [recorder](experiments/seven_seams_self_organizing.py) |
| [Concurrency versus context](docs/results/concurrency.md) | [Protocol](docs/CLI_CONCURRENCY_STUDY.md) · [recorder](experiments/concurrency_study.py) |
| [Refund torture](docs/results/refunds.md) | [Protocol](docs/CLI_TORTURE_REFUNDS.md) · [fixture](experiments/torture_refunds/fixture) · [checker](experiments/torture_refunds_check.py) |
| [Original seven-seam history](docs/results/seven-seams.md) | [Protocol](docs/CLI_SEVEN_SEAMS.md) · [fixture](experiments/seven_seams/fixture) · [checker](experiments/seven_seams_check.py) |
| [Native microstudy and repair attempts](docs/results/early-studies.md) | [Microstudy](docs/CLI_AB_SEAM_MICRO.md) · [withdrawal policy](docs/CLI_AB_EVALUATION.md#withdrawn-coached-controls) |

This is an exploratory evidence record. The aim is to learn where shared project
state makes concurrent development useful, not to select only results that favor PI.
