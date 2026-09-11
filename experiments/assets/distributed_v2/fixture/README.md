# Depot: a small wholesale order system

Candidate2 adds durable partial returns: read the complete
[OBJECTIVE.md](OBJECTIVE.md). New payload layouts are producer-owned and documented
in each component's CONTRACT.md, equally visible to every worker.

This is a working legacy product, not a blank implementation. Four packages own
separate JSON stores: `catalog`, `orders`, `settlement`, and `reporting`. Orders
reserve catalog inventory and expose events; settlement consumes order events and
exposes payment events; reporting consumes both. Delivery is an ordinary caller
responsibility; there is no broker, coordinator, service, or network dependency.

The complete requested migration is in [OBJECTIVE.md](OBJECTIVE.md). All four role
tasks are visible in `tasks/`. A component assignment bounds source editing, not
access to the other components' requirements or public APIs. No worker allocation,
repair sequence, messages, waiting period, or implementation strategy is prescribed.

Run the existing focused checks with `python3 -B -m unittest discover -v`.
Run the new product contract with `python3 -B acceptance.py`. Its assertions are
public; the observer uses an unchanged copy of exactly this checker. Existing
focused tests pass on the legacy product but do not prove the migration is complete.
Do not change OBJECTIVE.md, role tasks, or acceptance.py to change acceptance.

Only the Python standard library is needed. All examples and test data are synthetic.
No model calls, clocks, sleeps, network, payment service, or background worker is
part of the product. Runtime calls are sequential; delayed and reordered delivery
is supplied explicitly by callers. Concurrent development is not a requirement for
simultaneous multi-process database transactions.
