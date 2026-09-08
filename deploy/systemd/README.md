# Independent service-account migration candidate

Production candidate not activated. An isolated offline account canary passed
and is stopped; see VALIDATION.md. This preserves the current read model and authentication
behavior; it adds no SPIRE dependency, provider mutation or execution authority.

Target: locked dedicated `project-intent` system account, no sudo/docker/libvirt
membership. Root-controlled release and unit; mutable cache under /var/lib/project-intent.
The admitted marker is a root-controlled deployment interlock only, not evidence
that checks were performed and not an authorization mechanism for application work.

Before cutover:

1. Seal the running release, including UI bytes. Build that exact release into a
   new final-path venv under /opt/project-intent; do not silently replace it with
   main or relocate a venv whose entry-point shebang still uses the operator home.
2. Enumerate all configured scopes and principal grants without printing secrets.
   Stage root-owned config at /etc/project-intent/config.json, group-readable only
   by project-intent (0640). Provider credentials must be explicit, minimally
   scoped service credentials in similarly protected paths, not operator admin keys.
3. Stage caches under /var/lib/project-intent, preserving scope binding and captured
   timestamps. Config writes remain root-only; only cache/state writes belong to
   the service. Snapshot export is not a replacement for provider backup.
4. Current local worker registrations, reports, telemetry and workspace inventory
   depend on human-owned paths. Define exact read-only feed access and producer
   write access before enabling ProtectHome=yes. Prefer sanitized exported
   observations, not exposing raw Codex homes/transcripts. Read-only permissions
   do not make a producer's data authenticated. No blanket home ACL, bind mount,
   recursive chown, or silent loss of currently enrolled coverage is acceptable.
   The installed file readers must be tested with the chosen feed design.
5. Verify private access to every configured provider and exact observation feed.
   Provider outage retains last-known scope state and freshness labels. SparkOps
   outage must not stop PI. Offline CLI bootstrap must still find its scoped data.
6. Test candidate with isolated cache copies on a different loopback port; compare
   authorized scope coverage, totals and detail, treating live timestamps separately.
   Test unauthenticated 401, unauthorized scope 403, provider fallback, writes denied
   to release/config and unavailable observations represented truthfully.
7. Independent review, then stop old user service, final-sync owned cache state,
   and start candidate on 8290. Disable old unit only after verification. Preserve
   original credentials, unit and state for rollback. Never have two writers sharing
   one cache while comparing services.

Rollback: stop candidate, preserve any new local evidence and cache timestamps,
restore the old unit/enablement and old port ownership; do not overwrite newer
reports with a stale backup. After acceptance, document startup and exercise
restart/boot recovery in an approved maintenance window. No broad service outage
or credential rotation is performed by this candidate package.

SPIFFE may later authenticate PI to appropriate services but must not make its
offline orientation depend on SparkOps or a live SPIRE server. Unix identity and
file isolation are useful independently of network workload identity.
