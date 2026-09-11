# Compact PI prompt · Qwen thinking off

[All results](../../RESULTS.md) · [Measurements](qwen-compact-pi-measurements.json) · [Exact prompt](../../experiments/qwen_compact_pi.md) · [Method](../CLI_QWEN_COMPACT_PI.md)

**1/3 projects accepted: 0/7, 0/7, 7/7.** Shortening the instructions did not
eliminate protocol loops. Two producers were stopped by Qwen Code's native loop
guard; there were **no timeouts**. All 88 provider requests had thinking disabled
and reported zero reasoning tokens. No confidence phrase or ordinary trials.

## What changed

Startup instructions fell from **543 to 260 words**, with no SayHi/SparkOps-specific
prose. Discovery, enrollment, shared context, repair agreement, integrated validation
and release remain. The preceding startup also required a 775-word skill and
911-word worker reference: **2,229 words across those three documents**, before
additional links. The compact route makes detailed documentation available on
demand instead. None of these six workers read the full skill/worker reference;
C1's producer did read repair guidance.

This is a **compact instruction/UX bundle**, not a word-count-only ablation: it
also supplies a relative shell helper and the actual `start` refresh command.
Backend **v0.05**, skill and operational documents are unchanged. PI command
responses are not shortened and can still contain long context and installed
documentation paths. Experiment version: **`qwen-compact-pi/v1`**.

Same original **non-torture seven-seam** source, checker and producer/consumer
prompts. Qwen Code **0.23.2**, `qwen38-27b-dflash2`, DGX1+DGX2, 230k context,
32,768 output cap, thinking off, native compaction retained. Three fresh projects
ran sequentially; each contained two concurrent native sessions. All plans froze
before C1. No worker feedback, retries, evaluator repairs or production changes.

## Results · newest first

| Run | Executed UTC, Sep 9 | Integrated | Producer / consumer | Project time | Aggregate worker time | Input + output tokens |
| --- | --- | --- | --- | ---: | ---: | ---: |
| C3 | 22:05:28–22:07:11 | **7/7 accepted** | 7/7 · 7/7 | **103.227s** | 189.896s | 1,289,644 |
| C2 | 22:04:04–22:05:28 | **0/7** | 0/7 · 1/7 | 83.979s | 153.346s | 737,914 |
| C1 | 22:01:54–22:04:04 | **0/7** | 7/7 · 0/7 | 129.917s | 200.160s | 1,473,077 |

All seven integrated seams fail in C1 and C2. C2's only passing consumer seam is
Orders; its producer never implements the migration. Four of six native workers
exit successfully; two exit with an explicit loop-detection error. Native success
is not project acceptance. Human intervention after launch: **zero**.

Tokens sum all requests, including repeated cached input, not unique context or
an efficiency score. Cached-input reporting is incomplete in C1/C2 and complete
in C3; input/output and reasoning reporting are complete throughout. The ledger
includes each worker's usage, native duration, identity and control verification.

## What actually happened

- **C1 — stale implementation, then repair/enrollment failure.** Consumer tests
  passed before the producer's migration. Its release explicitly acknowledged
  that integration remained unverified. Producer subsequently found stale
  `NAMES`/`REFUNDED` imports and attempted a repair claim naming the exited peer.
  PI refused because that peer was inactive. Producer misread this as its own
  expired enrollment and used `presence` as though it were an inspection command.
  That legacy command overwrote its enrollment with a simpler presence record.
  Seven subsequent enrollment attempts failed with `'claimed_at'`; identical
  retries triggered Qwen Code's loop guard. No repair survived. All producer
  checks passed, but importing the consumer failed across all seven seams.
- **C2 — discovery loop, no migration.** Producer called `onboard` six times and
  `start` twice, repeatedly saying it would enroll, but never did. No CLI error
  caused this loop; native loop detection stopped it. Consumer implemented against
  old representations, passed the existing local suite and released. Its final
  claim of working labels did not satisfy the frozen migrated-data checks.
