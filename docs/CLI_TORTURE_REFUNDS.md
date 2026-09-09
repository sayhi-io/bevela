# Refund migration concurrent-edit study — v1

Completed results: [refund migration](results/refunds.md) · [all studies](../RESULTS.md).
The text below records the initial no-PI protocol; later Medium control and PI
batches are separately identified in the result history, with unchanged acceptance.

Two native workers share a small functioning shop. One changes the monetary,
inventory and persisted representations; the other extends full refunds into
partial refunds, durable retry safety and accurate receipts. Their tasks naturally
touch purchase/refund, save/load and receipt code in the same module. Workers may
restructure code or avoid interference; no edit order or collision is imposed.

Seven correlated post-exit groups cover units, preserving both features, refund
rounding/conservation, inventory/reservations, durable request identity, schema/history
preservation, and receipt invalidation. Checks are derived from the worker prompts
and existing README contracts. A joint reference solution passes all groups; seven
deliberately defective variants demonstrate that the relevant groups detect failure.
The original fixture passes its existing public-contract tests and fails the new
combined requirements. Reference code is oracle-test material, never a worker input.

The harder structural condition is shared mutable implementation: both assignments
can change the same functions and serializers, instead of one changing storage while
the other mostly calls stable helpers. This does not guarantee a race or prove that
an observed failure was caused by another edit; review recorded commands/patches
before attributing causation. Runtime request sequences exercise the resulting code;
there is no requirement for application-level multithreading.

## Exactly one authorized no-PI trial

```
.venv/bin/python experiments/torture_refunds.py prepare --model gpt-5.6-luna --effort high
.venv/bin/python /returned/trial/recorder.py run /returned/trial
.venv/bin/python /returned/trial/recorder.py check /returned/trial
```

Preparation copies only the fixture, individual prompts, recorder and frozen checker
into a private temporary trial. The worker checkout contains no PI instructions,
inventory, reference solution, or post-exit checker. Native Codex config/environment
are inherited; host reads are not hermetically isolated. Check completed native logs
for actual model/effort and unintended PI/reference/checker use.

Execution reuses the existing command/record/manifest functions: two concurrent native
Codex sessions, each with its own task prompt, exact argv/stdout/stderr/timing and
before/after bytes. No intermediate feedback, follow-up prompts, owner selection,
deadlines, retries or automatic next trial. Scoring executes a disposable copy after
both workers exit and never modifies archived output. The scorer timeout is not a
worker timeout. Preserve byte differences and concrete failed assertions, not just
one opaque success number. At initial preparation this fixture had no matched PI
result; subsequent runs are linked above. Old seven-label scores are a different
experiment. Implementation and running trials do not
authorize commit, push, merge or service activation.
