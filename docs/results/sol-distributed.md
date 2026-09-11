# Sol Medium · distributed coherence

[All results](../../RESULTS.md) · [Method](../CLI_SOL_DISTRIBUTED_SOFTWARE.md) ·
[Protocol competence](sol-protocol.md) · [Structured measurements](sol-distributed-measurements.json)

## Outcome · calibration stopped before treatment

1. **Could Sol Medium operate PI?** It completed **8/9** deterministic workflows
   inside the frozen limit, qualifying for software calibration. One reporting/release
   timeout and transcription friction remain; this was not error-free operation.
2. **Could one Sol Medium solve the distributed project?** **Not tested.** Neither
   candidate qualified for the single-worker ceiling gate.
3. **Did concurrent ordinary Sol Medium succeed?** Candidate 1: **3/3 accepted**.
   Candidate 2: **3/3 accepted**. Both allowed candidates saturated this small sample.
4. **Did otherwise-identical PI workers succeed?** Not run. Treatment follows the
   agreed ordinary-calibration and single-worker gates; those gates did not open.

These are **completed calibration results**, not the planned frozen A/B/C evaluation.
The two-candidate budget is exhausted. **No more model trials were launched.**
We observed useful ordinary concurrency, but did not establish the correctness
headroom needed to measure PI's contribution. This is neither a PI win nor evidence
that PI has no value.

## Candidate 2 · implementation-defined return contracts

**3/3 accepted without PI; rejected as saturated, not an A/B/C result.** This second and final candidate
retains the original migration and adds durable partial returns. Catalog chooses
its restoration receipt layout, Orders chooses return notifications, and Settlement
chooses refund notifications. Reporting must integrate the actual chosen meanings.
Every business requirement and checker is public in both conditions; no producer
payload layout or reference implementation is supplied to workers.

[Frozen methodology](../CLI_SOL_DISTRIBUTED_CANDIDATE2.md) ·
[Objective](../../experiments/assets/distributed_v2/fixture/OBJECTIVE.md) ·
[Prelaunch validation and source hashes](sol-distributed-candidate2-inputs.json)

Sol Medium throughout; PI behavior v0.05 and the recorder are unchanged. **300
repository tests** passed before freeze. The reference and a coherent alternative
layout pass all **15 integration groups + eight original local tests**. A changed
producer payload without consumer adaptation fails integration while local/legacy
checks pass. This validates selected seam sensitivity, not exhaustive correctness.

| Project | Started Sep 9 UTC | State | Integration / locals | First accepted sample | Final project | Worker-s | Tokens | Retained implementations |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| B3 | 10:13:57 | **Accepted** | **15/15 · 17/17** | **487.242s** | **665.177s** | **2,376.468** | **2,965,664** | **4** |
| B2 | 10:01:00 | **Accepted** | **15/15 · 17/17** | **504.892s** | **632.790s** | **2,301.124** | **3,139,955** | **4** |
| B1 | 09:46:08 | **Accepted** | **15/15 · 18/18** | **599.422s** | **742.253s** | **2,595.296** | **2,629,461** | **4** |

Every planned calibration project completed; none was replaced. No single-worker
or PI software project ran. B1 reached its first durably accepted sampled
source at **9m59s**; a worker first observed a passing checker at **613.0s**. The
remaining tail ended at **12m22s** including final verification. Peak concurrency
was four, factor **3.498**, launch skew **0.724ms**; no human intervention.

B1's concrete observations:

- **Ordinary contract inspection occurred.** Orders reread Catalog's new contract
  and added a `schema == 3` guard plus matching docs/tests at 557.9s. Its original
  receipt-field assumptions already matched; this was validation hardening, not
  a demonstrated repair of incompatible data. Reporting's initial parser supported
  Settlement's chosen per-return deltas; its 705.3s change was post-pass hardening.
- **All four components retained distinct implementations and added tests.** No
  observed competing implementation, peer overwrite or peer-parser/state access.
  Reading shared requirements and performing repeated checks is not counted as
  duplicate implementation. There is no measured serial baseline to prove speedup.
