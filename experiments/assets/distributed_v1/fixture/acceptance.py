"""Public deterministic Depot contract. Identical observer copy; no model code."""
import argparse
import contextlib
import copy
import importlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile


COMPONENTS = ("catalog", "orders", "settlement", "reporting")


def require(value, detail):
    if not value:
        raise AssertionError(detail)


def rejects(call):
    try:
        call()
    except ValueError:
        return
    raise AssertionError("Expected ValueError without partial mutation")


def cls(name):
    return getattr(importlib.import_module(name), name.title())


def product(path):
    catalog = cls("catalog")(path / "catalog.json")
    return (catalog, cls("orders")(path / "orders.json", catalog),
            cls("settlement")(path / "settlement.json"), cls("reporting")(path / "reporting.json"))


def items(sku="tea", quantity=2):
    return [{"sku": sku, "quantity": quantity}]


def order(key="a", unit=250, quantity=2, cancelled=False):
    return {"schema": 2, "event_id": key + (":cancelled" if cancelled else ":placed"),
            "order_id": key, "kind": "order.cancelled" if cancelled else "order.placed",
            "revision": 2 if cancelled else 1, "total_minor": unit * quantity,
            "lines": [{"sku": "tea", "title": "Tea", "quantity": quantity,
                       "unit_minor": unit, "line_minor": unit * quantity}]}


def payment(key="a", amount=500, refunded=False):
    return {"schema": 2, "event_id": key + (":refunded" if refunded else ":captured"),
            "order_id": key, "kind": "payment.refunded" if refunded else "payment.captured",
            "revision": 2 if refunded else 1, "amount_minor": amount}


def legacy(event):
    event = copy.deepcopy(event)
    event["schema"] = 1
    if "total_minor" in event:
        event["total"] = event.pop("total_minor") / 100
        event["items"] = [{"sku": i["sku"], "title": i["title"], "quantity": i["quantity"],
                          "price": i["unit_minor"] / 100} for i in event.pop("lines")]
    else:
        event["amount"] = event.pop("amount_minor") / 100
    return event


def snapshot(path):
    return {p.name: json.loads(p.read_text()) for p in path.glob("*.json")}


def money_and_quotes(path):
    cat = cls("catalog")(path / "catalog.json")
    for sku, price, expected in (("a", "2.675", 268), ("b", "1.005", 101),
                                 ("c", "0", 0), ("d", "19.995", 2000)):
        cat.put(sku=sku, title="Unit " + sku, price=price, stock=9)
        quote = cat.quote(sku=sku, quantity=3)
        require(quote == {"sku": sku, "title": "Unit " + sku, "quantity": 3,
            "unit_minor": expected, "line_minor": 3 * expected}, "Round unit half-up before multiplying")
        require(type(quote["unit_minor"]) is int, "Minor units must be integers")
        require(cat.get(sku=sku)["price"] == expected / 100, "Preserve legacy dollars")
    cat.put_minor(sku="n", title="New", unit_minor=307, stock=2)
    require(cls("catalog")(path / "catalog.json").quote("n")["line_minor"] == 307, "Restart quote")
    value = cat.get("n")
    value["stock"] = 500
    require(cat.get("n")["stock"] == 2, "Get must detach returned state")


def reservation_atomicity(path):
    cat = cls("catalog")(path / "catalog.json")
    cat.put("tea", "Tea", 2.5, 8)
    cat.put("jam", "Jam", 4, 1)
    first = cat.reserve(reservation_id="r", items=items(quantity=1) + items(quantity=2))
    require(first["total_minor"] == 750 and len(first["lines"]) == 1, "Coalesce basket")
    require(cat.get("tea")["stock"] == 5, "Reserve once")
    cat.put("tea", "Changed title", 99, 5)
    cat = cls("catalog")(path / "catalog.json")
    require(cat.reserve("r", items(quantity=3)) == first, "Retry must retain old snapshot")
    before = snapshot(path)
    rejects(lambda: cat.reserve("r", items(quantity=4)))
    rejects(lambda: cat.reserve("bad", items(quantity=1) + items("jam", 2)))
    require(snapshot(path) == before, "Failed whole basket must not partially reserve")
    first["lines"][0]["unit_minor"] = 0
    require(cat.reserve("r", items(quantity=3))["total_minor"] == 750, "Detached reservation")
    cat.release(reservation_id="r")
    cat = cls("catalog")(path / "catalog.json")
    cat.release("r")
    require(cat.get("tea")["stock"] == 8, "Release once across restart")
    rejects(lambda: cat.reserve("r", items(quantity=3)))


