# Original seven-seam study: concurrency versus context, Luna medium

[All results](../../RESULTS.md) · [Measurements](measurements.json)

PI behavior **v0.05** · frozen core `e384223` · fixture/recorder study v2.
Public editorial copy of the completed report; original evidence is unchanged. Run tables are newest-first by actual launch, not by arm label. Raw streams and private execution records stay outside Git.

**PI made parallel work less duplicative, but one worker was the fastest and lowest-token path on this fixture.** All 12 projects passed 7/7 without intervention. This does not establish that concurrency is the primary source of PI value in larger projects.

## Design and validity

- Exactly 3 fresh projects per A/B/C/D, 18 native Codex sessions, all verified `gpt-5.6-luna` / `medium`, CLI 0.153.4. No second model stratum.
- Original prices, stock, weights, discounts, delivery, contacts and orders fixture; identical producer/consumer prompt bytes and unchanged dynamic checker, including price→discount dependencies. Not the refund/migration fixture.
- A/D received both verbatim task texts in one session. B/C retained their original individual prompts. Every arm had both task texts available as ordinary repository files with the same pointer; PI indexed those same facts. Unlike historical trials, future peer requirements were not available only through PI. This intentionally changes information availability versus that historical baseline, not acceptance difficulty; do not pool the results.
- C/D used the unchanged supported PI skill/template and local integration workflow, pinned to merged `e384223962c55bbb7b4742f7cbced7bf1ae72f94`. Only operational documents were bundled; no prior evaluation results, solutions, transcripts or evaluator hints were supplied.
- Order: A1 B1 C1 D1 / C2 D2 A2 B2 / D3 C3 B3 A3. One project at a time, maximum two test workers; all process intervals confirm no cross-project overlap. No steering, prescribed repairs, runtime barriers, resumed trials or replacements. All processes exited normally; no 600-second cap was reached.
- Final verification happened only after all workers exited, on an isolated copy. Native token totals, literal output, source history and source/recorder hashes are preserved. No benchmark-evidence reads or delegated model sessions were found by the recorded-command audit; native configuration/host reads were not hermetically isolated, so this is not proof of absence of hidden service-side effects.
- Preflight v1 was rejected without model launches for excessive PI documentation exposure. v2 passed independent review and 208 pre-launch unit tests. PI implementation and live service were not modified.

## Primary project results

Time and compute columns below are **medians per project**; aggregate means summed across that project’s workers, not summed across repetitions. All runs passed, so accepted-project and all-run medians coincide. “Rework” lists observed events, not a subjective score.

| Condition | Runs | 7/7 rate | Median project wall time | Aggregate worker time | Aggregate tokens | Rework | Human intervention |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Single worker | 3 | 3/3 (100%) | 81.6s | 81.6 worker-s | 152,371 | 0 peer conflicts | 0 |
| Concurrent ordinary | 3 | 3/3 (100%) | 99.6s | 156.6 worker-s | 337,743 | 3 peer-stale patch failures; 2 label rewrites | 0 |
| Concurrent + PI | 3 | 3/3 (100%) | 141.4s | 236.9 worker-s | 949,750 | 0 peer patch conflicts; 2 demonstrated seam corrections; 1 self patch failure | 0 |
| Single worker + PI | 3 | 3/3 (100%) | 118.3s | 118.3 worker-s | 371,850 | 0 peer conflicts | 0 |

Tokens = input + output, including cached input. Cached input and reasoning output are subsets, not additional tokens. These are native usage counters, not GPU-seconds or a monetary cost estimate. Extra tokens are not automatically bad; here they did not purchase a faster or more consistently accepted project.

### Per-run results