- **Five rejected patch attempts:** four same-file module replacements plus an
  Orders documentation replacement. Module-absence intervals included Catalog
  148.2s, Orders 143.1s and Settlement 206.6s; these overlap and are not additive
  project delay. Reporting's delete/add gap was approximately 4ms.
- **Seven worker checker calls:** two failing, five passing. Each failed call had
  twelve missing-Settlement failures and one legacy Reporting assertion failure.
  Catalog's final message over-attributed them all to missing Settlement, but did
  not claim the project was accepted. Other accepted claims had passing probes.

B2 also retained four separately owned implementations. Reporting corrected an
own-code zero-capture/refund conflation at **451.9s**, adding an explicit refund
evidence flag and a regression test. Its initial parser already supported the
actual cumulative payment fields; later validation at **541.2s** followed first
acceptance, not a demonstrated stale-peer repair. Six rejected patch calls included
four module replacements, a malformed test patch and a documentation replacement.
Eight worker checker calls produced three failing and five passing observations;
temporary module absence accounts for the integration failures. First/durable
accepted source was **504.892s**, first worker passing probe **509.8s**; final
completion **632.790s**. No human intervention, integrity violation or timeout.
Orders' post-pass receipt and event-ID changes were also hardening, not recovery
from a demonstrated peer incompatibility. Catalog's final claim of four “Orders
integration tests using Catalog” actually referred to tests using **CatalogStub**;
the later real integrated checker is the acceptance evidence. Orders' reported
seventeen focused tests meant the aggregate suite, not seventeen Orders tests.

B3 retained all four implementations, contracts and expanded local test files.
Four rejected replacement patches preceded module-absence intervals of Catalog
**142.7s**, Orders **141.5s**, Reporting **181.6s** and Settlement approximately
**5ms**. Eleven scored worker checker calls produced three failures on incomplete
source and eight passes; one additional invocation used an unsupported `--group`
flag. First acceptance occurred when Reporting landed at **487.242s**, not during
a later repair. Catalog's precision checks, Orders' stricter restoration validation,
Settlement's refund-ID/persisted-state checks and Reporting's explicit per-return
`amount_minor` parsing all came afterward. Reporting's cumulative-refund handling
already passed: the later delta parsing was contract alignment/hardening, not an
acceptance-enabling coordination repair. No observed peer overwrite or authority
violation; final accepted claims had passing integrated probes.

### Project-level summary · candidate 2 only

Medians of per-project totals; tokens include the post-acceptance worker tail.

| Condition | Accepted | First accepted sample | Final project time | Aggregate worker time | Tokens | Distinct retained contributions | Rework |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Single Sol Medium | Not run | — | — | — | — | n/a | Not measured |
| Four ordinary Sol Medium · calibration | **3/3** | **504.892s** | **665.177s** | **2,376.468s** | **2,965,664** | **4 components/project** | Own-code repair/hardening and patch friction; no observed peer overwrite |
| Four Sol Medium + PI | Not run | — | — | — | — | Not measured | Not measured |

| Project | Checkout setup | Archive | Final verification | Worker window | Concurrency factor | First worker passing probe | Human intervention |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| B3 | 0.019s | 0.024s | 0.283s | 664.869s | 3.574 | 497.966s | 0 |
| B2 | 0.017s | 0.022s | 0.288s | 632.478s | 3.638 | 509.808s | 0 |
| B1 | 0.018s | 0.022s | 0.362s | 741.868s | 3.498 | 613.018s | 0 |

Peak concurrency was **four in every project**; maximum launch skew **1.913ms**.
No failed final contracts, worker timeouts, identity mismatches or protected-input
changes occurred. No outside integration/repair was supplied. Four distinct
retained implementations support useful work, not just overlapping processes.
Precise productive seconds, discarded-effort fractions and tokens to first
acceptance are not available; native-active time is not continuous coding time.

**Possible benchmark limit:** ordinary source/docs inspection remained sufficient
even with producer-designed payloads. The next separately authorized study would
need to test genuinely unresolved cross-component assumptions and their evolution,
not merely add another feature or weaken Sol. This bounded study stops here rather
than repeatedly tuning against the same model until it fails.