def order_recovery(path):
    cat, orders, _, _ = product(path)
    cat.put("tea", "Tea", "1.005", 10)
    try:
        orders.place(key="retry", items=items(quantity=3), fail_after_reserve=True)
    except RuntimeError:
        pass
    else:
        raise AssertionError("Required post-reservation failure was not injected")
    require(cls("catalog")(path / "catalog.json").get("tea")["stock"] == 7, "Durable reservation before interruption")
    cat, orders, _, _ = product(path)
    cat.put("tea", "Changed", 99, 7)
    require(orders.place("retry", items(quantity=1) + items(quantity=2)) == "retry", "Recover stable ID")
    require(orders.get(order_id="retry")["total_minor"] == 303, "Recover old reservation snapshot")
    require(cat.get("tea")["stock"] == 7, "Retry must not reserve twice")
    require(orders.place("retry", items(quantity=3), fail_after_reserve=True) == "retry", "Completed retry ignores fault")
    before = snapshot(path)
    rejects(lambda: orders.place("retry", items(quantity=4)))
    require(snapshot(path) == before, "Conflicting order retry must be atomic")


def durable_order_outbox(path):
    cat, orders, _, _ = product(path)
    cat.put("tea", "Tea", 2.5, 6)
    orders.place("a", items())
    events = orders.events()
    require(events == [order()], "New order wire contract")
    events[0]["lines"][0]["quantity"] = 99
    require(orders.events() == [order()], "Events must detach state")
    orders.ack(event_id="a:placed")
    cat, orders, _, _ = product(path)
    require(orders.events() == [], "Ack persists")
    orders.cancel(order_id="a")
    orders.cancel("a")
    cat, orders, _, _ = product(path)
    require(cat.get("tea")["stock"] == 6, "Cancellation releases once")
    require(orders.events() == [order(cancelled=True)], "New cancellation wire preserves snapshot")
    require(orders.place("a", items()) == "a" and cat.get("tea")["stock"] == 6, "Cancelled retry cannot reserve")
    require(orders.legacy("a") == {"order_id": "a", "total": 5.0, "status": "cancelled"}, "Legacy order adapter")
    rejects(lambda: orders.ack("absent"))


def migration_and_restart(path):
    old = legacy(order("old"))
    zero = legacy(order("zero", unit=0, quantity=1))
    for name, state in {
        "catalog": {"version": 1, "products": {"tea": {"title": "Tea", "price": 2.5, "stock": 3}},
            "reservations": {"old": {"reservation_id": "old", "items": old["items"],
                                    "total": 5.0, "released": False}}},
        "orders": {"version": 1, "orders": {"old": {"order_id": "old", "items": old["items"],
            "total": 5.0, "status": "placed"}}, "acked": ["old:placed"]},
        "settlement": {"version": 1, "payments": {
            "old": {"order_id": "old", "amount": 5.0, "status": "captured"},
            "zero": {"order_id": "zero", "amount": 0, "status": "captured"}},
            "seen": {"old:placed": old}, "acked": ["old:captured"]},
        "reporting": {"version": 1, "receipts": {
            "old": {"order_id": "old", "items": old["items"], "total": 5.0, "paid": 5.0, "status": "paid"},
            "zero": {"order_id": "zero", "items": zero["items"], "total": 0, "paid": 0, "status": "paid"},
            "returned": {"order_id": "returned", "items": old["items"], "total": 5.0, "paid": 0, "status": "refunded"}},
            "seen": {"old:placed": old, "old:captured": legacy(payment("old"))}},
    }.items():
        (path / (name + ".json")).write_text(json.dumps(state))
    cat, orders, settle, report = product(path)
    require(all(s["version"] == 2 for s in snapshot(path).values()), "All stores migrate")
    require(cat.get("tea")["stock"] == 3 and orders.get("old")["total_minor"] == 500, "Migration does not reserve again")
    require(orders.events() == [] and settle.drain() == 0, "Retain ack/capture on migration")
    require(settle.handle(old) is False and settle.handle(order("old")) is False,
            "Migrate settlement's existing deduplication history")
    require(report.handle(old) is False and report.handle(payment("old")) is False,
            "Migrate reporting's existing deduplication history")
    require([e["event_id"] for e in settle.events()] == ["zero:captured"], "Retain payment ack")
    require(report.receipt("zero")["status"] == "paid" and report.receipt("zero")["paid_minor"] == 0,
            "Zero-value legacy paid receipt stays paid")
    report.handle(payment("returned"))
    require(report.receipt("returned")["status"] == "refunded", "Migration preserves refund precedence")
    orders.cancel("old")
    require(cat.get("tea")["stock"] == 5, "Migrated reservation releases original hold")
    settle.handle(orders.events()[0])
    report.handle(payment("old", refunded=True))
    cat, orders, settle, report = product(path)
    require(report.revenue() == 0 and settle.balance() == 0, "Restarts preserve refunds")
    require(report.legacy_receipt("old") == "old: $5.00 (refunded)", "Migrated legacy adapter")


