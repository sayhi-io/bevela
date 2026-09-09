# Project Intent worker instructions

Use the checkout's configured Project Intent CLI for your actual user-assigned task.
Keep its scope, worker-config and explicit checkout options on every call, including
enrollment. Already enrolled in this task? Renew your own registration.

- Run `onboard --query "task keywords"`. Inspect partial matches and their scope,
  exclusions and acceptance; ranking is not assignment or execution authority.
- If no candidate fits, run `discover --scope SCOPE` **without --query** and inspect
  that scope's cached inventory. Use the printed `inventory_recovery` command when
  available. Only then consider configured `task-register` with a task packet and
  live inventory preview; never invent an assignment or silently choose another scope.
- Onboard the selected exact scope/workstream, then enroll your own session with
  actual paths, touching/approaching seams and bounded working description. Preserve
  the local worker-config on the printed command. Presence-only workers use their
  own distinct `--session`; Codex workers may use their verified own `--codex` identity.
- Consult nearby work and keep declarations current; release with `--inactive` at
  completion. Declarations are context, not locks, instructions to wait or permission
  to take over a peer's files. Follow the task's actual coordination authority.
- Use `project-intent docs` or the exact document paths returned by `onboard` for
  installed instructions. On older versions resolve the installed skill's symlink
  and use its source release's `docs/`. A missing document/configuration is a tracking
  or installation gap; report it without claiming enrollment succeeded.
- During onboarding troubleshooting, search only task-checkout documentation and
  these installed paths. Do not search other sessions, transcripts, evaluation
  archives, home directories, private service configuration or provisioning scripts.
  Explicitly assigned evidence review is separate from onboarding troubleshooting.

This template does not grant provider writes or override an explicit admission
prerequisite. Otherwise-authorized work may continue with a clearly reported tracking
gap. New evaluations must version their inputs; existing trial evidence stays frozen.