Batch freeze SHA-256:
`77e7f8e2c47059e8f06752aec900c7ab9092ed7f377233a1b0657d4cc26431ea`.
Checker SHA-256:
`4038acf5a9a839cee9e131d2b774d5f7bb1ae4d5dba2b1e46814a8a6bec572f0`.
Full worker intervals, token subsets and review/source bindings are in the
[separate ledger](sol-distributed-measurements.json); candidate scores are not pooled.

### Measured representative timeline · candidate 2 B3

Seconds from first native launch, rounded; bars indicate process intervals only.

```text
                     0         150         300         450         600    700s
Catalog              |==========================================| 543
Orders               |===========================================| 554
Settlement           |================================================| 614
Reporting            |====================================================| 665

250  Catalog removes its old module for replacement
256  Orders removes its old module for replacement
306  Reporting removes its old module for replacement
393  Catalog implementation lands
397  Orders implementation lands
417  Settlement implementation lands
487  Reporting implementation lands → first durably accepted sampled source
498  Reporting observes passing integration
520  Catalog precision/state-version hardening
538  Orders tightens restoration receipt validation
539  Settlement normalizes lines and refund identifiers
600  Settlement adds persisted identity/acknowledgment validation
646  Reporting aligns delta parsing; cumulative handling already passed
665  Final worker exit and verification → accepted 15/15 + 17 local tests
```

This is observed ordinary concurrency, not a PI timeline or a measured serial
speedup. Source snapshots are not atomic across files; post-exit replay provides
sampled acceptance times, while worker probes independently observed later passes.

## Candidate 1 · prescribed internal contracts

Four workers owned Catalog, Orders, Settlement and Reporting, respectively. The
working legacy product needed money/schema migration, durable inventory reservation,
retry recovery, acknowledged outboxes, deferred capture, cancellation/refund
reordering, historical-store migration and late receipt joins. All workers could
inspect every requirement, component and public checker. No evaluator messages,
integration fixes, artificial delays or follow-up assignments were supplied.

**Ordinary workers achieved useful parallel implementation without PI.** All four
component implementations survived in each project. Temporary file-replacement
gaps and self-editing errors occurred, but no competing implementation of an owned
component or peer overwrite was observed. This is not a measured speedup over one
worker: that baseline has not run.

**Suspected benchmark limit:** the complete internal wire contracts were prescribed,
so workers could implement compatible components independently. **The second candidate
examined** implementation-defined internal payloads for partial returns, with
fixed public business semantics and equally inspectable producer code/docs. Its
prelaunch checks and completed calibration are reported above. PI stayed unchanged.

### Calibration summary

Native **gpt-5.6-sol / medium**, Codex **0.153.4**; three fresh projects, one project
at a time, four workers concurrently inside each. Every recorded native worker
confirmed the requested model/effort. Medians below are per-project values.

| Condition | Accepted | First accepted source¹ | Final project time | Worker-s | Tokens² | Distinct retained contributions | Human intervention |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| Single Sol Medium | Not run | — | — | — | — | — | — |
| Four ordinary workers · calibration | **3/3** | **344.0s** | **490.0s** | **1,620.2** | **1,488,668** | **4 component implementations/project** | **0** |
| Four PI workers | Not run | — | — | — | — | — | — |

¹ First accepted **sampled source state**, verified by post-exit replay; also the
first durably accepted sample in all three runs. It is not a live observer signal
or an exact continuous first-passing instant. Worker-observed passing probes are
reported separately below. Final project time includes worker completion and final
verification, not the sum of worker durations.

² Cumulative input + output through each worker's last usage record, including
post-acceptance validation/final-message work. Cached input and reasoning output
are subsets, not additional tokens. These are not exact tokens consumed up to
first acceptance, GPU compute, dollars, or an efficiency verdict.

### Every project · newest first

UTC execution times; labels retain launch order.

