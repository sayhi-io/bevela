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

class Settlement:
    def __init__(self, path):
        self.path = Path(path)
        self.state = _load(self.path, {"version": 2, "orders": {}, "seen": {}, "acked": []})
        if self.state["version"] == 1:
            self.state["orders"] = {key: {"total_minor": _minor(old["amount"]), "lines": None,
                "placed": True, "cancelled": old["status"] == "refunded",
                "captured": True, "refunded": old["status"] == "refunded"}
                for key, old in self.state.pop("payments").items()}
            self.state["seen"] = {key: _normalize(event, ("order.placed", "order.cancelled"))
                                  for key, event in self.state["seen"].items()}
            for event in self.state["seen"].values():
                record = self.state["orders"].get(event["order_id"])
                if record is not None:
                    record["lines"] = event["lines"]
            self.state["version"] = 2
        _save(self.path, self.state)

    def handle(self, event):
        if isinstance(event, dict) and event.get("schema") == 3:
            return self._handle_return(event)
        event = _normalize(event, ("order.placed", "order.cancelled"))
        if _duplicate(self.state, event):
            return False
        state = copy.deepcopy(self.state)
        key = event["order_id"]
        record = state["orders"].setdefault(key, {"total_minor": event["total_minor"],
            "lines": None, "placed": False, "cancelled": False, "captured": False, "refunded": False})
        if record["total_minor"] != event["total_minor"]:
            raise ValueError("Conflicting order amount")
        if record["lines"] is not None and record["lines"] != event["lines"]:
            raise ValueError("Conflicting order snapshot")
        record["lines"] = event["lines"]
        if event["kind"] == "order.cancelled":
            record["cancelled"] = True
            if record["captured"]:
                record["refunded"] = True
        else:
            record["placed"] = True
        state["seen"][event["event_id"]] = event
        _save(self.path, state)
        self.state = state
        return True

    def drain(self):
        state = copy.deepcopy(self.state)
        count = 0
        for key, record in state["orders"].items():
            if record["placed"] and not record["cancelled"] and not record["captured"]:
                record["captured"] = True
                count += 1
                self._refund_pending(state, key)
        _save(self.path, state)
        self.state = state
        return count

    def _events(self):
        events = []
        for key, record in sorted(self.state["orders"].items()):
            for revision, kind in ((1, "captured"), (2, "refunded")):
                if record[kind]:
                    events.append({"schema": 2, "event_id": key + ":" + kind,
                        "kind": "payment." + kind, "order_id": key, "revision": revision,
                        "amount_minor": record["total_minor"]})
        events.extend(copy.deepcopy(self.state.get("adjustments", [])))
        return sorted(events, key=lambda e: (e["order_id"], e["revision"], e["event_id"]))

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

    def balance(self):
        return sum((r["total_minor"] - r.get("partial_refund", 0)) if r["captured"] and not r["refunded"] else 0
                   for r in self.state["orders"].values())

    def _handle_return(self, event):
        event = _return_event(event)
        if _duplicate(self.state, event):
            return False
        state = copy.deepcopy(self.state)
        key = event["order_id"]
        record = state["orders"].setdefault(key, {"total_minor": event["total_minor"],
            "lines": None, "placed": False, "cancelled": False,
            "captured": False, "refunded": False})
        if record["total_minor"] != event["total_minor"]:
            raise ValueError("Conflicting return total")
        returns = record.setdefault("returns", {})
        if event["return_id"] in returns:
            raise ValueError("Return ID reused under another event ID")
        if sum(r["refund_minor"] for r in returns.values()) + event["refund_minor"] > record["total_minor"]:
            raise ValueError("Cumulative refund exceeds order")
        returns[event["return_id"]] = event
        state["seen"][event["event_id"]] = event
        self._refund_pending(state, key)
        _save(self.path, state)
        self.state = state
        return True

    @staticmethod
    def _refund_pending(state, key):
        record = state["orders"][key]
        if not record["captured"] or record["refunded"]:
            return
        emitted = record.setdefault("return_payments", [])
        for ticket, returned in sorted(record.get("returns", {}).items()):
            if ticket in emitted:
                continue
            record["partial_refund"] = record.get("partial_refund", 0) + returned["refund_minor"]
            state.setdefault("adjustments", []).append({
                "schema": 3, "event_id": json.dumps([key, "credit", ticket]),
                "kind": "payment.return_refund", "order_id": key, "revision": 3,
                "refund_position": [record["total_minor"], record["partial_refund"]]})
            emitted.append(ticket)
