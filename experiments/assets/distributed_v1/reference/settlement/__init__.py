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
        for record in state["orders"].values():
            if record["placed"] and not record["cancelled"] and not record["captured"]:
                record["captured"] = True
                count += 1
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

    def balance(self):
        return sum(r["total_minor"] * (int(r["captured"]) - int(r["refunded"]))
                   for r in self.state["orders"].values())
