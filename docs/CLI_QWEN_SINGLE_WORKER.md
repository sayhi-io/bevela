# Qwen single-worker diagnostic · v1

Three sequential fresh ordinary projects, A1–A3. One native Qwen Code **0.23.2**
session receives the existing `concurrency_study.py` combined prompt verbatim:
`Complete both tasks below in this session.` followed by the original producer
and consumer task texts. No prescribed implementation order or extra hints.

Use the original non-torture seven-seam fixture and observer-only acceptance
checker unchanged. Profile: `qwen38-27b-dflash2`, thinking off, confidence off,
PI off, 230k context, native generic effort `none`, explicit provider Medium plus
`enable_thinking: false`; output cap 32768, temperature 0.6, top-p 0.95 and native
compaction unchanged. Each project retains the 1800s worker boundary.

`experiments.qwen_single_worker` extends the existing Qwen recorder using private
module instances. It selects only the solo role, a fresh UUID and native home.
It preserves the existing source observer, isolation, token/transport evidence,
post-exit checker, once-only launch markers and sequential batch integrity fences.
No PI files/instructions or prior trial artifacts are visible to workers.
Native tools remain unchanged; inspect logs for any self-delegation rather than
assuming one harness-launched process guarantees no delegated work.

```sh
.venv/bin/python -m experiments.qwen_single_worker freeze /absolute/new-batch \
  --runtime /absolute/verified-qwen-runtime --endpoint http://resolved-host:8078/v1
.venv/bin/python -m experiments.qwen_single_worker run /absolute/new-batch
```

All three source/session/profile plans and recorder hashes freeze before the
first execution. No retry, coaching, extra repair session or failure replacement.
Infrastructure ambiguity stops progression. A failed software check alone does
not stop the remaining authorized repetitions.

The question is whether a coherent single no-thinking worker can solve both sides
without PI. Report all three integrated scores, native/project durations, tokens,
failed seams and self-rework. Compare separately with the preceding one ordinary
two-worker and one PI two-worker thinking-off project; unequal sample sizes and
fixed temporal order do not establish a general causal effect.

The single worker receives the union of both assignments. Each ordinary concurrent
worker received only its original role task plus normal shared source inspection;
therefore this is a single-session ceiling diagnostic, not a pure worker-count
ablation with equal per-worker context. No fixture or acceptance change is allowed
after observing results. PI production behavior remains untouched.
