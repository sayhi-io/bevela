import copy
import json
import os
from pathlib import Path
import tempfile
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def _minor(value):
    if isinstance(value, bool):
        raise ValueError("Invalid dollars")
    try:
        number = Decimal(str(value))
        if not number.is_finite() or number < 0:
            raise ValueError("Invalid dollars")
        return int((number * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except (InvalidOperation, TypeError):
        raise ValueError("Invalid dollars") from None


def _integer(value, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError("Invalid integer")
    return value


def _identity(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Invalid identifier")
    return value


def _save(path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix="." + path.name)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(state, stream, sort_keys=True)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def _load(path, empty):
    state = json.loads(path.read_text()) if path.exists() else empty
    if state.get("version") not in (1, 2):
        raise ValueError("Unsupported stored version")
    return state

def _basket(items):
    if not isinstance(items, list) or not items:
        raise ValueError("Empty or invalid basket")
    quantities = {}
    for item in items:
        try:
            sku = _identity(item["sku"])
            quantity = _integer(item["quantity"], 1)
        except (KeyError, TypeError):
            raise ValueError("Invalid basket item") from None
        quantities[sku] = quantities.get(sku, 0) + quantity
    return [{"sku": sku, "quantity": quantities[sku]} for sku in sorted(quantities)]


def _old_lines(items):
    return sorted([{"sku": i["sku"], "title": i["title"], "quantity": i["quantity"],
                    "unit_minor": _minor(i["price"]),
                    "line_minor": _minor(i["price"]) * i["quantity"]}
                   for i in items], key=lambda i: i["sku"])

class Orders:
    def __init__(self, path, catalog):
        self.path, self.catalog = Path(path), catalog
        self.state = _load(self.path, {"version": 2, "orders": {}, "acked": []})
        if self.state["version"] == 1:
            self.state["orders"] = {key: {"basket": _basket(old["items"]),
                "record": {"schema": 2, "order_id": key, "lines": _old_lines(old["items"]),
                           "total_minor": _minor(old["total"]), "status": old["status"]}}
                for key, old in self.state["orders"].items()}
            self.state["version"] = 2
        _save(self.path, self.state)

    def place(self, key, items, fail_after_reserve=False):
        _identity(key)
        basket = _basket(items)
        prior = self.state["orders"].get(key)
        if prior:
            if prior["basket"] != basket:
                raise ValueError("Conflicting order retry")
            return key
        reservation = self.catalog.reserve(reservation_id=key, items=basket)
        if fail_after_reserve:
            raise RuntimeError("Injected interruption after durable reservation")
        state = copy.deepcopy(self.state)
        state["orders"][key] = {"basket": basket, "record": {"schema": 2, "order_id": key,
            "lines": reservation["lines"], "total_minor": reservation["total_minor"], "status": "placed"}}
        _save(self.path, state)
        self.state = state
        return key

    def get(self, order_id):
        _identity(order_id)
        try:
            return copy.deepcopy(self.state["orders"][order_id]["record"])
        except (KeyError, TypeError):
            raise ValueError("Unknown order") from None

    def legacy(self, order_id):
        record = self.get(order_id)
        return {"order_id": order_id, "total": record["total_minor"] / 100, "status": record["status"]}

    def cancel(self, order_id):
        record = self.get(order_id)
        if record["status"] == "cancelled":
            return False
        self.catalog.release(reservation_id=order_id)
        state = copy.deepcopy(self.state)
        state["orders"][order_id]["record"]["status"] = "cancelled"
        _save(self.path, state)
        self.state = state
        return True

    def _events(self):
        events = []
        for key in sorted(self.state["orders"]):
            record = self.get(key)
            kinds = ["placed", "cancelled"] if record["status"] == "cancelled" else ["placed"]
            for revision, kind in enumerate(kinds, 1):
                events.append({"schema": 2, "event_id": key + ":" + kind, "kind": "order." + kind,
                    "order_id": key, "revision": revision, "lines": record["lines"],
                    "total_minor": record["total_minor"]})
        for key, order in sorted(self.state["orders"].items()):
            for return_id, returned in sorted(order.get("returns", {}).items()):
                # New payload belongs to Orders; legacy event bodies stay unchanged.
                events.append({"schema": 3, "event_id": json.dumps([key, "return", return_id]),
                    "kind": "order.returned", "order_id": key, "revision": 3,
                    "return_note": {"ticket": return_id, "units": returned["items"],
                                    "credit": returned["refund_minor"],
                                    "original": order["record"]["total_minor"]}})
        return copy.deepcopy(sorted(events, key=lambda e: (e["order_id"], e["revision"], e["event_id"])))

    def events(self):
        return [e for e in self._events() if e["event_id"] not in self.state["acked"]]

    def ack(self, event_id):
        _identity(event_id)
        if event_id not in {e["event_id"] for e in self._events()}:
            raise ValueError("Unknown event")
        if event_id not in self.state["acked"]:
            state = copy.deepcopy(self.state)
            state["acked"].append(event_id)
            _save(self.path, state)
            self.state = state

    def returns(self, order_id):
        self.get(order_id)
        return [copy.deepcopy(value) for _, value in
                sorted(self.state["orders"][order_id].get("returns", {}).items())]

    def return_items(self, order_id, return_id, items, fail_after_restore=False):
        record = self.get(order_id)
        _identity(return_id)
        basket = _basket(items)
        previous = self.state["orders"][order_id].get("returns", {}).get(return_id)
        if previous is not None:
            if previous["items"] != basket:
                raise ValueError("Conflicting return retry")
            return return_id
        if record["status"] == "cancelled":
            raise ValueError("Cancelled order")
        # Consume the Catalog-owned JSON receipt, not its internal state/parser.
        proof = json.loads(json.dumps(self.catalog.restore(
            reservation_id=order_id, return_id=return_id, items=basket)))
        if (proof["hold"] != order_id or proof["ticket"] != return_id or
                proof["items"] != basket or proof["original"] != record["total_minor"]):
            raise ValueError("Catalog restore receipt does not match order")
        refund = _integer(proof["credit"])
        if refund > record["total_minor"]:
            raise ValueError("Invalid restore credit")
        if fail_after_restore:
            raise RuntimeError("Injected interruption after durable restoration")
        state = copy.deepcopy(self.state)
        state["orders"][order_id].setdefault("returns", {})[return_id] = {
            "return_id": return_id, "items": basket, "refund_minor": refund}
        _save(self.path, state)
        self.state = state
        return return_id