def deferred_settlement(path):
    settle = cls("settlement")(path / "settlement.json")
    event = order(unit=317, quantity=3)
    require(settle.handle(event=event) is True, "New event accepted")
    require(settle.events() == [] and settle.balance() == 0, "Capture is delayed until drain")
    settle = cls("settlement")(path / "settlement.json")
    require(settle.drain() == 1, "Exactly one capture")
    require(settle.handle(event) is False and settle.drain() == 0, "No duplicate charge")
    require(settle.events() == [payment(amount=951)] and settle.balance() == 951, "Integer settlement amount")
    settle.ack(event_id="a:captured")
    settle.ack("a:captured")
    settle = cls("settlement")(path / "settlement.json")
    require(settle.events() == [] and settle.balance() == 951, "Ack and balance survive restart")
    bad = copy.deepcopy(event)
    bad["total_minor"] += 1
    before = snapshot(path)
    rejects(lambda: settle.handle(bad))
    require(snapshot(path) == before, "Conflicting duplicate cannot alter ledger")


def cancellation_reordering(path):
    settle = cls("settlement")(path / "settlement.json")
    settle.handle(order("cancel-first", cancelled=True))
    settle = cls("settlement")(path / "settlement.json")
    settle.handle(order("cancel-first"))
    require(settle.drain() == 0 and settle.events() == [], "Cancel-before-place cannot charge")
    settle.handle(order("paid-first"))
    require(settle.drain() == 1, "Normal capture")
    settle.handle(order("paid-first", cancelled=True))
    settle = cls("settlement")(path / "settlement.json")
    require(settle.handle(order("paid-first", cancelled=True)) is False, "Dedup survives restart")
    settle.handle(order("paid-first"))
    require(settle.drain() == 0 and settle.balance() == 0, "Cancelled order cannot recapture")
    require(settle.events() == [payment("paid-first"), payment("paid-first", refunded=True)],
            "Retain unacked capture and refund exactly once")


def reporting_late_join(path):
    report = cls("reporting")(path / "reporting.json")
    report.handle(payment())
    before = snapshot(path)
    rejects(lambda: report.handle(payment(amount=501)))
    require(snapshot(path) == before, "Conflicting duplicate payment must not alter reporting")
    require(report.receipt("a") is None and report.revenue() == 0, "Payment alone awaits snapshot")
    report = cls("reporting")(path / "reporting.json")
    report.handle(order())
    require(report.receipt(order_id="a")["paid_minor"] == 500 and report.revenue() == 500, "Join after restart")
    report.handle(order(cancelled=True))
    require(report.receipt("a")["status"] == "cancelled" and report.revenue() == 500, "Cancellation awaits refund")
    report.handle(payment(refunded=True))
    report.handle(payment())
    report.handle(order())
    require(report.receipt("a")["status"] == "refunded" and report.revenue() == 0, "Never regress refund")
    report.handle(payment("b", refunded=True))
    report.handle(order("b", cancelled=True))
    report.handle(order("b"))
    report.handle(payment("b"))
    report = cls("reporting")(path / "reporting.json")
    require(report.receipt("b")["status"] == "refunded" and report.revenue() == 0, "Fully reversed streams")
    detached = report.receipt("b")
    detached["lines"][0]["unit_minor"] = 0
    require(report.receipt("b")["lines"][0]["unit_minor"] == 250, "Detached receipt")


