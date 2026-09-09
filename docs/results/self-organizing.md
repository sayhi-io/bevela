# Seven-seam self-organizing study — Luna medium, v4

[All results](../../RESULTS.md) · [Measurements](measurements.json)

PI behavior **v0.05** · frozen core `e384223` · fixture/recorder study v4.
Public editorial copy of the completed report; original evidence is unchanged. Run tables are newest-first by actual launch, not by arm label. Raw streams and private execution records stay outside Git.

Original fixture, not refund torture. Three repetitions per arm; identical complete objective for every worker; no assigned producer/consumer roles. Values below are medians per project; duplicate episodes are totals across the three repetitions. “Project time” is the frozen primary endpoint: launch through final verification after all workers exit. First verified accepted-checkout time is reported separately immediately below.

| Condition | Runs | 7/7 | Median project time | Aggregate worker time | Aggregate tokens | Useful implementation decomposition | Duplicate work | Human intervention |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Single worker | 3 | 3/3 | 53.4s | 53.4s | 105,244 | n/a | n/a | 0 |
| 3 ordinary concurrent | 3 | 3/3 | 72.3s | 182.7s | 422,657 | 0/3 runs | 6 rejected whole-project patches | 0 |
| 3 PI concurrent | 3 | 3/3 | 101.7s | 276.2s | 991,981 | 0/3 runs | 5 rejected whole-project patches | 0 |
| Single worker + PI (secondary) | 3 | 3/3 | 86.1s | 86.0s | 295,317 | n/a | n/a | 0 |

**Bottom line:** PI did not produce useful self-organized parallel implementation here. Every project was solved by one worker implementing all nine source files. The other workers mostly drafted duplicate solutions, then inspected or refined the surviving implementation. PI made peers visible and briefly changed roles in C1, but did not yield stable seam allocation.

## Accepted-result timing, not just worker completion

| Condition | Median first verified durable 7/7 | Median sampled source first durable 7/7 | Median all-workers-finished final verification |
| --- | --- | --- | --- |
| Single worker | 43.7s | 41.3s | 53.4s |
| 3 ordinary concurrent | 41.3s | 38.6s | 72.3s |
| 3 PI concurrent | 63.2s | 59.2s | 101.7s |
| Single worker + PI (secondary) | 63.2s | 60.9s | 86.1s |

First verified durable 7/7 uses actual native tool-call completion timestamps for successful unchanged-checker executions, with subsequent sampled source states also passing through final verification. These are measured upper bounds, not the instant a shell printed its last byte. Source replay is retrospective 100ms sampling, not live feedback or an atomic write journal.

Ordinary concurrency reached its first accepted checkout about 2.4s earlier by median than single-worker execution, but ranges overlap (39.4–45.4s versus 41.8–45.5s). This is redundant racing, not division of work; three observations do not establish a reliable speedup. Three PI workers and one PI worker reached first accepted results at essentially the same median time (63.2s). The larger C completion tail must not be mistaken for later initial correctness.

## Every run

