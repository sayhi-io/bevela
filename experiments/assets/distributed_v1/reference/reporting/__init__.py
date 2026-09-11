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

def _normalize(event, allowed):
    try:
        schema = event["schema"]
        kind = event["kind"]
        revisions = {"order.placed": 1, "order.cancelled": 2,
                     "payment.captured": 1, "payment.refunded": 2}
        if type(schema) is not int or schema not in (1, 2) or kind not in allowed:
            raise ValueError("Unsupported event")
        if type(event["revision"]) is not int or event["revision"] != revisions[kind]:
            raise ValueError("Invalid revision")
        out = {"schema": 2, "event_id": _identity(event["event_id"]), "kind": kind,
               "order_id": _identity(event["order_id"]), "revision": event["revision"]}
        if kind.startswith("payment."):
            out["amount_minor"] = _minor(event["amount"]) if schema == 1 else _integer(event["amount_minor"])
        else:
            out["total_minor"] = _minor(event["total"]) if schema == 1 else _integer(event["total_minor"])
            items = event["items"] if schema == 1 else event["lines"]
            if not isinstance(items, list) or not items:
                raise ValueError("Missing lines")
            lines = []
            for item in items:
                quantity = _integer(item["quantity"], 1)
                unit = _minor(item["price"]) if schema == 1 else _integer(item["unit_minor"])
                line = {"sku": _identity(item["sku"]), "title": _identity(item["title"]),
                        "quantity": quantity, "unit_minor": unit, "line_minor": quantity * unit}
                if schema == 2 and _integer(item["line_minor"]) != line["line_minor"]:
                    raise ValueError("Invalid line total")
                lines.append(line)
            out["lines"] = sorted(lines, key=lambda i: i["sku"])
        return out
    except (KeyError, TypeError):
        raise ValueError("Malformed event") from None


def _duplicate(state, event):
    prior = state["seen"].get(event["event_id"])
    if prior is None:
        return False
    if prior != event:
        raise ValueError("Conflicting event ID")
    return True

class Reporting:
    def __init__(self, path):
        self.path = Path(path)
        self.state = _load(self.path, {"version": 2, "orders": {}, "seen": {}})
        if self.state["version"] == 1:
            orders = {}
            for key, old in self.state.pop("receipts").items():
                normalized = _normalize({"schema": 1, "event_id": key + ":placed",
                    "kind": "order.placed", "order_id": key, "revision": 1,
                    "items": old["items"], "total": old["total"]}, ("order.placed",))
                refunded = old["status"] == "refunded"
                paid = _minor(old["paid"])
                captured = old["status"] == "paid" or paid > 0
                orders[key] = {"lines": normalized["lines"], "total_minor": normalized["total_minor"],
                    "order_revision": 2 if old["status"] in ("cancelled", "refunded") else 1,
                    "payment_revision": 2 if refunded else (1 if captured else 0),
                    "amount_minor": normalized["total_minor"] if refunded else (paid if captured else None)}
            self.state["seen"] = {key: _normalize(event, ("order.placed", "order.cancelled",
                "payment.captured", "payment.refunded")) for key, event in self.state["seen"].items()}
            self.state.update(version=2, orders=orders)
        _save(self.path, self.state)

    def handle(self, event):
        event = _normalize(event, ("order.placed", "order.cancelled",
                                  "payment.captured", "payment.refunded"))
        if _duplicate(self.state, event):
            return False
        state = copy.deepcopy(self.state)
        record = state["orders"].setdefault(event["order_id"], {"lines": None,
            "total_minor": None, "order_revision": 0, "payment_revision": 0, "amount_minor": None})
        amount = event.get("total_minor", event.get("amount_minor"))
        if any(known is not None and known != amount
               for known in (record["total_minor"], record["amount_minor"])):
            raise ValueError("Conflicting receipt amount")
        if event["kind"].startswith("order."):
            if record["lines"] is not None and record["lines"] != event["lines"]:
                raise ValueError("Conflicting receipt snapshot")
            record["lines"], record["total_minor"] = event["lines"], amount
            record["order_revision"] = max(record["order_revision"], event["revision"])
        else:
            record["amount_minor"] = amount
            record["payment_revision"] = max(record["payment_revision"], event["revision"])
        state["seen"][event["event_id"]] = event
        _save(self.path, state)
        self.state = state
        return True

    def receipt(self, order_id):
        _identity(order_id)
        record = self.state["orders"].get(order_id)
        if not record or record["lines"] is None:
            return None
        paid = record["amount_minor"] if record["payment_revision"] == 1 else 0
        status = ("refunded" if record["payment_revision"] == 2 else
                  "cancelled" if record["order_revision"] == 2 else
                  "paid" if record["payment_revision"] == 1 else "placed")
        return copy.deepcopy({"schema": 2, "order_id": order_id, "lines": record["lines"],
            "total_minor": record["total_minor"], "paid_minor": paid, "status": status})

    def revenue(self):
        return sum(self.receipt(key)["paid_minor"] for key, r in self.state["orders"].items()
                   if r["lines"] is not None)

    def legacy_receipt(self, order_id):
        receipt = self.receipt(order_id)
        if receipt is None:
            return None
        total = receipt["total_minor"]
        return f"{order_id}: $" + f"{total // 100}.{total % 100:02d} ({receipt['status']})"