| Run | Integrated | Producer / consumer | Failed seams | Project s | Worker-s | Concurrency factor | Total tokens |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A3 | 7/7 | 7/7 / 7/7 | None | 107.5 | 107.5 | 1.00 | 176,212 |
| B3 | 7/7 | 7/7 / 7/7 | None | 99.6 | 159.7 | 1.60 | 343,789 |
| C3 | 7/7 | 7/7 / 7/7 | None | 141.4 | 236.9 | 1.68 | 955,815 |
| D3 | 7/7 | 7/7 / 7/7 | None | 129.9 | 129.8 | 1.00 | 395,334 |
| B2 | 7/7 | 7/7 / 7/7 | None | 103.1 | 156.6 | 1.52 | 337,743 |
| A2 | 7/7 | 7/7 / 7/7 | None | 57.2 | 57.1 | 1.00 | 88,979 |
| D2 | 7/7 | 7/7 / 7/7 | None | 118.3 | 118.3 | 1.00 | 371,850 |
| C2 | 7/7 | 7/7 / 7/7 | None | 148.7 | 246.4 | 1.66 | 949,750 |
| D1 | 7/7 | 7/7 / 7/7 | None | 111.6 | 111.6 | 1.00 | 344,949 |
| C1 | 7/7 | 7/7 / 7/7 | None | 103.1 | 196.4 | 1.91 | 768,951 |
| B1 | 7/7 | 7/7 / 7/7 | None | 88.3 | 149.1 | 1.69 | 283,967 |
| A1 | 7/7 | 7/7 / 7/7 | None | 81.6 | 81.6 | 1.00 | 152,371 |

Each producer/consumer entry means all original checks in all seven seam groups passed; the exact individual checks remain in each archived results.json. No failed or partial run was dropped.

### Setup, execution and final verification

| Run | Prepare s | Worker interval s | Archive s | Final verification s | External repair s |
| --- | --- | --- | --- | --- | --- |
| A3 | 0.0041 | 107.460 | 0.0018 | 0.0340 | 0 |
| B3 | 0.0053 | 99.543 | 0.0018 | 0.0194 | 0 |
| C3 | 0.0092 | 141.342 | 0.0035 | 0.0374 | 0 |
| D3 | 0.0101 | 129.844 | 0.0039 | 0.0202 | 0 |
| B2 | 0.0030 | 103.107 | 0.0048 | 0.0214 | 0 |
| A2 | 0.0043 | 57.133 | 0.0019 | 0.0199 | 0 |
| D2 | 0.0104 | 118.274 | 0.0040 | 0.0194 | 0 |
| C2 | 0.0097 | 148.722 | 0.0041 | 0.0194 | 0 |
| D1 | 0.0114 | 111.565 | 0.0040 | 0.0331 | 0 |
| C1 | 0.0089 | 103.057 | 0.0041 | 0.0342 | 0 |
| B1 | 0.0042 | 88.286 | 0.0018 | 0.0194 | 0 |
| A1 | 0.0055 | 81.569 | 0.0018 | 0.0349 | 0 |

All preparation plus read-only preflights: 0.661s. Sequential execution/verification batch: **1291.1s (21.52 minutes)**. Harness development, observer analysis and review time are separate from coding-project time. In-session integration/repair is inside worker execution, not an additional sequential phase that should be added again.

## Worker compute

| Run / worker | Duration s | Input | Cached input | Uncached input | Output | Reasoning output | Total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A3 solo | 107.5 | 171,153 | 131,840 | 39,313 | 5,059 | 1,248 | 176,212 |
| B3 producer | 99.5 | 211,724 | 181,504 | 30,220 | 4,569 | 948 | 216,293 |
| B3 consumer | 60.1 | 124,785 | 102,656 | 22,129 | 2,711 | 525 | 127,496 |
| C3 producer | 95.6 | 361,226 | 319,488 | 41,738 | 4,391 | 560 | 365,617 |
| C3 consumer | 141.3 | 583,644 | 537,088 | 46,556 | 6,554 | 2,502 | 590,198 |
| D3 solo | 129.8 | 389,113 | 352,000 | 37,113 | 6,221 | 1,042 | 395,334 |
| B2 producer | 103.1 | 189,420 | 158,208 | 31,212 | 4,836 | 592 | 194,256 |
| B2 consumer | 53.5 | 141,088 | 118,784 | 22,304 | 2,399 | 1,126 | 143,487 |
| A2 solo | 57.1 | 86,374 | 69,376 | 16,998 | 2,605 | 705 | 88,979 |
| D2 solo | 118.3 | 366,693 | 326,400 | 40,293 | 5,157 | 1,285 | 371,850 |
| C2 producer | 148.7 | 578,431 | 526,336 | 52,095 | 6,782 | 1,437 | 585,213 |
| C2 consumer | 97.6 | 360,152 | 320,512 | 39,640 | 4,385 | 1,362 | 364,537 |
| D1 solo | 111.6 | 339,911 | 292,864 | 47,047 | 5,038 | 990 | 344,949 |
| C1 producer | 103.1 | 401,222 | 336,640 | 64,582 | 4,831 | 851 | 406,053 |
| C1 consumer | 93.4 | 358,755 | 294,912 | 63,843 | 4,143 | 1,107 | 362,898 |
| B1 producer | 60.8 | 105,457 | 83,456 | 22,001 | 2,812 | 766 | 108,269 |
| B1 consumer | 88.3 | 171,409 | 152,320 | 19,089 | 4,289 | 1,261 | 175,698 |
| A1 solo | 81.6 | 148,587 | 117,760 | 30,827 | 3,784 | 988 | 152,371 |