- **C3 — source reconciliation worked.** Both enrolled. Consumer initially used
  stale imports, encountered an import error, read the changed producer files and
  replaced its own presentation implementation. It then checked all 15 label
  examples and the existing suite. Both released, and the independent checker
  accepted 7/7. One shell-helper syntax error was corrected. No repair claim/ack
  was used, and no competing implementation repair was observed.

### Separate PI UX defect observed, not repaired

C1 combines worker misuse with an actual unsafe command interaction: legacy
`presence` writes to the same session record without enrollment fields, while
`enroll` renewal assumes an active prior record contains `claimed_at`. Evidence is
the successful `presence` output, the resulting record, subsequent CLI errors,
and the frozen paths in [CLI](../../project_intent/cli.py) and
[enrollment](../../project_intent/enrollment.py). No production repair was made
during or after this batch. The compact prompt does not instruct `presence` use.
The initial refusal to obtain acknowledgment from an inactive peer was expected
behavior, not the same defect.

## Measured execution

```text
Seconds from each project's worker launch; P = producer, C = consumer

C1  P  0 ├─────────────────────────────────┤ 129.339  loop guard
    C  0 ├──────────────────┤                70.822  exit
       43.3 first consumer write; 51.4 producer migration writes
       70.6 producer reads stale consumer; 76.1 repair claim refused
       84.2 presence overwrites enrollment; 89.0 first renewal failure
       Final verification: 129.917s → 0/7

C2  P  0 ├──────────────────────┤ 83.628  discovery loop guard
    C  0 ├──────────────────┤     69.718  exit
       Final verification: 83.979s → 0/7

C3  P  0 ├──────────────────────┤     86.935  exit
    C  0 ├──────────────────────────┤ 102.961  exit
       48.0 initial consumer write; 54.7 consumer import error
       61.9 consumer reads migrated files; 70.5 replacement write
       Final verification: 103.227s → 7/7
```

Maximum simultaneous workers: two in every project. Concurrency factors were
**1.548, 1.834, 1.844** for C1–C3. C3 retained distinct producer/consumer work but
also required one stale-consumer rewrite. C1 retained incompatible contributions;
C2 had only one implementing worker. Overlapping processes alone are not useful
concurrency. No precise duplicate-effort percentage is inferred from these logs.

## Comparison and next question

| PI instructions, thinking off | Accepted | Accepted-project time | Accepted-project input + output |
| --- | ---: | ---: | ---: |
| Previous full prompt | 1/1 | 146.669s | 1,983,581 |
| Compact prompt | 1/3 | 103.227s | 1,289,644 |

The compact success took **43.4s less**, but two failures prevent calling this a
reliable improvement. The 103.227s all-run median includes failures and must not
be presented as median time to a correct project. These are small, unequal,
sequential samples without exclusive model reservation, not a causal speed claim.

**Suspected remaining problem:** shortening startup text leaves large command
responses and multiple workflow transitions; it did not prevent repetitive
discovery, premature handoff or misuse of a mutating presence command. A next,
separately authorized version should test whether a smaller, explicit
next-action/response surface prevents those protocol failures while preserving
final source reconciliation. Fixing the presence/enrollment interaction would
need its own recorded backend version, not a silent treatment change. No further
model run is scheduled.

## Evidence and validation

Batch `20260909-qwen-compact-pi-v1`; local raw recordings remain outside Git.
Frozen hashes and per-project result hashes are in the public ledger.

- Template: `e2449ccc6ede1f0568e021da0603688d728f267d627d4339dc05ed29608b32c2`.
- Recorder: `b80b6549f20364d1b65cd02ea051e1eb7ca0b1c02abdaa11dea0b6e5468df7c0`.
- Batch: `f350ad8e1ce6695ec650a4333a29a2d8b4c150d1f10d9e39313b19d3279bfb34`.
- Before execution: **24 focused tests; 393 total tests passed**, plus all three
  native/isolation preflights. Frozen inputs verified again after execution.

Acceptance is observed after worker exit, not continuous time-to-first-correct.
Archive and final checker durations are recorded separately. Inherited
`setup_seconds` excludes the compact instruction rewrite/recommit, so it is not
an all-inclusive setup measurement. Worker/project execution timings are unaffected.
