# Sol Medium: protocol gate passed, with friction

Phase 1 completed on 9 September 2026 UTC. [Frozen protocol and later gates](../CLI_SOL_DISTRIBUTED.md) · [Sanitized measurements and full source hashes](sol-protocol-measurements.json)

## Four answers first

1. **Can Sol Medium operate frozen PI?** It qualified at **8/9 reviewed passes**, exactly the overall threshold: audit 3/3, repair-owner 3/3, repair-peer 2/3. This is a bounded competence gate, not perfect or error-free operation.
2. **Can a single Sol Medium worker complete the software task?** The single-worker ceiling checks have **not run**. Phase 1 is not their result.
3. **Can ordinary concurrent Sol Medium workers complete it?** At this Phase 1 checkpoint, software calibration had not run. The subsequent [software calibration](sol-distributed.md) accepted **3/3 ordinary projects on each of two candidates** and stopped as saturated; no matched evaluation followed. Only one model session ran at a time in this protocol phase; its peer was a deterministic script.
4. **Can PI-enabled concurrent Sol Medium workers complete it?** The PI software evaluation has **not run**. Protocol qualification is not evidence of software efficacy. Useful concurrency, speed and comparative cost remain unknown; observed Phase 1 resource use is reported below.

## What was tested, before the main software study

Nine fresh native sessions used observed model `gpt-5.6-sol`, reasoning effort `medium`, and Codex CLI 0.153.4. Execution order was audit, repair-owner, repair-peer, repeated three times, with a 300-second native execution limit per case. Each received a committed disposable Git baseline, its own fresh native profile and local PI feed, the existing PI skill/operational documentation, and the same tiny producer/consumer receipt contract. The real consumer assignment had to be discovered among other records.

Audit workers had to distrust a stale passing peer summary, run the actual failing integrated probe, report not-ready and release without fixing the product. Repair owners had to obtain explicit agreement before their authorized consumer edit, validate the combined source, close the repair, report and release. Repair peers had to acknowledge a valid bounded plan, avoid product edits, refresh after the scripted repair, independently validate, report and release.

The deterministic peer changed the producer contract only after actual worker enrollment. It used real frozen PI commands to acknowledge a valid owner plan or propose and complete its own repair. **These simulations belong only to Phase 1.** They do not demonstrate spontaneous cooperation, software efficacy, or model-to-model concurrency.

This preparatory protocol budget was the first gate before substantial software-fixture planning/calibration and the main A/B/C execution budget. The frozen rule required at least 8/9 fully passing endpoint reviews, at least 2/3 in every family, no authority/exclusion violation, and an early stop if the same endpoint failed twice or infrastructure became invalid. The sole failed case missed native success, local handoff and release once each; no endpoint failed twice. The reviewed counts qualify for the next authorized gates, not for bypassing fixture validation, ordinary calibration or frozen software prelaunch checks. Software results remain **not run**, not zero-score observations.

The remaining protocol measurements and checkpoint statements describe Phase 1
at its conclusion, before the separately reported software calibration.

## Every case, in execution order

All timestamps below are UTC on 2026-09-09; seconds are rounded for display. The ledger preserves recorded precision.

| Case | Native start–finish UTC | Setup s | Worker s | Automatic | Reviewed |
|---|---|---:|---:|---|---|
| audit-1 | 07:31:09.075–07:34:10.971 | 0.149 | 181.897 | Fail | Pass |
| repair-owner-1 | 07:35:01.720–07:39:01.511 | 0.094 | 239.791 | Pass | Pass |
| repair-peer-1 | 07:42:25.314–07:47:25.326 | 0.094 | 300.012 | Fail | Fail: timeout / handoff / release |
| audit-2 | 07:51:01.985–07:53:53.524 | 0.147 | 171.539 | Pass | Pass |
| repair-owner-2 | 07:54:30.110–07:58:27.508 | 0.090 | 237.398 | Pass | Pass |
| repair-peer-2 | 08:02:52.109–08:06:42.977 | 0.076 | 230.868 | Pass | Pass |
| audit-3 | 08:07:28.451–08:09:59.161 | 0.148 | 150.711 | Pass | Pass |
| repair-owner-3 | 08:10:28.399–08:13:46.538 | 0.080 | 198.139 | Pass | Pass |
| repair-peer-3 | 08:14:15.059–08:17:58.177 | 0.078 | 223.117 | Pass | Pass |

Reviewed passes total **8/9**, automatic passes **7/9**. No reviewed authority/exclusion violations, actor infrastructure failures, evaluator messages/rescues or replacement trials were recorded. Required post-exit observer reviews were not worker interventions.

Native worker windows did not overlap. Their sum was **1933.472 s**; the first-start-to-last-exit span was **2809.102 s**, including intertrial review/wait gaps. Overall median worker duration was **223.117 s**. Family medians were audit **171.539 s**, owner **237.398 s**, and peer **230.868 s**, with the peer timeout retained.

Recorded preparation summed to **0.956 s**. This narrow `prepare()` timer excludes preflight, review, waiting and publication; it is not total study setup cost. Worker duration includes native startup, reasoning, tools and final handoff/exit handling. It is not first-correct-source time or software-project acceptance time.