| Condition | Total worker-s across 3 projects | Total tokens across 3 projects |
| --- | --- | --- |
| Single worker | 246.2 | 417,562 |
| Concurrent ordinary | 465.4 | 965,499 |
| Concurrent + PI | 679.8 | 2,674,516 |
| Single worker + PI | 359.7 | 1,112,133 |

Counters use the last cumulative native usage sample, not a sum of cumulative samples. Output already includes reported reasoning output. Worker duration includes reasoning, tools, latency and waits; physical inference time is not separately observable.

## Was concurrency useful?

The defensible observable is whether **both workers landed separate, retained feature implementations while the other process was active**. It is not a measure of simultaneous GPU execution or a claimed number of productive reasoning-seconds.

| Run | Both-active seconds | First producer edit s | First consumer edit s | Both contributed during overlap? |
| --- | --- | --- | --- | --- |
| B3 | 60.1 | 66.1 | 40.8 | No: second editor landed after peer exit |
| C3 | 95.6 | 51.4 | 54.5 | Yes: disjoint implementations retained |
| B2 | 53.5 | 74.8 | 38.0 | No: second editor landed after peer exit |
| C2 | 97.6 | 65.5 | 53.3 | Yes: disjoint implementations retained |
| C1 | 93.4 | 54.0 | 47.6 | Yes: disjoint implementations retained |
| B1 | 60.8 | 39.9 | 79.8 | No: second editor landed after peer exit |

- **Ordinary: 0/3** met that productive-overlap observation. All three launched concurrently, but one worker’s overlapping patch was rejected; its eventual successful edit landed only after the other worker exited. Do not describe these as equivalent productive concurrency to C merely because two processes existed.
- **PI: 3/3** met it. In every C run the producer edited the eight producer modules and the consumer edited presentation.py, with no cross-worker file rewrite. Both sides’ implementations contributed to the accepted final project. C2 still required a repair tail after its consumer exited.
- All six B/C pairs repeated ordinary task/repository inspection. That shared discovery is visible duplicated effort, but it is also normal orientation, not automatically waste. Exact useful reasoning-seconds cannot be reconstructed from these logs.

### Concrete rework and duplication

| Run | Observed evidence |
| --- | --- |
| A3 | Self-refinement of integer day return; no peer rework. |
| B3 | Producer stale migration patch rejected after consumer implemented both tasks; later refined days(). |
| C3 | Disjoint work; consumer repeated an already-completed import cleanup (self patch failure), then expanded legacy compatibility. |
| D3 | Self-refinement/extra compatibility checks; one malformed PI handoff command recovered. |
| B2 | Producer stale presentation patch rejected; replaced peer labels; then repaired day formatting. |
| A2 | One implementation patch; no peer rework. |
| D2 | Self-refinement; one malformed PI refresh command recovered. |
| C2 | Disjoint work; consumer defensively guarded REFUNDED (still present); producer repaired day formatting after consumer exit. |
| D1 | Self-cleanup; no peer rework. |
| C1 | Disjoint work; consumer corrected day formatting after migration; producer also restored integer returns. |
| B1 | Consumer stale migration patch rejected; later rewrote producer-created presentation.py. |
| A1 | Self-cleanup only; no peer rework. |

B1: producer implemented both tasks at 39.9s; consumer’s old-catalog patch failed, then it rewrote presentation.py at 79.8s, after producer exit at 60.8s. B2: consumer labels landed at 38.0s; producer’s stub-based patch failed, then it replaced the label implementation at 74.8s after consumer exit at 53.5s. B3: consumer implemented both at 40.8s; producer’s old-catalog patch failed and its only successful edit was a days() refinement at 66.1s, after consumer exit at 60.1s.

