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


def _return_event(event):
    """Consumer-owned parser for Orders' documented return_note payload."""
    try:
        if (event["schema"] != 3 or type(event["schema"]) is not int or
                event["kind"] != "order.returned" or type(event["revision"]) is not int or
                event["revision"] != 3):
            raise ValueError("Unsupported return event")
        note = event["return_note"]
        units = note["units"]
        if not isinstance(units, list) or not units:
            raise ValueError("Missing returned units")
        counts = {}
        for item in units:
            sku = _identity(item["sku"])
            if sku in counts:
                raise ValueError("Noncanonical returned units")
            counts[sku] = _integer(item["quantity"], 1)
        credit, total = _integer(note["credit"]), _integer(note["original"])
        if credit > total:
            raise ValueError("Return exceeds total")
        return {"schema": 3, "event_id": _identity(event["event_id"]),
                "order_id": _identity(event["order_id"]), "kind": "order.returned",
                "revision": 3, "return_id": _identity(note["ticket"]),
                "items": [{"sku": k, "quantity": counts[k]} for k in sorted(counts)],
                "refund_minor": credit, "total_minor": total}
    except (KeyError, TypeError):
        raise ValueError("Malformed return event") from None

def _refund_event(event):
    """Consumer-owned parser for Settlement's cumulative refund_position."""
    try:
        if (event["schema"] != 3 or type(event["schema"]) is not int or
                event["kind"] != "payment.return_refund" or type(event["revision"]) is not int or
                event["revision"] != 3):
            raise ValueError("Unsupported refund event")
        total, refunded = map(_integer, event["refund_position"])
        if refunded > total:
            raise ValueError("Refund exceeds total")
        return {"schema": 3, "event_id": _identity(event["event_id"]),
                "order_id": _identity(event["order_id"]), "kind": "payment.return_refund",
                "revision": 3, "total_minor": total, "refunded_minor": refunded}
    except (KeyError, TypeError):
        raise ValueError("Malformed refund event") from None

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
        if isinstance(event, dict) and event.get("schema") == 3:
            return self._handle_return_wire(event)
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
        partial = record.get("partial_refund", 0)
        paid = max(0, paid - partial)
        status = ("refunded" if record["payment_revision"] == 2 else
                  "cancelled" if record["order_revision"] == 2 else
                  "paid" if record["payment_revision"] == 1 else "placed")
        if record.get("return_payment_known") and record["payment_revision"] != 2:
            if partial == record["total_minor"]:
                status = "refunded"
            elif record["order_revision"] != 2 and partial > 0:
                status = "partially_refunded"
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

    def _handle_return_wire(self, raw):
        event = (_return_event(raw) if raw.get("kind") == "order.returned"
                 else _refund_event(raw))
        if _duplicate(self.state, event):
            return False
        state = copy.deepcopy(self.state)
        record = state["orders"].setdefault(event["order_id"], {"lines": None,
            "total_minor": None, "order_revision": 0, "payment_revision": 0, "amount_minor": None})
        total = event["total_minor"]
        if any(x is not None and x != total for x in (record["total_minor"], record["amount_minor"])):
            raise ValueError("Conflicting return amount")
        # An amount alone never establishes the original order snapshot.
        record["amount_minor"] = total
        if event["kind"] == "order.returned":
            returns = record.setdefault("returns", {})
            if event["return_id"] in returns:
                raise ValueError("Return ID reused")
            if sum(r["refund_minor"] for r in returns.values()) + event["refund_minor"] > total:
                raise ValueError("Cumulative refund exceeds order")
            returns[event["return_id"]] = event
        else:
            record["partial_refund"] = max(record.get("partial_refund", 0), event["refunded_minor"])
            record["return_payment_known"] = True
            record["payment_revision"] = max(1, record["payment_revision"])
        state["seen"][event["event_id"]] = event
        _save(self.path, state)
        self.state = state
        return True

    def return_summary(self, order_id):
        if self.receipt(order_id) is None:
            return None
        record = self.state["orders"][order_id]
        counts = {}
        for returned in record.get("returns", {}).values():
            for item in returned["items"]:
                counts[item["sku"]] = counts.get(item["sku"], 0) + item["quantity"]
        refunded = (record["total_minor"] if record["payment_revision"] == 2 else
                    record.get("partial_refund", 0))
        return {"returned_items": [{"sku": sku, "quantity": counts[sku]} for sku in sorted(counts)],
                "refund_due_minor": sum(r["refund_minor"] for r in record.get("returns", {}).values()),
                "refunded_minor": refunded}
