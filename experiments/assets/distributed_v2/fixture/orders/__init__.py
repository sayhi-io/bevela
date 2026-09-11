"""Working v1 dollar order journal and outgoing events."""
import copy
import json
from pathlib import Path


class Orders:
    def __init__(self, path, catalog):
        self.path, self.catalog = Path(path), catalog
        self.state = json.loads(self.path.read_text()) if self.path.exists() else {
            "version": 1, "orders": {}, "acked": []}
        self.save()

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.state, sort_keys=True))

    def place(self, key, items):
        if key not in self.state["orders"]:
            held = self.catalog.reserve(key, items)
            self.state["orders"][key] = {"order_id": key, "items": held["items"],
                                        "total": held["total"], "status": "placed"}
            self.save()
        return key

    def get(self, order_id):
        return copy.deepcopy(self.state["orders"][order_id])

    def legacy(self, order_id):
        record = self.get(order_id)
        return {k: record[k] for k in ("order_id", "total", "status")}

    def cancel(self, order_id):
        record = self.state["orders"][order_id]
        if record["status"] == "cancelled":
            return False
        self.catalog.release(order_id)
        record["status"] = "cancelled"
        self.save()
        return True

    def events(self):
        events = []
        for key, record in sorted(self.state["orders"].items()):
            kinds = ["placed", "cancelled"] if record["status"] == "cancelled" else ["placed"]
            for revision, kind in enumerate(kinds, 1):
                event_id = key + ":" + kind
                if event_id not in self.state["acked"]:
                    events.append({"schema": 1, "event_id": event_id, "kind": "order." + kind,
                        "order_id": key, "revision": revision,
                        "items": copy.deepcopy(record["items"]), "total": record["total"]})
        return events

    def ack(self, event_id):
        if event_id not in self.state["acked"]:
            self.state["acked"].append(event_id)
            self.save()