| Run | Final score | Producer / consumer | Failed seams | First verified 7/7 | Final project time | Worker-seconds | Tokens | Concurrency factor | Stale duplicate patches | Intervention |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D3 | 7/7 | 7/7 / 7/7 | none | 67.1s | 86.1s | 86.0 | 258,661 | 1.00 | 0 | 0 |
| D2 | 7/7 | 7/7 / 7/7 | none | 63.2s | 81.8s | 81.8 | 304,520 | 1.00 | 0 | 0 |
| D1 | 7/7 | 7/7 / 7/7 | none | 62.1s | 99.6s | 99.6 | 295,317 | 1.00 | 0 | 0 |
| A3 | 7/7 | 7/7 / 7/7 | none | 45.5s | 54.7s | 54.7 | 121,109 | 1.00 | 0 | 0 |
| C3 | 7/7 | 7/7 / 7/7 | none | 62.2s | 101.7s | 276.2 | 991,981 | 2.72 | 2 | 0 |
| B3 | 7/7 | 7/7 / 7/7 | none | 45.4s | 63.8s | 178.6 | 383,688 | 2.80 | 2 | 0 |
| B2 | 7/7 | 7/7 / 7/7 | none | 39.4s | 72.3s | 182.7 | 422,657 | 2.53 | 2 | 0 |
| A2 | 7/7 | 7/7 / 7/7 | none | 43.7s | 53.4s | 53.4 | 105,244 | 1.00 | 0 | 0 |
| C2 | 7/7 | 7/7 / 7/7 | none | 63.2s | 95.3s | 267.9 | 938,370 | 2.81 | 2 | 0 |
| C1 | 7/7 | 7/7 / 7/7 | none | 64.3s | 112.5s | 282.5 | 1,115,114 | 2.51 | 1 | 0 |
| B1 | 7/7 | 7/7 / 7/7 | none | 41.3s | 84.5s | 197.4 | 426,871 | 2.34 | 2 | 0 |
| A1 | 7/7 | 7/7 / 7/7 | none | 41.8s | 49.7s | 49.7 | 104,807 | 1.00 | 0 | 0 |

Every v4 run exited normally and passed without intervention; no retries, replacement runs, timeouts, checker changes or final false-completion claims were observed. Early baseline failures were not completion claims. No model/effort strata are pooled.

| Separate infrastructure attempt | Source score | Duration | Reported tokens | Intervention | Disposition |
| --- | --- | --- | --- | --- | --- |
| v3 A1 | 0/7 | 99.125s | unavailable | 1 | DNS isolation failure; explicitly stopped, archived, excluded from model comparison |

V3 produced no recorded coding output. This failed launch is not hidden or counted as a successful repetition; its complete record remains alongside the newly frozen v4 study.

## Measured representative execution timelines

Representative = median final-project-duration run in each arm. Bars show native process activity (including inference latency, tools and waiting), not continuous reasoning or useful coding.

```text
Single worker — A2
worker1  0.000s ├───────────────────────────┤ 53.383s
 41.256s  worker1 edits all nine source files
 43.693s  first verified durable 7/7
 53.406s  final quiescent verification: 7/7
```

```text
3 ordinary concurrent — B2
worker1  0.001s ├──────────────────────────┤ 51.440s
worker2  0.001s ├─────────────────────────────┤ 58.991s
worker3  0.000s ├────────────────────────────────────┤ 72.262s
 36.109s  worker1 edits all nine source files
 39.375s  worker2 stale whole-project patch rejected
 39.397s  first verified durable 7/7
 42.409s  worker3 stale whole-project patch rejected
 51.480s  worker2 edits delivery.py
 72.303s  final quiescent verification: 7/7
```

```text
3 PI concurrent — C3
worker1  0.000s ├───────────────────────────────────────────────────┤ 101.706s
worker2  0.001s ├────────────────────────────────────────────┤ 88.442s
worker3  0.000s ├───────────────────────────────────────────┤ 86.020s
 59.042s  worker3 edits all nine source files
 61.770s  worker2 stale whole-project patch rejected
 62.199s  first verified durable 7/7
 67.276s  worker1 stale whole-project patch rejected
 74.400s  worker3 edits delivery.py
101.732s  final quiescent verification: 7/7
```

```text
Single worker + PI (secondary) — D3
worker1  0.000s ├───────────────────────────────────────────┤ 86.026s
 63.673s  worker1 edits all nine source files
 67.076s  first verified durable 7/7
 86.068s  final quiescent verification: 7/7
```

## Emergent allocation, duplication and rework