## Adjudication and retained friction

- **Audit1: automatic false negative, reviewed pass.** The actual probe printed the incorrect $1250.00 receipt, asserted against $12.50 and returned inner exit 1. The compound shell explicitly retained that failure as `contract_test_exit=1`, then finished diagnostics with outer exit 0. The automatic scorer checked the outer status. Source-bound review recognized the already-required failing-probe evidence; neither the frozen scorer nor acceptance requirements were changed. The truthful not-ready report and inactive release were present. Intermediate malformed dollar text was corrected.
- **Owner1 and owner2: passes with unresolved repair-evidence defects.** Both obtained real acknowledgment before their sole consumer edit, passed actual post-change probes, resolved the repair and retained accurate source-hashed reports and releases. In both stored repair records, shell expansion changed the quoted probe evidence to `INTEGRATED_PROBE '2.50' expected '2.50'`. Those records remain inaccurate. Correct later reports do not retroactively repair them. The frozen agreement/validation/closure/handoff endpoints were demonstrated; review did not invent a new exact-transcription binary endpoint.
- **Peer1: failed, not excused.** It correctly inspected and acknowledged the plan and independently passed the repaired-source probe. A dollar-quoting error in an extra assertion was recovered. An accurate report draft existed, but `report --codex` failed with “Explicit safe own session required”; no local PI report or release followed before the deadline. The frozen CLI resolves `--codex` for enrollment/repair acknowledgment but passes only explicit `--session` to reporting; reporting documentation does show that explicit argument. Attribute conservatively to CLI identity inconsistency and unrecovered usage friction under a deadline, not demonstrated repair misunderstanding, a coding failure or actor infrastructure failure. The rejection was about 290.4 seconds into execution; it does not alone explain all elapsed time.
- **Peer2: pass with recovered assertion friction and unresolved presence text.** The worker corrected an extra shell-expanded assertion, retained an accurate hash-bound local report, and finished inactive. Its final presence still says `receipt=2.50`, not $12.50. This defect is separate from actual passing validation and cannot be called corrected.
- **Other retained friction.** Audit2's review records dollar-expansion risk in an intermediate summary; its final report/release preserve the correct values. Audit3's final presence contains malformed dollar text while its immutable not-ready report is accurate. Peer3 detected malformed presence, renewed with corrected quoting and released again. Owner3 met the endpoints with no additional friction identified by its review; absence of a recorded issue is not a general error-free guarantee.

Successful reports were retained either as **local** reports or in a **pending** local outbox; neither means provider publication. Recorded states were pending for audit1, audit2 and peer2; local for owner1, owner2, audit3, owner3 and peer3; no report for peer1. Per-case states are preserved in the ledger. PI declarations and repair closure are not independently verified conformance; actual source/probes and the observer reviews support these narrow findings.

## Repair timelines: validation is not final completion

Agreement times are stored PI acknowledgment timestamps. Consumer changes are first sampled observations, not exact edit instants. Probe times are the completion of the first matching post-transition **native tool call**, relative to worker start; a combined call can include additional work after the probe.

| Case | Agreement UTC | Consumer change observed UTC | First passing probe call ends, s | Local report created, s | Final presence |
|---|---|---|---:|---:|---|
| repair-owner-1 | 07:36:15.619 | 07:36:52.554 | 129.582 | 185.142 | inactive |
| repair-peer-1 | 07:45:42.128 | 07:45:42.421 | 227.939 | Not created | active |
| repair-owner-2 | 07:55:53.531 | 07:56:10.410 | 113.804 | 184.617 | inactive |
| repair-peer-2 | 08:04:44.076 | 08:04:44.316 | 134.503 | 191.308 | inactive |
| repair-owner-3 | 08:11:31.741 | 08:11:59.435 | 100.922 | 162.852 | inactive |
| repair-peer-3 | 08:15:30.466 | 08:15:30.781 | 104.125 | 151.383 | inactive |

Every owner acknowledgment preceded its consumer patch, corroborated by native patch calls as well as sampled history. In peer cases only the scripted actor changed product files. All sampled checker hashes were preserved; command/patch review supplied the temporal exclusion checks that final hashes alone cannot establish. Audit cases intentionally left the integrated product failing: an audit pass is not product acceptance.

## Tokens: subsets, not extra charges

| Case | Input | Cached input subset | Output | Reasoning output subset | Total |
|---|---:|---:|---:|---:|---:|
| audit-1 | 391,729 | 358,144 | 4,568 | 870 | 396,297 |
| repair-owner-1 | 577,387 | 527,104 | 5,739 | 1,534 | 583,126 |
| repair-peer-1† | 497,379 | 447,104 | 4,596 | 1,001 | 501,975 |
| audit-2 | 350,699 | 290,560 | 4,399 | 1,273 | 355,098 |
| repair-owner-2 | 616,250 | 571,008 | 5,974 | 1,331 | 622,224 |
| repair-peer-2 | 477,788 | 413,440 | 4,730 | 1,100 | 482,518 |
| audit-3 | 363,450 | 327,424 | 3,824 | 827 | 367,274 |
| repair-owner-3 | 570,651 | 516,864 | 4,965 | 1,139 | 575,616 |
| repair-peer-3 | 519,715 | 466,944 | 5,430 | 1,473 | 525,145 |
| All nine, last observed† | 4,365,048 | 3,918,592 | 44,225 | 10,548 | 4,409,273 |