C1: consumer repaired `2.0 days` formatting with `:g` at 61.2s; producer later restored integer-valued helper returns. C2: consumer defensively guarded REFUNDED at 73.4s, but that symbol remained present in every recorded orders.py version, so this was not a demonstrated repair. The producer corrected float day formatting at 117.3s after consumer exit. These are two demonstrated integration corrections across C, plus defensive hardening. C3’s failed patch was self-induced: it tried to match an import it had already removed, not a peer conflict. Its subsequent compatibility expansion was retained but did not improve the already-passing integrated score.

No obsolete tests were added to the final repository, and no repair-claim/ack/complete operations occurred. Workers mainly used native ad-hoc checks and the existing test suite. We did not infer undocumented rework from same-file edits alone.

## PI overhead and friction

| Run / worker | Enrollment completed at s | Observed onboarding span s | PI-related tool-call wall s | PI-related output bytes | Failed PI command groups |
| --- | --- | --- | --- | --- | --- |
| C3 producer | 29.9 | 21.8 | 0.945 | 91,903 | 0 |
| C3 consumer | 30.2 | 22.7 | 0.962 | 90,041 | 0 |
| D3 solo | 29.3 | 22.3 | 1.080 | 67,245 | 1 |
| D2 solo | 30.9 | 24.0 | 1.005 | 65,889 | 1 |
| C2 producer | 40.5 | 34.2 | 1.070 | 70,852 | 1 |
| C2 consumer | 28.2 | 20.6 | 0.883 | 86,427 | 0 |
| D1 solo | 31.2 | 22.6 | 0.965 | 54,826 | 0 |
| C1 producer | 30.1 | 22.4 | 1.028 | 87,688 | 0 |
| C1 consumer | 24.6 | 16.3 | 0.834 | 87,098 | 0 |

| Operation | C total, 6 workers | D total, 3 workers |
| --- | --- | --- |
| Successful onboarding invocations (command groups) | 13 (12 groups) | 6 (6 groups) |
| Rejected onboarding shell attempts | 1 | 0 |
| Successful active enrollment / release operations | 6 / 6 | 3 / 3 |
| Successful integration refresh operations | 7 | 4 |
| Rejected refresh shell groups | 0 | 2 |
| Rejected release in same malformed compound group | 0 | 1 |
| repair claim / ack / complete | 0 / 0 / 0 | 0 / 0 / 0 |

- All nine PI-aware workers enrolled under their own native session IDs and released. Median enrollment completion was about 30s into execution; the observed first-PI-read→enrollment span was about 22s per worker. Those spans include intervening model reasoning and sometimes repository reading—not a pure API latency measurement.
- Median aggregate PI-related native tool-call wall time was 1.907s/project for C and 1.005s/project for D. These include mixed PI + repository command groups, so they are not exact PI-only runtime. The CLI’s buffered item event delivery gaps must not be used as execution durations.
- Median emitted output from PI-related command groups was 174,786 bytes/project in C and 65,889 in D. These mixed outputs include some ordinary task/code reads and may be truncated by native output limits. Exact PI-only context tokens are **not identifiable** from whole-request usage counters; no invented token allocation is reported.
- Friction: C2 quoted the entire multiword CLI prefix as an executable; D2 and D3 constructed malformed quoted refresh commands. The workers recovered unaided. These were workflow/shell-usage errors, not observed service crashes. C1 also omitted checkout.py from its producer path declaration despite editing it; seam context still covered prices. The treatment was not repaired mid-study.

## Measured execution timelines

Representative repetition 1; labels are measured seconds from first native launch. Bars depict process windows, not uninterrupted inference. Marked edits/repairs occurred naturally; there was no evaluator repair phase.

```text
A1 — single, no PI
  0.0 |================ worker ================| 81.6  7/7
                 joint implementation 43.3s

B1 — concurrent ordinary
  0.0 |=========== producer ============| 60.8
  0.0 |================ consumer =================| 88.3  7/7
       whole project: 39.9s; consumer stale patch rejected
                              consumer rewrite: 79.8s

C1 — concurrent PI
  0.0 |================= producer ==================| 103.1  7/7
  0.0 |=============== consumer ===============| 93.4
       consumer labels: 47.6s; producer migration: 54.0s
       consumer day-format repair: 61.2s

D1 — single + PI
  0.0 |==================== worker =====================| 111.6  7/7
       enrolled: 31.2s; joint implementation: 67.7s
```