| Project | Started Sep 9 | Integration | Local tests | First accepted sample | First worker passing probe | Final project | Worker-s | Concurrency factor | Total tokens |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| B3 | 09:14:36 | **12/12** | **14/14** | 307.616s | 312.4s | 399.306s | 1,542.721 | 3.866 | 1,488,668 |
| B2 | 09:01:17 | **12/12** | **14/14** | 536.619s | 543.2s | 649.189s | 1,918.028 | 2.956 | 1,893,107 |
| B1 | 08:51:08 | **12/12** | **13/13** | 343.970s | 350.8s | 490.014s | 1,620.196 | 3.308 | 1,469,382 |

No failed final contract, worker timeout, native identity mismatch or human
intervention occurred. Each native process exited cleanly and the protected task,
architecture and checker inputs remained unchanged. Peak concurrency was **4** in
each project; maximum launch skew was **1.7ms**. Process overlap alone is not the
evidence of useful work: distinct retained source contributions are.

| Project | Checkout setup | Archive | Final verification | Worker execution window | Outside integration/repair |
| --- | ---: | ---: | ---: | ---: | ---: |
| B3 | 0.015s | 0.014s | 0.238s | 399.052s | 0 |
| B2 | 0.011s | 0.015s | 0.250s | 648.923s | 0 |
| B1 | 0.012s | 0.027s | 0.269s | 489.715s | 0 |

Setup is recorded disposable-checkout preparation, not benchmark design, source
freezing, preflight or human review. Repairs/hardening by workers remain inside the
execution window. Passive history replay happened after exit and is analysis time,
not interactive assistance or project execution time.

### Rework, transient failures and completion claims

- **B1:** four rejected delete-and-add-in-one-patch attempts, one per worker.
  Reporting then left its module absent for **117.5s** while composing its replacement.
  Seven worker checker invocations: four failing, three passing. Missing Reporting
  and unfinished Settlement caused most transient failures, not ten independent
  semantic mistakes. Orders' final message retained an outdated “Reporting missing”
  observation after the module had returned. Later Orders/Reporting hardening did
  not establish the first passing state.
- **B2:** four rejected same-file replacement attempts; module-absence intervals
  were Catalog **100.8s**, Orders **99.9s**, Reporting **111.9s**, Settlement **116.4s**.
  They overlap and must not be summed into attributable project delay. Settlement's
  replacement introduced malformed syntax, detected and repaired by that same
  worker at **536.6s**; this was an own-code repair, not evidence of stale peer state.
  Seven checker invocations: five failing, two passing. Reporting briefly described
  already-migrated peers as legacy. No worker falsely claimed full final acceptance.
- **B3:** four rejected same-file replacement attempts. Three workers then removed
  and replaced their modules; Settlement used an update patch instead. Seven checker
  invocations: two failing, five passing. Both failing probes
  encountered Catalog's missing replacement module; the earlier probe also found
  Orders absent during replacement. They did not reveal eight
  distinct final contract defects. Orders explicitly noticed neighboring work,
  kept changes scoped, and used its own focused Catalog-contract check. Each worker's
  eventual accepted claim was supported by a passing integrated probe.

All three retained four separate component implementations and additional focused
tests in two component roots. No observed duplicate component implementation,
cross-owner overwrite, competing repair or discarded integration branch. Repeated
reading of the common specification/checker occurred; that is duplicate inspection,
not automatically duplicate implementation. Precise effort fractions for discarded
work are unavailable. Patch failures, tool-use recovery and missing-module intervals
are reported rather than compressed into a subjective coordination score.

### Measured representative timeline · B3

Times are seconds since first native launch, rounded. Bars show process intervals,
not continuous implementation activity.

```text
                     0          100         200         300         400s
Catalog              |======================================| 389
Orders               |=======================================| 399
Settlement           |======================================| 393
Reporting            |===================================| 362

174  Reporting removes its legacy module for replacement
178  Orders removes its legacy module for replacement
198  Catalog removes its legacy module for replacement
280  Reporting replacement lands
281  Settlement implementation lands
287  Orders replacement lands
308  Catalog replacement lands → first accepted sampled source
312  Catalog observes a passing integrated checker
352  Settlement adds focused regression tests/hardening
353  Catalog adds focused regression tests
399  Last native worker exits; final verification accepts 12/12
```

