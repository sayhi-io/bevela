# Project Intent ownership and startup

Human-interface rule: never add emojis. Use restrained vector icons, readable
typography and visual grouping where they aid scanning. Preserve all underlying
data; progressive disclosure may hide technical detail, never omit it or imply
that a declaration is verified conformance.

This is SayHi's independent development-intent capability, not a SparkOps plugin.
Read README.md and docs/ARCHITECTURE.md before substantial work. Use the repo-backed
`skills/project-intent/SKILL.md` (also installed as `$project-intent` in this workspace)
for worker and orchestrator startup/reporting. Existing sessions should read it
explicitly; installing a skill does not retroactively load it into their context.
The initial real
assignment is `sayhi/project-intent:PI-MISSION-01`; scope and authority remain in
the provider. Use `project-intent start --snapshot .project-intent/snapshot.json
--workstream PI-MISSION-01` for bounded offline orientation after installation.

Use a checkout-owned `.venv`; tests are standard-library unittest. Do not import
SparkOps or other product runtime packages. Preserve the original SparkOps CLI as
fallback; this is an explicit parallel service, not a silent migration.

Provider credentials, access credentials, live presence, and service state stay
outside Git. Every API data read must filter scopes before computing context.
Missing/expired observations never mean available, safe, or authorized. Do not
turn matching revision declarations into verified conformance. UI is read-only;
no HTTP dispatch or PM mutation endpoints. Authorized local CLI publication,
reconciliation and explicit session continuation follow docs/REPORTING.md and
docs/SESSION_CONNECTOR.md. Mature SparkOps execution admission is deferred task 6
in docs/SPARKOPS_CONSUMER_BRIDGE.md.

Record evidence, exact source/artifact hashes, review, and remaining readiness with
`report`; an authorized `publish-report` operation creates the native comment.
Preserve local/pending/published/uncertain distinctions; publication does not certify
claims or rewrite provider readiness. Coordinate with Environment Catalog through profile
references, not by owning provisioning. Keep reviewed source, local tests, actual
CI, merge and production activation separate.

Before substantial work, use `start` for your actual assignment, then `enroll`
after first running `discover` from your actual checkout to find relevant work.
Do not ask the human to look up an ID. Use task text, exact reference match and
native delegate information to identify candidates; inspect scope/avoid/acceptance
with `start`, then select the existing alias or native identifier. Similarity is
not assignment authority; resolve true ambiguity or missing enrollment explicitly.
Declare `--access edit --touching-path ...` or `--access inspect`, current semantic
seams, approaching seams and exclusions. Enrollment captures your own Git root,
branch and HEAD; never substitute another owner's source reference. Inspect nearby
local workers and route around overlap when possible; declarations are not locks,
as documented in README.md. Workspace `bin/project-intent` supplies the local
credential-free scope map. For Codex, `enroll --scope sayhi/project-intent
--workstream PI-MISSION-01 --codex --working "bounded task"` advertises this
initiative's worker only; do not enroll another owner's work on their behalf.
Subagents may inherit a parent's CODEX_THREAD_ID; use a distinct explicit
`--session` presence-only identity unless your own Codex thread is established.
Renew at meaningful transitions (one-hour lease); release with the same command
plus `--inactive`. Enrollment does not create PM assignments or grant execution.

Independent integration review follows docs/INTEGRATION_GATE.md. An unborn repository
can support a sealed isolated source-copy test, not a clean committed Git checkout
claim. Keep source sealing, independent review, actual CI and production separate.