### Retrospective source-state check (secondary)

The observer replayed sampled byte snapshots only after workers exited. This identifies the first sampled 7/7 state that stayed passing in subsequent samples; it is **not** an earlier online verification or permission to stop workers retrospectively. Sampling is 100ms and non-atomic.

| Condition | Stable sampled 7/7 source median s | Per-run seconds |
| --- | --- | --- |
| Single worker | 41.1 | 43.3, 41.1, 40.6 |
| Concurrent ordinary | 40.8 | 39.9, 87.6, 40.8 |
| Concurrent + PI | 61.2 | 61.2, 117.3, 54.5 |
| Single worker + PI | 61.3 | 67.7, 61.3, 58.4 |

This secondary view also shows no meaningful source-completion gain from ordinary concurrency and no PI concurrency advantage over single+PI. Some extra worker time was validation, cleanup or compatibility expansion after a passing source state, rather than necessary repair.

## Answers to the ten evaluation questions

1. All four conditions reached 7/7 in 3/3 runs, including every producer and consumer check. This sample showed no correctness advantage for PI.
2. Single worker without PI had the lowest median accepted-project time: 81.6s. The fastest individual project was A2 at 57.2s.
3. Single worker without PI used the least recorded aggregate tokens and worker-seconds. Physical model compute is not measured directly; tokens/cache/output are provided as separate proxies.
4. Concurrency did not reduce median project completion time: B 99.6s versus A 81.6s; C 141.4s versus D 118.3s. Do not infer a population effect from three runs.
5. PI concurrency was productive in the concrete retained-contribution sense (3/3); ordinary overlap mostly duplicated implementation and produced rejected stale patches (3/3). Productive overlap alone did not produce a wall-clock win.
6. PI reduced observed peer-stale patch failures from 3 to 0 and cross-worker presentation rewrites from 2 to 0. It did not eliminate seam repairs: C1/C2 still needed two demonstrated day-format corrections; the C2 REFUNDED guard was defensive, not a proven repair. C3 had one self-stale cleanup failure.
7. Yes: roughly 30s to enrollment per worker, around 22s from first PI read through enrollment, additional context/usage, 1–2s of aggregate mixed PI-related tool calls per project, and three malformed shell groups across C/D. Exact PI-only tokens are unavailable.
8. No stronger worker was needed: the same Luna-medium single worker solved all three projects. Stronger models were not tested in this study.
9. That single-worker route was faster at the median: 81.6s versus 141.4s for concurrent PI. Individual runtimes varied (A 57.2–107.5s), so this is not an assertion that every A run beats every C run.
10. The strongest observed PI effect was role-aware coordination, not additional task facts or individual correctness. However, PI’s instructions, structured task context and live presence remain bundled: these arms do not isolate live shared state from static context alone. The primary-concurrency-value hypothesis is not established, and this fixture’s measured trade favored one coherent worker.

## Limits and artifacts

- Three runs per condition, one small original fixture and one model/effort. Perfect 3/3 scores do not establish reliability on larger work. Interleaving is not full counterbalancing; shared service load/cache behavior remains uncontrolled.
- Original Git initialization was retained: fixture files start untracked with no commit, so ordinary git diff has no tracked baseline. Git/test/repository inspection capabilities were not disabled, but D2 spent time verifying this; results are not a direct model of a mature repository.
- Raw task text availability was deliberately equalized. Earlier PI/control scores with unequal peer-task visibility are not a matched baseline for this question.
- No online checker feedback or automatic early stopping, and no source repair by the observer. Post-hoc repairs were classified from recorded actions; exact time spent reasoning about them is unavailable.
- Frozen protocol, result/analysis JSON, integrity checks, source replay and native archives remain private. [Published measurements](measurements.json) retain per-run telemetry and SHA-256 provenance without raw logs.
- The Project Intent skill governed observer enrollment/reporting and supplied the unchanged worker workflow in the treatment. [Official Codex documentation](https://learn.chatgpt.com/docs/non-interactive-mode) describes native noninteractive execution; actual model, effort and usage were verified from each local session.

## What to test next

Hypothesis: the serial problem was too short to repay onboarding/context overhead, while the predefined split helped PI workers keep their contributions distinct. The next completed study removed that prescribed split: [identical-objective self-organization](self-organizing.md); all arms again passed, but neither concurrent arm divided implementation usefully.
