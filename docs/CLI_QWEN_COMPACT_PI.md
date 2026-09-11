# Compact PI startup · Qwen experiment v1

[Completed results](results/qwen-compact-pi.md): **0/7, 0/7, 7/7**;
thinking off, two concurrent workers per project, no timeouts.

Three sequential projects, two concurrent native workers per project. Original
producer/consumer role prompts, original non-torture seven-seam fixture and
observer-only acceptance checker. Qwen Code 0.23.2, thinking off, confidence off,
PI on, 230k context, unchanged sampling/output budget and worker deadline.

Treatment: replace only disposable `AGENTS.md` with
[the compact checklist](../experiments/qwen_compact_pi.md). No project/vendor
references, task solutions or evaluator hints. It retains discovery, exact task
selection, enrollment, shared context, current-source reconciliation, agreed
repair ownership, validation, handoff, release and authority boundaries.

The checklist replaces mandatory full-skill reading with on-demand documentation.
It names the real `start` refresh command and uses a relative CLI shell helper
instead of repeating installation-specific paths. Thus this is a **compact UX
bundle**, not a word-count-only ablation. Backend, skill, operational documents
and native inventory requirements remain unchanged and available. Workers may
still choose to read long docs; measure that instead of suppressing it.

All three source/session/profile plans freeze before C1. The generated pre-compact
Git history and baseline are preserved outside the worker namespace; the worker
checkout starts with one fresh compact-instruction commit, so Git does not expose
the superseded startup text. No production change or historical evidence rewrite.

```sh
.venv/bin/python -m experiments.qwen_compact_pi freeze /absolute/new-batch \
  --runtime /absolute/verified-qwen-runtime --endpoint http://resolved-host:8078/v1
.venv/bin/python -m experiments.qwen_compact_pi run /absolute/new-batch
```

Compare integrated correctness, elapsed project/worker time, token usage,
enrollment/refresh failures, documentation reads and duplicate repairs against
the preceding full-instruction thinking-off PI project. That control has only one
run; do not infer reliability or pure prompt-length causality from unequal samples.
Preserve all failures. No mid-batch tuning, replacement trials or evaluator repair.
