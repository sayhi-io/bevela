# Project Intent integration gate

The immediate work is the real `sayhi/project-intent:PI-MISSION-01` continuation:
supported reporting, provider reconciliation, optional local session continuation,
and a reusable worker/orchestrator skill. The mature SparkOps consumer bridge is
task 6, deferred in [its decision record](SPARKOPS_CONSUMER_BRIDGE.md).

## Independent review and reproducibility

An independent worker uses `skills/project-intent/SKILL.md` to discover/start the real
assignment and enroll a unique inspection session. Its task is to review the current
delivered source and report concrete findings/evidence. No fictional workstream,
invariant amendment, coordination request or finding is needed.

The initial source checkpoint was an unborn branch with no remote, so its evidence
was correctly reported as an **isolated source-copy validation**. That source is now
committed and merged into `main`. The historical approval covers only the exact
recorded source seal; subsequent changes, including UI experiments and deployment
candidate work, require their own review and validation.

1. Read the repository instructions and operational contracts, including REPORTING.md
   and SESSION_CONNECTOR.md. Review scope filtering, publication receipts and failure
   recovery, session identity/checkout binding, duplicate continuation handling,
   snapshot independence and the read-only HTTP boundary.
2. Inspect `git status --short --untracked-files=all`. Assemble an explicit reviewed
   newline-separated source list outside Git. Include application source, tests,
   pyproject.toml, docs, bootstrap instructions, `.github/workflows/check.yml`, the
   complete skill package, and `.project-intent/snapshot.json` where tests require it.
   Exclude credentials, `.env`, runtime state, logs, evidence, caches and environments.
   The helper limits eligible paths but does not prove absence of embedded secrets;
   review the selected content. Record intentionally omitted files.
3. Run `skills/project-intent/scripts/seal_source.py --source ACTUAL_CHECKOUT
   --files REVIEWED_LIST --output NEW_PRIVATE_OUTPUT`. The output must not exist and
   must be outside the source checkout. Record its manifest SHA-256 and file count.
4. In that output's `source` directory, create its own `.venv`, install the package
   from its own pyproject.toml, and run `.venv/bin/python -m unittest discover -s
   tests -v`, plus `node tests/test_identity_display.cjs` and JavaScript syntax checks.
   Tests needing Git should construct an isolated test repository; never borrow the
   original checkout's `.git` or `.venv` to make a portability failure disappear.
5. Run the skill creator's `quick_validate.py` on the copied skill where available.
   Exercise the actual supported report/status flow on this review assignment. The
   authorized publisher may publish that report separately; a local outbox receipt
   must not be called a provider comment. A harmless continuation to a consenting
   existing worker may verify delivery; queue acceptance is not completion.
6. Run the browser validation using its documented optional test environment against
   scoped real state and an isolated unavailable-provider instance. Do not stop a
   product, provider or production service to manufacture outage evidence.
7. Run the seal helper's `--verify OUTPUT` after checks. Record dependency-install
   output, test results, review findings, limitations and exact manifest hash. Route
   bounded corrections to implementation owners, then seal and reverify changed
   source before final approval.

The helper may be invoked with the checkout-owned Python. It creates only an
explicit source copy plus a manifest and never reads provider credentials or invokes
Git, a service, or the network. The manifest binds listed files; it does not assert
that a selection is complete or that later generated build files are part of source.

## Handoff and remaining gates

Report source reviewed, local validation, independent findings/corrections, actual
CI status, commit state, merge readiness and production authorization separately.
Provider publication confirms durable delivery, not acceptance of assertions. Record
remaining project-information gaps separately from Project Intent defects.

The inherited `CODEX_THREAD_ID` observed in this multi-agent harness is a concrete
identity hazard: a child worker uses its own explicit unique presence-only session
unless a distinct Codex thread identity is independently established. No parent
telemetry may be attributed to a child. Treat this as a documented integration
constraint; it does not prove a particular worker caused any registration overwrite.

After source integration, repeat validation from the actual committed checkout and
obtain required CI evidence for each substantive change. The checked-in workflow is
a definition, not proof CI ran. Local service activation is also separate from
source integration: the loopback dogfood process uses a pinned runtime release.
No public deployment or production activation follows automatically from this gate.
