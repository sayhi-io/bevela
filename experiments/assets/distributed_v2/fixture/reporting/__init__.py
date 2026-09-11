"""Working v1 receipts: historical delivery was placement, then payment."""
import copy
import json
from pathlib import Path


class Reporting:
    def __init__(self, path):
        self.path = Path(path)
        self.state = json.loads(self.path.read_text()) if self.path.exists() else {
            "version": 1, "receipts": {}, "seen": {}}
        self.save()

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.state, sort_keys=True))

    def handle(self, event):
        if event["event_id"] in self.state["seen"]:
            return False
        key = event["order_id"]
        if event["kind"] == "order.placed":
            self.state["receipts"][key] = {"order_id": key, "items": copy.deepcopy(event["items"]),
                "total": event["total"], "paid": 0, "status": "placed"}
        elif key in self.state["receipts"]:
            receipt = self.state["receipts"][key]
            if event["kind"] == "payment.captured":
                receipt.update(paid=event["amount"], status="paid")
            elif event["kind"] == "payment.refunded":
                receipt.update(paid=0, status="refunded")
            elif event["kind"] == "order.cancelled":
                receipt["status"] = "cancelled"
        self.state["seen"][event["event_id"]] = copy.deepcopy(event)
        self.save()
        return True

    def receipt(self, order_id):
        return copy.deepcopy(self.state["receipts"].get(order_id))

    def revenue(self):
        return sum(r["paid"] for r in self.state["receipts"].values())

    def legacy_receipt(self, order_id):
        receipt = self.receipt(order_id)
        if receipt is None:
            return None
        return f"{order_id}: $" + f"{receipt['total']:.2f} ({receipt['status']})"
