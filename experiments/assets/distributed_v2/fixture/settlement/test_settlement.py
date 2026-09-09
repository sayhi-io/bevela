import tempfile
from pathlib import Path
import unittest
from settlement import Settlement


def order():
    return {"schema": 1, "event_id": "a:placed", "kind": "order.placed",
            "order_id": "a", "revision": 1, "items": [
            {"sku": "tea", "title": "Tea", "quantity": 2, "price": 2.5}], "total": 5.0}


class SettlementLegacyChecks(unittest.TestCase):
    def test_legacy_order_creates_one_payment(self):
        with tempfile.TemporaryDirectory() as temp:
            pay = Settlement(Path(temp) / "settlement.json")
            pay.handle(event=order())
            pay.drain()
            pay.handle(order())
            pay.drain()
            self.assertEqual([e["event_id"] for e in pay.events()], ["a:captured"])

    def test_acked_payment_is_not_redelivered(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "settlement.json"
            pay = Settlement(path)
            pay.handle(order())
            pay.drain()
            pay.ack(event_id="a:captured")
            self.assertEqual(Settlement(path).events(), [])