- No worker-created allocation/coordination file, seam partition, explicit agreed ownership split or repair agreement appeared. No required work remained unowned at final acceptance.
- In every A/D run the single worker implemented the entire objective. In B1/B2/B3 worker1 implemented all nine source files; in C1 worker1 did so; in C2/C3 worker3 did so.
- All other B workers attempted the same full migration first. In C2/C3 both losing workers also attempted the full migration despite seeing broad peer declarations. C1 worker2 changed to verification after seeing overlap and never attempted a patch; C1 worker3 changed to verification, then changed back after a short observation window and attempted a stale full patch.
- B had six discarded whole-project patch attempts; C had five. All eleven failed on the original `catalog.PRICES` line after a peer had already migrated it. The native patch tool rejected the stale edit; the experiment did not inject a coordinator or edit barrier.
- Successful peer rewrites after acceptance: B1 worker2 changed delivery arithmetic and worker3 refactored presentation imports/discount calculation; B2 worker2 changed delivery arithmetic. These are three retained refinements of already-7/7 code, not independent progress toward unfinished seams. B1 changes occur after prior editors exit; B2 is at the winner’s exit boundary (~40ms later in recorded edit receipt), below sampling precision for a strong non-overlap claim. C had zero peer rewrites; C1/C3 winners refined their own delivery helpers.
- No observed acceptance-breaking integrated regression, obsolete test addition, successful competing repair, integration discard, or checker-triggered regression repair occurred. Rejected attempts caused reinspection and repeated validation, not broken final repositories. B2 worker3 described peer changes as a partially applied patch, but its patch failed at the first catalog check and it recorded no successful edit; that statement is not evidence of ownership.
- Harmless duplicate initial inspection is separate: all concurrent workers inspected the same objective/source. Subsequent inspections after failed patches reconstructed an already solved contract. Verification overlapped in time, but peers did not discover an unmet acceptance condition or establish the first 7/7 ahead of the implementing worker.
- Time to useful implementation decomposition: not reached in any B/C trial. Stable explicit ownership: not established. C1’s tentative implementation/verification distinction was not a division of unfinished implementation and did not persist for its third worker. Exact duplicate-effort/token ratios are unavailable; count concrete discarded patches instead.

### Per-worker actions and compute

All first implementation attempts covered the complete nine-file migration except C1 worker2 (verification only); C1 worker3 initially chose verification before attempting the full migration. Times are seconds from that project’s first launch. Cached input and reasoning output are subsets of input/output, not extra tokens. Counts use the last cumulative native usage sample.

