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

## Latest completed project-level comparison

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
