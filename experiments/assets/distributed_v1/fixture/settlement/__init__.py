"""Working v1 immediate payments for in-order legacy delivery."""
import copy
import json
from pathlib import Path


class Settlement:
    def __init__(self, path):
        self.path = Path(path)
        self.state = json.loads(self.path.read_text()) if self.path.exists() else {
            "version": 1, "payments": {}, "seen": {}, "acked": []}
        self.save()

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.state, sort_keys=True))

    def handle(self, event):
        if event["event_id"] in self.state["seen"]:
            return False
        key = event["order_id"]
        if event["kind"] == "order.placed":
            self.state["payments"][key] = {"order_id": key, "amount": event["total"], "status": "captured"}
        elif event["kind"] == "order.cancelled":
            self.state["payments"][key]["status"] = "refunded"
        else:
            raise ValueError("Unknown order event")
        self.state["seen"][event["event_id"]] = copy.deepcopy(event)
        self.save()
        return True

    def drain(self):
        return 0

    def events(self):
        events = []
        for key, payment in sorted(self.state["payments"].items()):
            kinds = ["captured", "refunded"] if payment["status"] == "refunded" else ["captured"]
            for revision, kind in enumerate(kinds, 1):
                event_id = key + ":" + kind
                if event_id not in self.state["acked"]:
                    events.append({"schema": 1, "event_id": event_id, "kind": "payment." + kind,
                        "order_id": key, "revision": revision, "amount": payment["amount"]})
        return events

    def ack(self, event_id):
        if event_id not in self.state["acked"]:
            self.state["acked"].append(event_id)
            self.save()

    def balance(self):
        return sum(p["amount"] for p in self.state["payments"].values() if p["status"] == "captured")