| Run / worker | Start–end (s) | Native duration | Input | Cached input | Output | Reasoning | Tool calls | Successful files | Rejected patches |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D3 / worker1 | 0.000–86.026 | 86.026 | 254,987 | 221,952 | 3,674 | 521 | 8 | all nine | 0 |
| D2 / worker1 | 0.000–81.768 | 81.768 | 300,850 | 260,096 | 3,670 | 430 | 11 | all nine | 0 |
| D1 / worker1 | 0.000–99.587 | 99.587 | 291,675 | 259,328 | 3,642 | 224 | 10 | all nine | 0 |
| A3 / worker1 | 0.000–54.684 | 54.684 | 118,743 | 88,320 | 2,366 | 294 | 6 | all nine | 0 |
| C3 / worker1 | 0.000–101.706 | 101.706 | 383,443 | 334,336 | 4,440 | 910 | 13 | none | 1 |
| C3 / worker2 | 0.001–88.442 | 88.441 | 335,586 | 290,048 | 3,702 | 470 | 10 | none | 1 |
| C3 / worker3 | 0.000–86.020 | 86.020 | 261,062 | 215,808 | 3,748 | 643 | 8 | all nine | 0 |
| B3 / worker1 | 0.000–53.239 | 53.239 | 103,107 | 82,432 | 2,342 | 380 | 5 | all nine | 0 |
| B3 / worker2 | 0.001–63.753 | 63.752 | 149,022 | 128,000 | 2,754 | 596 | 7 | none | 1 |
| B3 / worker3 | 0.000–61.600 | 61.600 | 123,970 | 102,656 | 2,493 | 429 | 6 | none | 1 |
| B2 / worker1 | 0.001–51.440 | 51.439 | 102,042 | 85,504 | 2,192 | 354 | 5 | all nine | 0 |
| B2 / worker2 | 0.001–58.991 | 58.990 | 146,759 | 129,024 | 2,550 | 353 | 7 | delivery.py | 1 |
| B2 / worker3 | 0.000–72.262 | 72.262 | 166,037 | 134,912 | 3,077 | 778 | 8 | none | 1 |
| A2 / worker1 | 0.000–53.383 | 53.383 | 102,925 | 86,528 | 2,319 | 311 | 5 | all nine | 0 |
| C2 / worker1 | 0.000–95.302 | 95.302 | 321,183 | 270,592 | 3,900 | 503 | 10 | none | 1 |
| C2 / worker2 | 0.001–87.587 | 87.586 | 337,026 | 281,600 | 3,484 | 510 | 11 | none | 1 |
| C2 / worker3 | 0.001–84.980 | 84.979 | 268,947 | 220,672 | 3,830 | 661 | 9 | all nine | 0 |
| C1 / worker1 | 0.000–89.221 | 89.221 | 331,078 | 271,360 | 3,851 | 619 | 11 | all nine | 0 |
| C1 / worker2 | 0.000–80.826 | 80.826 | 371,114 | 297,216 | 2,682 | 507 | 10 | none | 0 |
| C1 / worker3 | 0.001–112.414 | 112.413 | 401,933 | 356,096 | 4,456 | 911 | 12 | none | 1 |
| B1 / worker1 | 0.001–50.527 | 50.526 | 102,592 | 87,552 | 2,185 | 209 | 5 | all nine | 0 |
| B1 / worker2 | 0.000–62.395 | 62.395 | 144,564 | 117,760 | 2,786 | 613 | 7 | delivery.py | 1 |
| B1 / worker3 | 0.000–84.481 | 84.481 | 170,932 | 140,032 | 3,812 | 1174 | 8 | presentation.py | 1 |
| A1 / worker1 | 0.000–49.685 | 49.685 | 102,636 | 84,480 | 2,171 | 207 | 5 | all nine | 0 |

Maximum simultaneously active workers: A/D one; B/C three. Maximum start skew was 1.289ms. Concurrency factor measures overlapping native processes, not productive decomposition. No extra/delegated native sessions were found. No precise allocation of model tokens to particular edits, waiting, or discarded code is observable.
Token totals include each worker’s complete execution, including work after the first passing checker. They are not an exact token counter stopped at the first accepted instant; concurrent in-flight reasoning cannot be phase-attributed from final cumulative telemetry.

## PI operations and overhead

| Condition | Successful onboard calls | Active / inactive enroll calls | Context refreshes | Repair claim/ack/complete | Failed PI-shell commands |
| --- | --- | --- | --- | --- | --- |
| C (nine workers) | 18 | 9 / 9 | 11 | 0 / 0 / 0 | 0 |
| D (three workers) | 6 | 3 / 3 | 3 | 0 / 0 / 0 | 1 |

Every PI worker completed enrollment using its own native session and released it. Declarations were broad full-project file/seam scopes; they did not become a seam allocation. No provider/live production calls were required; treatment was the frozen supported local snapshot/cooperative-presence workflow, not a production dispatcher.

| Run | Median launch→enrolled | Median observed onboarding span | PI-tagged tool-call wall sum | PI-tagged output bytes | Failures |
| --- | --- | --- | --- | --- | --- |
| D3 | 33.14s | 19.15s | 0.703s | 65,158 | 0 |
| D2 | 29.29s | 21.11s | 0.846s | 64,970 | 1 |
| D1 | 25.84s | 17.49s | 0.790s | 54,970 | 0 |
| C3 | 31.39s | 19.61s | 2.245s | 261,666 | 0 |
| C2 | 27.92s | 17.64s | 2.288s | 243,062 | 0 |
| C1 | 29.32s | 18.95s | 10.430s | 244,352 | 0 |

