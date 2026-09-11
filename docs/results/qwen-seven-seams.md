# Qwen Code Medium · original seven seams

[All results](../../RESULTS.md) · [Frozen method](../CLI_QWEN_SEVEN_SEAMS.md) ·
[Per-worker measurements](qwen-seven-seams-measurements.json)

**Ordinary: 3/3 accepted. PI: 2/3 accepted. All 12 workers finished; zero timeouts.**

```text
ORIGINAL SEVEN SEAMS / QWEN MEDIUM
================================

                  Round 1       Round 2       Round 3
Without PI        ####### 7/7   ####### 7/7   ####### 7/7
With PI           ####### 7/7   #####.# 6/7   ####### 7/7

# preserved seam   . failed seam (Contacts)
```

This small batch **does not show a PI benefit**. Ordinary Qwen completed every
project and was faster in each numbered comparison. PI's failed project retained
a stale display-name lookup despite both workers enrolling. Additional context,
protocol work and repeated validation may explain some of the elapsed-time cost;
the run logs do not isolate their individual contributions. A future focused test
should determine whether workers reconcile live `CONTACTS.display_name` rather
than trusting the legacy `NAMES` mapping after reading peer context, before another
larger study. No PI fix or extra trial was performed here.

## Project results

Executed **September 9, 2026, 20:04:22–20:45:36 UTC**, about **41m 14s** for the
sequential cohort. Two native Qwen Code workers ran concurrently inside each
project; projects never overlapped. All actual recorded requests used the same
local model, literal Medium effort, thinking enabled and 32,768 output limit.

| Condition | Accepted | Scores | Median project elapsed, all runs | Median aggregate worker time | Median input + output tokens |
| --- | ---: | --- | ---: | ---: | ---: |
| Ordinary | **3/3** | 7, 7, 7 | **3m 51s** | 4m 57s | 430,459 |
| PI v0.05 | **2/3** | 7, 6, 7 | **10m 9s** | 15m 26s | 1,910,569 |

The table includes the failed PI project; its elapsed time is not time to a correct
result. Among **accepted projects only**, ordinary median project time was
**3m 51s** (n=3), versus **10m 14s** for PI (n=2). Corresponding median observed
input + output counts were 430,459 and approximately 1,778,690. Tokens include
cached inputs, not billable cost estimates; cached input and reasoning are subsets,
not additional tokens. All workers had complete recorded input/output usage.

### Every project · newest first

All workers exited zero with correlated native final receipts. Each run had two
overlapping top-level workers, no timeout, no recorded transport failure and no
human repair. The checker ran once on an isolated final copy, not inside the
worker loop.

| Project | Score | Project elapsed | Producer | Consumer | Input + output tokens | Failed seam |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| C3 · PI | 7/7 | 10m 3s | 2m 58s | 10m 2s | 1,571,447 | None |
| B3 · ordinary | 7/7 | 3m 54s | 3m 54s | 1m 4s | 430,459 | None |
| B2 · ordinary | 7/7 | 3m 51s | 3m 51s | 1m 9s | 486,782 | None |
| C2 · PI | **6/7** | 10m 9s | 5m 52s | 10m 8s | 1,910,569 | **Contacts** |
| C1 · PI | 7/7 | 10m 25s | 5m 1s | 10m 25s | 1,985,932 | None |
| B1 · ordinary | 7/7 | 2m 51s | 2m 50s | 50s | 410,121 | None |

Times are rounded independently. Exact timings, producer/consumer checks, usage
coverage, concurrency intervals, source identities and evidence hashes are in the
linked ledger. The initial preparation was rejected **before any model execution**
and retained separately; it is not a seventh project or a replaced failed trial.

## The one failure: a stale name, not a broken import

C2 preserved all producer checks and every other seam. Its consumer used:

```python
from customers import NAMES, email

def contact_label(customer):
    return f"{NAMES[customer]} <{email(customer)}>"
```

The producer retained `NAMES = {"ada": "Ada", "lin": "Lin"}` alongside the new
structured `CONTACTS`. When the frozen checker changed Ada's contact record, the
email updated but the label still read the old name:

```text
Expected: Ada Lovelace <ada2@example.test>
Actual:   Ada <ada2@example.test>
```

Both C2 workers enrolled and released with explicit edit paths. That establishes
observed PI participation, not full protocol compliance or successful integration.
The new display-name representation was available in the producer task carried
by PI; the delivered consumer still used the legacy mapping. This is observable
stale-contract behavior, not proof of a particular internal reasoning cause.

Ordinary B1 also illustrates why control success must be retained: its producer
reread and rewrote `presentation.py` after the consumer's contribution, then checked
the integrated result. That repair arose from native source inspection, not a
message or solution supplied by the evaluator.

## Scope and limits

- Qwen Code **0.23.2**, `qwen38-27b-dflash2`, Medium, **230k** context, native
  automatic compaction enabled, 30-minute worker ceiling. Served on DGX1+DGX2;
  the failed DGX3+DGX4 launch was not used for these projects.
- Original non-torture fixture, role prompts and seven-seam checker unchanged.
  Ordinary workers received their own task and shared source; PI additionally
  exposed peer task context through its frozen workflow. This is not the later
  equal-static-information concurrency ablation.
- PI behavior **v0.05 unchanged**; native Qwen session wording and restricted
  operational documentation only. No production PI modifications, evaluator
  coaching, hidden repairs, retries, stronger-model rescue or changed acceptance.
- Compared with the earlier distributed Qwen cohort, **fixture, worker count and
  effort all changed**. Zero timeouts here does not establish which change was
  responsible. Three projects per arm are exploratory, not population estimates.
- Source and reports are local; this report does not claim remote CI, merge or
  GitHub publication. Frozen manifest:
  `fe378b77345b414204d50601d3d3ce400f0fe5c79d4fdefe97bc9d3ecbe11b45`.