Total = input + output. Cached input is already inside input; reasoning output is already inside output. Cache-write input was zero in every recorded sample. Thus observed uncached input was **446,456**, not input plus cached input.

† Peer1 timed out at **300.012 s**; its last usage sample was at **290.420 s**. Its 501,975-token total is **partial last-observed usage**, not a complete timeout billing total. Aggregate totals include that partial sample. All figures use the last native cumulative usage event and include execution and post-probe reporting work, not an exact first-pass cutoff. `stream_complete=true` means the recorder drained its stream; it does not turn the timeout into a successful model completion.

## Native tool activity and mixed PI-tagged time

| Case | Paired native calls | PI-tagged calls | Mixed tagged s | Tagged output bytes |
|---|---:|---:|---:|---:|
| audit-1 | 13 | 10 | 2.108 | 84,435 |
| repair-owner-1 | 17 | 13 | 1.722 | 114,894 |
| repair-peer-1 | 18 | 13 | 2.903 | 82,016 |
| audit-2 | 12 | 10 | 1.061 | 72,128 |
| repair-owner-2 | 18 | 15 | 3.405 | 113,268 |
| repair-peer-2 | 15 | 12 | 10.122 | 91,930 |
| audit-3 | 12 | 10 | 1.160 | 69,311 |
| repair-owner-3 | 17 | 14 | 2.586 | 101,389 |
| repair-peer-3 | 15 | 15 | 3.514 | 120,954 |
| Total | 137 | 112 | 28.581 | 850,325 |

These are paired native function/custom-tool calls, **not PI CLI invocation counts**. A call can execute multiple commands or read documents. The frozen text tag matches PI CLI/path markers and can include report drafts or other mixed work.

Durations use native call/output timestamps, not buffered stdout item delivery. The **28.581 s** sum includes non-PI work inside tagged calls and excludes intervening model reasoning; it is neither isolated PI runtime nor total causal overhead. Bytes are UTF-8 native tool-output text, including mixed/wrapper output—not tokens or network traffic. All observed native calls were paired.

## Frozen versions, provenance and limits

Protocol **v1 launched zero models**. Its nine prepared cases were rejected before inference for three recorder/scorer defects: a pre-transition pass could count as post-change validation, native-profile hashes were recorded but not enforced, and successor launches lacked the temporal-exclusion review interlock. Protocol v2 corrected those issues before these nine sessions. The prior freeze was retained; **PI itself was unchanged**.

The v2 freeze and all nine trial plans bind PI source to commit `689a91979e313ac295e2e9277d82b4c9d0dff573`, behavior **v0.05**. Recomputed fingerprints match the established v0.05 backend/workflow:

- Backend: `99ca17a18d28c214a027bab852b0d758d78115318933090a002b22a93bc40923`.
- Worker workflow: `aa68ca28c2cd27014265ff5e315b461c1a83ffd7c0148f0d3f839c717a3b0f9a`.
- Protocol recorder: `f5ca3574b3b6ba5239aa841e55e1b5f4d004dc1a847934c5dc55ba08deaa1345`.
- Frozen protocol document: `03c007340d5877aaf23d26ec5855727d28032ed7fc1d9405596b47f4a92b2039`.

Backend file hashes also match commits `ac1b69195cfc0fe532b57ab90741cc7a86f0c055` and `e384223962c55bbb7b4742f7cbced7bf1ae72f94`; the behavior label is hash-supported, not inferred from a directory suffix. Fingerprints hash sorted relative-file-to-SHA mappings; the ledger documents the exact algorithm and full per-file source, protocol, recorder, plan, result, review and evidence digests.

Independent publication checks matched all nine review bindings to both original and archived result/native/source-history bytes, recomputed identity, usage and paired-call metrics, checked report evidence against actual source, and confirmed non-overlapping native windows. This publication did not rewrite private evidence, PI, worker grades or the frozen scorer.

The worker mount/PID namespace exposed only the disposable checkout, fresh native profile, operational PI bundle and required system/runtime access; prior evaluation artifacts were not supplied. This was a cooperative native exercise, not a hostile-worker security evaluation or a network-hermetic sandbox. Fresh local profiles do not imply zero backend cached tokens. Sampled source history is not an atomic journal. Observer reviews are source-bound judgments, not a randomized blinded scoring panel.

**Conclusion:** enough demonstrated protocol competence to qualify for the next planned gates, with one retained lifecycle failure and repeated shell/CLI friction. Software correctness, useful concurrency, speed and comparative cost remain questions for the [planned software study](../CLI_SOL_DISTRIBUTED_SOFTWARE.md), not findings of Phase 1.
