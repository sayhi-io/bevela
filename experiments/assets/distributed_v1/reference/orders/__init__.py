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
        return events

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
