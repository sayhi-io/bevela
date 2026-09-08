# Record a user-assigned task

Repository enrollment makes a project's context discoverable; it does not pre-create
every future task. A worker may record work the user has already assigned through
the configured local `task-register` capability. Creating that record is bookkeeping,
not inventing work, transferring ownership or obtaining new execution authority.
No separate coordinator queue or human ID lookup is needed.

## Worker flow

First use `onboard --query "task keywords"` from the actual checkout. Broaden the
search and inspect candidates against the user task, native owners, scope, exclusions
and acceptance. Already enrolled in the correct assignment? Renew your own lease.
An empty snapshot search is not proof that native inventory has no matching issue.

If no cached candidate fits, prepare a bounded JSON file **outside tracked source**:

```json
{
  "title": "Short descriptive title of the actual task",
  "statement": "What the user asked this worker to accomplish",
  "scope": "Bounded implementation or investigation scope",
  "acceptance": ["Observable acceptance criterion from the task"],
  "boundaries": ["product/affected-seam"],
  "avoid": "Explicit exclusions; no unrelated work",
  "authority_ref": "Short reference to the user's instruction in this thread"
}
```

Do not include credentials, private transcripts, customer data or invented readiness
claims. `authority_ref` records the worker's assertion, not authenticated proof.
Use the scope of the repository actually owning the work; a neighboring product's
scope is not a substitute. The command checks configured checkout roots.

```sh
project-intent task-register --scope SCOPE --input /private/task.json
```

This default **read-only preview** reads live native inventory, including unannotated
issues, native lifecycle, assignees/delegates and existing metadata. Review it:

- If a native issue fits, preview again with `--native-identifier NATIVE-ID`.
  An annotated workstream will be reused unchanged. An unannotated issue will receive
  the supplied task metadata; native title, description, owners and lifecycle remain.
- If none fits, omit `--native-identifier` to create the missing native record.
- If ownership or scope genuinely conflicts, resolve that conflict; don't borrow an
  assignment because its title looks similar. Workers perform routine inventory review
  themselves, without asking the human to copy a digest or approve bookkeeping.

Submit the reviewed choice using the returned digest:

```sh
project-intent task-register --scope SCOPE --input /private/task.json \
  --submit --inventory-digest DIGEST
# Include the same --native-identifier if used for that preview.
```

The digest binds the scope, task, selected target and inventory. It is checked again
at the final inventory read under the common reconciliation lock, before mutation.
A changed inventory requires another preview. Exact normalized-title/alias duplicates require explicit
selection; semantic matching remains the worker's responsibility, not a guarantee
from keyword search. Creation sets readiness to unknown and native lifecycle to the
provider's unstarted column. It does not claim another native user as the worker.

On `state: registered`, run `onboard --scope SCOPE --workstream RETURNED-ID`, inspect
orientation/nearby work, then explicitly `enroll` your own session with actual access,
paths and seams. Registration itself neither enrolls nor dispatches a worker.

## Failure and retry

Keep the original task file and selected native identifier for retries. Registration
stores an exact packet before writing remotely, so branch/HEAD/session changes do not
change the provider operation identity. Concurrent registrations sharing the local
journal serialize; no distributed compare-and-swap is claimed.

- `registered-refresh-pending`: native registration was confirmed, but the shared
  snapshot could not be refreshed or no longer contains the task. Retry the identical
  submission: the saved native receipt makes this refresh-only, even if metadata has
  advanced or the issue disappears. It never recreates a missing issue. Resolve a
  persistently missing native record with the operator; don't fabricate a snapshot.
- `uncertain`: native creation or metadata writing may have succeeded. Retry only
  the identical task/target, previewing fresh inventory and supplying its new digest
  before another potential mutation. The reconciliation journal looks for its receipt;
  if no receipt can be established, it stays uncertain without repeating creation.
  An authorized operator must resolve that particular provider outcome.
- Policy unavailable, native permissions denied or conflicting records: report the
  exact missing capability/conflict. Don't scavenge credentials or write the database.

A bookkeeping gap is not itself revocation of the user's development authorization.
Keep it explicit and continue otherwise-authorized work unless the task has an
explicit enrollment/admission prerequisite or the unresolved issue is actual scope,
ownership or execution authority. Never claim tracking succeeded when it did not.

## Local capability configuration

This is an opt-in CLI route in the existing same-user cooperative deployment, **not**
credential isolation from hostile local code, delegated remote worker authentication,
or a browser mutation API. Operator configuration retains provider credentials. The
launcher supplies its path through `PROJECT_INTENT_REGISTRATION_CONFIG`, or a local
operator supplies `--registration-config`. Discovery/enrollment remain credential-free.
Do not broaden `operator.allowed_scopes` merely to enable task registration.

The private service config adds a separate policy, for example:

```json
{
  "task_registration": {
    "journal_directory": "/private/project-intent/task-registration",
    "checkout_roots": {
      "sayhi/example": [
        "/workspace/repos/example",
        "/workspace/worktrees/example"
      ]
    }
  }
}
```

Each enabled scope must already have exactly one configured `itsaplan` provider,
its own cache, and a native token able to read/create issues, comment and set the
Project Intent field in that project. The configured
`operator.journal_directory` remains the common reconciliation journal, without
requiring general operator grants. Registration and reconciliation journals must
use distinct lock directories and be preserved across upgrades. Workers using a scope map must reference the same
snapshot path as the scope's service cache; the CLI checks this before writing.

Choose roots per project, never one broad workspace root for all scopes. The command
observes the actual Git checkout and checks resolved path containment. This check is
a cooperative routing guard, not a repository identity or hostile-code boundary.
Enable new scopes deliberately; no provider permission or policy is auto-created.

Source installation, local configuration/activation, Git integration and production
deployment are separate. A command present in a source worktree is not evidence that
the pinned workspace launcher already supports it.
