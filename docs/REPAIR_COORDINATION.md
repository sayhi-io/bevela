# Agree on the repair, not ownership of the seam

Use this only when workers could make competing fixes to a specific break. Ordinary
assigned edits need no repair claim just because another worker shares a seam.
A neighboring assignment is not an edit prohibition or a promise to fix your change's
consequences. Preserve both tasks, within actual user authorization and exclusions.

Keep your existing CLI, worker-config, scope and checkout. The start/enroll commands
show repair plans; repair-status refreshes them and checks reported source hashes
in your own checkout. Look for the actual break and reuse its repair_id. Different
wording is not a reason to create another plan for the same break.

## One accepted repairer, explicit peer agreement

The volunteer describes the break, repair paths, affected peers and files to validate:

    project-intent repair-claim --scope SCOPE --workstream MY-TASK --session ME \
      --seam SHARED-BOUNDARY --problem 'Specific failure and expected behavior' \
      --repair-path affected/consumer.py --peer-session OTHER-WORKER \
      --check-path affected/consumer.py --check-path producer.py --check-path test_boundary.py

accepted: true means this worker volunteered; it is not agreement.
ready_to_edit: false means the named peers have not acknowledged.
Peers inspect the plan and explicitly agree that its named repairer handles it:

    project-intent repair-ack --scope SCOPE --workstream MY-TASK --session ME \
      --repair-id RETURNED-ID --expected-revision INSPECTED-REVISION

Only a named peer can acknowledge its own participation. Requesting a competing
claim does not silently acknowledge the other plan. Once all named peers acknowledge,
the state is claimed; the owner refreshes its claim to see ready_to_edit: true.
Only that owner performs the agreed repair. Peers avoid those repair edits while
continuing independent work, including other paths on the same seam. Claims contend
on overlapping paths, not boundary-name equality. Shared files are conservatively
serialized; independent hunks within one file are not modeled.
Repair paths/ancestors cannot be symlinks, and hard-linked repair files require
alias reconciliation; alternate names must not select two repairers for one file.

If the plan is wrong, don't acknowledge it. Its owner stops writes and uses
repair-release --claim-id TOKEN, then proposes the corrected plan. Every new plan
requires fresh acknowledgment. No self-ack, automatic takeover, or acknowledgment
inferred from silence/expired presence. If agreement is unavailable, report the exact
unresolved issue through the authorized coordination route; don't spin or claim success.

## Close the break, not just the paperwork

After relevant producer changes land, validate the agreed producer/consumer behavior
against both tasks. Then the owner runs:

    project-intent repair-complete --scope SCOPE --workstream MY-TASK --session ME \
      --repair-id RETURNED-ID --claim-id TOKEN --evidence 'Actual checks run and results'

Completion requires peer agreement, evidence and the agreed files; it cannot silently
narrow validation to only the owner's tests. Source hashes bind the reported result;
subsequent changes to listed files require revalidation. A specific remaining failure
can reopen a resolved plan with repair-claim --repair-id ID --expected-revision N
--evidence 'remaining failure' and a new plan/acknowledgment. Checks are worker
assertions, not independent execution or proof of sufficient coverage. Unlisted
dependencies and other worktrees remain unverified.

Before handoff, reconcile the current result: don't report a stale failure after the
peer repaired it, or call your change complete while its known regression remains
unresolved. A claim, acknowledgment, presence release or report is not the fix itself.

## Limits

Records live under the local enrollment feed's repairs/ directory, outside Git.
This is cooperative local-account coordination, not PM assignment, automatic
notification, a scheduler, filesystem fencing, or protection from hostile same-user
code. Workers must read context at relevant transitions; PI does not force compliance.
Only the same configured scope feed and local repository participate. No other
checkout is read for validation; cross-worktree integration still needs its authorized
owner. Missing/corrupt/unreadable feeds fail closed; 128 records per feed are supported.
Old version-1 claims have no peer acknowledgment and cannot be treated as agreed:
reconcile using their original CLI, never silently overwrite unresolved records.
Browser/API mutation and automatic release activation remain outside this feature.