def mixed_wire_versions(path):
    settle = cls("settlement")(path / "settlement.json")
    report = cls("reporting")(path / "reporting.json")
    for target in (settle, report):
        require(target.handle(legacy(order())) is True, "Legacy placement accepted")
        require(target.handle(order()) is False, "Equivalent normalized v2 duplicate")
    settle.drain()
    report.handle(legacy(payment()))
    require(report.legacy_receipt("a") == "a: $5.00 (paid)", "Old payment joins normalized order")
    settle.handle(order(cancelled=True))
    report.handle(legacy(order(cancelled=True)))
    report.handle(payment(refunded=True))
    require(report.revenue() == 0 and settle.balance() == 0, "Mixed-version cancellation/refund")
    # A new v2 event must work, not merely be ignored as an already-seen legacy ID.
    settle.handle(order("fresh", unit=101, quantity=3))
    report.handle(order("fresh", unit=101, quantity=3))
    settle.drain()
    report.handle(payment("fresh", amount=303))
    require(report.revenue() == 303 and settle.balance() == 303, "Fresh v2 bodies after legacy traffic")


def validation_is_atomic(path):
    cat, orders, settle, report = product(path)
    cat.put("tea", "Tea", 2.5, 8)
    for value in (True, -1, "NaN", "Infinity", float("inf")):
        before = snapshot(path)
        rejects(lambda: cat.put("bad", "Bad", value, 1))
        require(snapshot(path) == before, "Invalid dollars changed catalog")
    for quantity in (0, -1, True, 1.5):
        before = snapshot(path)
        rejects(lambda: cat.reserve("bad", items(quantity=quantity)))
        require(snapshot(path) == before, "Invalid quantity changed catalog")
    rejects(lambda: cat.put_minor("bad", "Bad", True, 1))
    rejects(lambda: cat.release("unknown"))
    rejects(lambda: orders.get("unknown"))
    rejects(lambda: orders.cancel("unknown"))
    for target in (settle, report):
        for event in (dict(order(), schema=3), dict(order(), revision=7),
                      dict(order(), total_minor=True), dict(order(), kind="unknown")):
            before = snapshot(path)
            rejects(lambda: target.handle(event))
            require(snapshot(path) == before, "Invalid event was partially consumed")
        target.handle(order())
        altered = order(cancelled=True)
        altered["total_minor"] = 501
        before = snapshot(path)
        rejects(lambda: target.handle(altered))
        require(snapshot(path) == before, "Conflicting amount changed state")
        require(target.handle(order(cancelled=True)) is True, "Rejected event ID must remain reusable")
    for name in COMPONENTS:
        corrupt = path / ("invalid-" + name + ".json")
        corrupt.write_text('{"version":99}')
        try:
            cls(name)(corrupt, cat) if name == "orders" else cls(name)(corrupt)
        except (ValueError, KeyError):
            pass
        else:
            raise AssertionError("Unsupported persisted version reset silently")
        require(corrupt.read_text() == '{"version":99}', "Invalid state was overwritten")