No single-worker or PI software timeline is invented for an unrun condition.
The [ledger](sol-distributed-measurements.json) retains every worker interval,
token subset and active-worker timeline, plus source/provenance hashes.

## Frozen inputs and retained preparation failure

- Candidate: `distributed/v1`; [source/objective](../../experiments/assets/distributed_v1/fixture/OBJECTIVE.md).
- Batch freeze SHA-256: `fe5f61ef1ab6531b6ccb3915c9cf28508b5628de727979f58e6ef648b4094373`.
- Native recorder SHA-256: `a60be3c061db37454bc45b3ede64c78a1c77ce5427c01d5b74c3fc49908445a8`.
- Checker SHA-256: `e3b9c8c4600c01d0c723b66a52f4096ac0fd4de5efa5bd08580e055a63c5f137`.
- PI behavior **v0.05**, frozen main `689a91979e313ac295e2e9277d82b4c9d0dff573`.
  Not enabled in these software calibration projects; no PI software overhead exists
  to measure here. The prerequisite protocol costs are [reported separately](sol-protocol.md).
- One preparation aborted **before any model launch**: a native version probe
  created helper files in supposedly pristine worker profiles. Freshness validation
  rejected them. A separate preflight profile and regression test fixed the recorder
  before the successful freeze; the rejected preparation remains archived. This did
  not replace a failed model trial or change PI.
- **269 repository tests** passed before the successful software freeze. The later
  posthoc exporter has **17 focused tests plus three publication checks**; it reads completed JSON and does not run
  candidate code, modify evidence, or provide feedback to workers.

The reference passed all twelve groups and eight original local tests. Twelve
deliberate contract mutations were detected, including local-pass/integration-fail
cases. Functional acceptance does not certify atomic filesystem replacement or
power-loss durability; that limitation is public before execution.

Final repository validation passed **301 tests in 21.911s**. Frozen recorder,
fixture/checker and prelaunch test hashes still match. Historical seven-seam
measurements, PI implementation and worker instructions remain unchanged.

## Interpretation and bounded stop

Both candidates demonstrate **coherent ordinary concurrency under fixed ownership**:
four retained component implementations in every project. Candidate 2 added
producer-designed internal payloads and substantially more return/recovery work,
but still produced three accepted projects. That is an observed result, not a
population success-rate estimate.

- **PI competence:** 8/9 explicit protocol exercises qualified, with a retained
  reporting/release failure and transcription friction. This does not certify
  perfect or spontaneous PI adherence during coding.
- **Single-worker capability and concurrency speedup:** not measured. No solo
  software project ran, so neither a serial ceiling nor an elapsed-time advantage
  can be inferred from these concurrent projects.
- **Useful concurrency:** four distinct owned implementations survived each run.
  No observed competing component implementation or cross-owner overwrite.
  Transient missing modules, rejected patches and own-code corrections occurred;
  these are not automatically stale-peer defects.
- **PI correctness benefit, overhead and failure attribution:** not measured in
  software. PI context reads, repair operations and handoffs exist only in the
  separately reported protocol calibration, not in these ordinary projects.
- **Compute:** candidate 1 consumed **4,851,157** reported input+output tokens;
  candidate 2 consumed **8,735,080**. These are accounting totals, not pooled effect
  estimates or exact compute to first acceptance.

The agreed maximum of two candidates × three ordinary projects has been exhausted.
Both were rejected as saturated; no single-worker ceiling or matched evaluation
was allocated. Calibration outcomes are not repackaged as frozen evaluation.
No PI code, worker instructions, production runtime or model capability was changed.

**Answer to the primary question:** this study cannot determine whether PI materially
improves coherence for competent concurrent workers. It established that both
bounded fixtures remained solvable by ordinary concurrent Sol Medium. A future
version should first justify a source of unresolved semantic change that ordinary
inspection cannot settle immediately; it must preserve equal task information and
native development capabilities. Do not manufacture a failure by crippling the
control or prescribing PI-only coordination.

The proposed orchestrator follow-up remains conceptual and unexecuted: fixed versus
agent-chosen decomposition, crossed with ordinary versus PI state. It should not be
mixed into this calibration or pursued before a useful base comparison exists.
