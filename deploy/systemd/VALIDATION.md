# Dedicated-account canary — 2026-09-06

Main source baseline f57251e is older than the running UI release at
state/project-intent/releases/workspace-inventory-20260906/source.
Copied its actual package/UI bytes; did not deploy main over the running UI.
Normal user service project-intent-dogfood.service and port8290 untouched.

## Isolated deployment

- Locked non-login project-intent account, no supplementary groups.
- Root-controlled final-path venv:
  /opt/project-intent/releases/workspace-inventory-account-fix-20260906.
- Separate /var/lib/project-intent-account-canary state. Only cache writable by
  service. Root-owned config/inputs group-readable; canary secret root-only.
  No production provider or operator credentials copied.
- Runtime-only project-intent-account-canary.service on127.0.0.1:18290 with
  candidate sandbox, ProtectHome=yes and empty capabilities.
- 20 real snapshots retained with input hashes in canary manifest. Offline
  snapshots remain non-authoritative for remote PM state.

## Bounded corrections

1. read_registrations raised PermissionError during directory inspection; API
   mislabeled it scope denial. Source now reports unavailable feed; two regressions.
2. Running-release workspace_inventory.observe called is_symlink outside error
   handling, disconnecting HTTP for inaccessible roots. Now reports unavailable.
   This module is absent from main f57251e: narrow patch preserved as
   workspace-inventory-permission.patch, applied to staged release only. No
   wholesale import of experimental UI. Mocked permission regression passed
   against installed canary. Must integrate patch into owning UI source later.

Final wheel SHA256:
eb49183d6ed6450f2a787fc8de54f9b23f002d9f2a68dd20f5fbc170084dba86.
All32 staged non-pycache package files matched installed bytes. Wheel is running
release plus two corrections, not main alone.

## Results and remaining gates

Authenticated API200:20 scopes/26 Workstreams. Provider offline, execution and
inventory unavailable. Missing authentication401; unauthorized scope403; UI200.
Checkout-owned unittest suite after enrollment fix:89 passed.
Canary stopped after tests, not enabled. Account/release/cache and root-only
canary credential retained for repetition.

No live cutover, live provider/feed parity, browser review, reboot test, CI,
commit or independent application-cutover approval. Need deliberate observation
exports and service-scoped provider credentials, not broad home/transcript access.
Offline proof is not live coverage proof.
