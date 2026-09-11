import tempfile
from pathlib import Path
import unittest
from reporting import Reporting


class ReportingLegacyChecks(unittest.TestCase):
    def test_legacy_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "reporting.json"
            report = Reporting(path)
            report.handle(event={"schema": 1, "event_id": "a:placed", "kind": "order.placed",
                "order_id": "a", "revision": 1, "items": [
                {"sku": "tea", "title": "Tea", "quantity": 2, "price": 2.5}], "total": 5.0})
            report.handle({"schema": 1, "event_id": "a:captured", "kind": "payment.captured",
                "order_id": "a", "revision": 1, "amount": 5.0})
            self.assertEqual(Reporting(path).legacy_receipt(order_id="a"), "a: $5.00 (paid)")

    def test_unknown_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            report = Reporting(Path(temp) / "reporting.json")
            self.assertIsNone(report.legacy_receipt("unknown"))