Median enrollment was 29.3s after launch in both C and D. PI-tagged tool time includes mixed shell work and is not pure CLI latency: C1 includes an explicit 8-second worker-chosen sleep inside a refresh call. Output bytes are mixed context/tool output, not PI-only tokens. The launch-to-enrollment span includes reasoning, ordinary inspection and model latency; it is not all API cost. Exact PI-specific token contribution cannot be separated reliably.

D2 quoted the entire multiword Python CLI prefix as one executable, received shell exit 127, then corrected the invocation and enrolled. This is friction in the frozen study CLI-prefix presentation/shell use, not evidence of a PI engine outage. No PI implementation was repaired during this study. The one fewer C duplicate episode is not reliable evidence of reduced duplication at n=3, especially because C2/C3 duplicated as much as the ordinary arm.

## Timing sections and total study cost

| Run | Setup (s) | Worker window (s) | Archive (s) | Final verification (s) | External repair (s) |
| --- | --- | --- | --- | --- | --- |
| D3 | 0.0191 | 86.0264 | 0.0040 | 0.0365 | 0 |
| D2 | 0.0281 | 81.7680 | 0.0039 | 0.0207 | 0 |
| D1 | 0.0280 | 99.5865 | 0.0041 | 0.0203 | 0 |
| A3 | 0.0127 | 54.6843 | 0.0018 | 0.0199 | 0 |
| C3 | 0.0271 | 101.7064 | 0.0042 | 0.0206 | 0 |
| B3 | 0.0167 | 63.7528 | 0.0019 | 0.0208 | 0 |
| B2 | 0.0136 | 72.2620 | 0.0019 | 0.0379 | 0 |
| A2 | 0.0136 | 53.3827 | 0.0019 | 0.0208 | 0 |
| C2 | 0.0151 | 95.3025 | 0.0042 | 0.0368 | 0 |
| C1 | 0.0196 | 112.4142 | 0.0108 | 0.0364 | 0 |
| B1 | 0.0129 | 84.4808 | 0.0019 | 0.0343 | 0 |
| A1 | 0.0092 | 49.6846 | 0.0018 | 0.0364 | 0 |

In-session inspection/refinement/repair is inside the worker interval and is not added twice. There was no external integration or repair phase. Frozen fixture setup plus per-profile offline/DNS/write preflights took 4.52s; backend catalog preflights are separately recorded in network-preflight.json. Implementation/debugging time and rejected preparations are not presented as model project execution time.

| Condition | Total input | Total cached input | Total output | Total reasoning | Total tokens (3 projects) |
| --- | --- | --- | --- | --- | --- |
| Single worker | 324,304 | 259,328 | 6,856 | 812 | 331,160 |
| 3 ordinary concurrent | 1,209,025 | 1,007,872 | 24,191 | 4,886 | 1,233,216 |
| 3 PI concurrent | 3,011,372 | 2,537,728 | 34,093 | 5,734 | 3,045,465 |
| Single worker + PI (secondary) | 847,512 | 741,376 | 10,986 | 1,175 | 858,498 |

The twelve sequential projects took 956.566s (15m 56.6s) batch wall time, 1810.312 aggregate worker-seconds, and 5,468,339 reported tokens. All these projects were accepted; failed infrastructure cost is separately retained below. No token-only efficiency or price claim is made.

## Research answers

