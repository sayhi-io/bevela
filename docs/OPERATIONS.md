# Independent operation and recovery (provisional)

Smallest topology: one Project Intent process serves the static UI and normalized
API; a separately operated PM provider owns durable PM persistence. Project Intent
has its own state/config/access credentials. It is not started by, proxied through,
or authenticated by SparkOps or the main SayHi application. Independent service
restart/release policy is required; shared physical hardware remains a common failure
domain. No HA is claimed.

The dogfood process binds only 127.0.0.1:8290. It uses independent high-entropy Basic
tokens over loopback, exact Host checks, no CORS, restrictive CSP and no-store
responses. Static principal-to-scope grants are a local v0 access boundary, not a
replacement for production identity lifecycle. Provider tokens never reach browsers.
Current provisional provider agent keys may have broader native rights; GET-only
adapter behavior does not turn them into provider-enforced read-only credentials.
Narrow provider grants are a production admission requirement.

Private configuration example (placeholders, not an executable deployment):

```json
{
  "principals": {"operator": {"token_sha256": "SHA256_OF_RANDOM_32_BYTE_TOKEN", "scopes": ["sayhi/project-intent"]}},
  "scopes": [{
    "id": "sayhi/project-intent", "label": "Project Intent",
    "provider": {"kind": "itsaplan", "url": "http://127.0.0.1:8280", "project": "SAYINT", "token_file": "/private/project-intent/provider-token"},
    "cache": "/private/project-intent/snapshots/SAYINT.json",
    "presence_sources": ["/private/project-intent/presence/platform"]
  }]
}
```

Keep the state directory mode 0700 and credentials/config mode 0600. Snapshots are
atomic fsynced replacements; caches survive process restarts. A malformed refresh
does not replace the prior valid scope cache. Existing scope binding is checked on
both startup and refresh. No primary product credential inheritance is needed.

Recovery order:

1. Restart this independent process with its own config and intact cache; do not
   start SparkOps or a product merely to obtain recovery context.
2. If the provider is unavailable, show the cached capture time and unavailable
   provider label. Continue previously authorized bounded offline work only.
3. Restore PM-provider persistence through its owning backup procedure; cache is
   not a PM backup and cannot reconstruct all comments/activity or identities.
4. Restore independent access configuration from protected operator recovery material;
   rotate lost credentials through their respective authority, not product tokens.
5. Reconnect optional execution feeds. Their absence must not hide durable intent.

The current It's a Plan installation is still the evaluation installation. Its
durable backup/restore, unattended operation, and credentials lifecycle have NOT
been production-qualified. This tranche tests cache restart and isolated failure
semantics without stopping any real SparkOps, provider or SayHi service. A real
provider disaster recovery drill and managed independent hosting remain admission
gates. Do not advertise this loopback development process as production availability.

The repository exports are scoped fallback material, not service secrets. Review
their content before committing to a repository with different readers. Do not copy
the whole operator cache into a product repository.

Optional browser dogfood uses Playwright only as a test dependency, not a service
dependency. Against the enrolled real local scopes and private access files:

```bash
.venv/bin/python -m pip install playwright==1.62.0
PLAYWRIGHT_BROWSERS_PATH=/private/project-intent/browser-test .venv/bin/python -m playwright install chromium
PLAYWRIGHT_BROWSERS_PATH=/private/project-intent/browser-test .venv/bin/python tests/browser_observatory.py \
  --state-dir /private/project-intent --output /private/evidence/observatory
```

This specific dogfood checks the enrolled PI/SparkOps work, product-only access,
mobile layout, detail/environment semantics, and an isolated cached-state HTTP
instance with execution feeds absent and provider labeled unavailable. It does
not stop or alter any actual provider/product. Screenshots contain private project
context and remain outside Git. The focused unit suite runs offline without browser
dependencies, credentials, a provider, or a SparkOps installation.