def integrated_replay(path):
    cat, orders, settle, report = product(path)
    for sku, price in (("tea", "1.005"), ("jam", "2.675"), ("free", "0")):
        cat.put(sku, sku.title(), price, 20)
    for key, basket in (("a", items("tea", 3)), ("b", items("jam", 2)), ("c", items("jam", 1)), ("zero", items("free", 1))):
        orders.place(key, basket)
    originals = orders.events()
    orders.cancel("b")
    all_order_events = orders.events()
    for e in reversed(all_order_events):
        settle.handle(e)
        settle.handle(e)
    settle = cls("settlement")(path / "settlement.json")
    require(settle.drain() == 3, "Capture only uncancelled orders, including zero value")
    orders.cancel("c")
    for e in reversed(orders.events()):
        settle.handle(e)
    for e in reversed(settle.events()):
        report.handle(e)
        report.handle(e)
    report = cls("reporting")(path / "reporting.json")
    require(report.revenue() == 0, "Payment-only rows do not produce revenue")
    for e in reversed(orders.events() + originals):
        report.handle(e)
    require(report.revenue() == 303 and settle.balance() == 303, "Only surviving order contributes")
    require({k: report.receipt(k)["status"] for k in ("a", "b", "c", "zero")} ==
            {"a": "paid", "b": "cancelled", "c": "refunded", "zero": "paid"}, "Final statuses")
    require(report.legacy_receipt("zero") == "zero: $0.00 (paid)", "Zero-price capture remains paid")
    require(cat.get("tea")["stock"] == 17 and cat.get("jam")["stock"] == 20, "Inventory matches final orders")
    for e in orders.events():
        orders.ack(e["event_id"])
    for e in settle.events():
        settle.ack(e["event_id"])
    cat, orders, settle, report = product(path)
    require(orders.events() == [] and settle.events() == [], "All outbox acknowledgments persist")
    for e in originals:
        settle.handle(e)
        report.handle(e)
    require(settle.drain() == 0 and report.revenue() == 303, "Late replay cannot revive cancelled revenue")


def legacy_workflow(path):
    cat, orders, settle, report = product(path)
    cat.put(sku="tea", title="Tea", price=2.5, stock=6)
    require(orders.place(key="old-client", items=items()) == "old-client", "Stable order ID")
    for e in orders.events():
        report.handle(event=e)
        settle.handle(event=e)
    settle.drain()
    for e in settle.events():
        report.handle(event=e)
    require(orders.legacy(order_id="old-client")["total"] == 5.0, "Old order client")
    require(report.legacy_receipt(order_id="old-client") == "old-client: $5.00 (paid)", "Old receipt client")


GROUPS = {f.__name__: f for f in (
    money_and_quotes, reservation_atomicity, order_recovery, durable_order_outbox,
    migration_and_restart, deferred_settlement, cancellation_reordering,
    reporting_late_join, mixed_wire_versions, validation_is_atomic,
    integrated_replay, legacy_workflow)}


def evaluate(root):
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("SOURCE_ROOT must be a directory")
    sys.path.insert(0, str(root))
    groups = {}
    for name, function in GROUPS.items():
        # Each group owns new state; one product assertion never skips later groups.
        with tempfile.TemporaryDirectory(prefix="depot-contract-") as temp:
            try:
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    function(Path(temp))
                groups[name] = {"passed": True}
            except Exception as exc:
                groups[name] = {"passed": False, "detail": type(exc).__name__ + ": " + str(exc)}
    component_checks = {}
    for component in COMPONENTS:
        code = '''import contextlib, io, json, sys, unittest
sys.path.insert(0, sys.argv[1])
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    suite = unittest.defaultTestLoader.discover(sys.argv[2], pattern='test*.py', top_level_dir=sys.argv[1])
    result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
print(json.dumps({'passed': result.wasSuccessful() and result.testsRun > 0,
                  'tests_run': result.testsRun, 'failures': len(result.failures),
                  'errors': len(result.errors)}))
'''
        try:
            result = subprocess.run([sys.executable, "-B", "-I", "-c", code, str(root), str(root / component)],
                                    cwd=root, text=True, capture_output=True, timeout=5)
        except subprocess.TimeoutExpired:
            component_checks[component] = {"passed": False, "detail": "Local tests exceeded 5 seconds"}
            continue
        try:
            local = json.loads(result.stdout)
            require(isinstance(local.get("passed"), bool), "Malformed local-test result")
            local["passed"] = local["passed"] and result.returncode == 0
            component_checks[component] = local
        except (ValueError, AssertionError, AttributeError):
            component_checks[component] = {"passed": False, "detail": "Local test process failed to report results"}
    failed = [name for name, result in groups.items() if not result["passed"]]
    return {"fixture": "distributed/v1", "accepted": not failed and all(
                c["passed"] for c in component_checks.values()),
            "groups": groups, "component_checks": component_checks, "failed_contracts": failed}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_root", nargs="?", default=str(Path(__file__).resolve().parent))
    args = parser.parse_args()
    try:
        result = evaluate(args.source_root)
    except Exception as exc:
        print(json.dumps({"infrastructure_error": type(exc).__name__ + ": " + str(exc)}))
        sys.exit(2)
    print(json.dumps(result, sort_keys=True))