- **Spontaneous useful division?** No seam/file implementation partition emerged in either multi-worker arm. C1 briefly differentiated implementation from verification.
- **Earlier/more reliable decomposition with PI?** Not observed; time-to-useful-implementation-decomposition was unreached in all six multi-worker projects.
- **Less duplicate implementation?** Six discarded full patches without PI versus five with PI. One fewer episode across three projects is weak, inconsistent evidence, not a reliable win.
- **Less conflict/rework?** Five versus six stale patch failures; zero peer rewrites in C versus three post-acceptance refinements in B. Neither arm suffered an accepted-result regression or needed a correctness repair.
- **Better final correctness?** No. Every arm was 3/3 at 7/7. One Luna-medium worker already solved the task; a stronger worker was not needed or tested here.
- **Did useful concurrency reduce project time?** No useful implementation concurrency emerged. Ordinary redundant racing had a small overlapping-range first-pass advantage, but longer completion tails. PI three-worker first acceptance matched single-worker + PI, not a speedup.
- **Compute tradeoff?** Median totals: A 105,244; B 422,657; C 991,981; D 295,317. C spent about 3.36× D aggregate tokens for essentially identical first-acceptance time; all outcomes were equally accepted.
- **What was PI used for?** Discovery, full-scope enrollment, peer awareness, final integration refresh and handoff/release. No seam division or repair claim/ack/complete. The extra context/workflow did not improve correctness here.
- **Concurrency substrate rather than context retrieval?** Not supported by this study. Shared state was visible, but did not turn identical objectives into a useful parallel implementation team. Neither a context-value gain nor a productive-concurrency gain is demonstrated on this small fixture; this is not a general disproof of PI on larger projects.

## Integrity, failures and limits

- Twenty-four fresh native sessions, Luna medium, CLI 0.153.4; one shared checkout per project; no overlap between project trials. Frozen source/checker/task hashes, common prompt hash, model/effort contexts, raw streams and sampled source objects are preserved.
- No harness-assigned files/seams, follow-ups, repairer, evaluator hints, live checker feedback or retries. Native workers executed their own checker and Git commands. Ordinary tools remained available; private native profiles/mounts intentionally hid all previous trial artifacts and peer transcripts. This tests standalone native sessions sharing source, not a shared Codex daemon/team.
- Fixture, seven cross-dependent acceptance semantics and PI implementation unchanged. Equal checker visibility and committed Git baselines distinguish this study from the prior producer/consumer study; do not pool them. PI operational docs and stock instructions were treatment context; no treatment-only task facts were added. PI was pinned to `e384223962c55bbb7b4742f7cbced7bf1ae72f94`.
- V1/v2 preparations failed no-inference sandbox preflights. V3 launched only A1, then hit a missing DNS mount. That launch was explicitly stopped and preserved: 99.125s, final source 0/7, exit −15, no recorded coding output or token usage, one observer intervention. V4 fixed only the isolation setup before its new freeze. This is a disclosed replacement study version, not an omitted failed model-performance repetition. Raw recorder metadata says zero intervention because termination was external; ABORTED-INFRASTRUCTURE.md is the explicit correction.
- The external sandbox uses read-only system/PI/auth mounts and writable project/private profile/tmp; native internal sandbox is bypassed equally in all arms. Authentication was mounted, never copied into evidence. Network is retained for native inference. No claim is made about hidden provider state or hostile-code/network isolation; recorded prior-artifact access/delegation flags were empty.
- Sampling is non-atomic, tool timing includes wrapped operations, and model effort cannot be precisely allocated among edits/coordination. Three projects per arm give exploratory evidence, not statistical significance. D ran after the balanced-order primary A/B/C block and is secondary.
- During execution no production runtime change, release activation or PI repair was performed. This later publication adds reviewed source and summaries; it does not change the treatment or the historical artifacts.

Source artifacts are identified by study ID and hashes in [measurements.json](measurements.json). Exact raw logs, source objects and authentication-related runtime state are not published.

## What to test next

Hypothesis: broad full-project declarations did not become an agreed division, and this small migration was cheap enough for one worker to implement in one patch. A proposed next experiment would preserve equal task information on a longer task with independently checkable components and measure whether spontaneous allocation precedes useful concurrent edits; no such follow-up is claimed here.
