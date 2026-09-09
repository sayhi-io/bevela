import tempfile
from pathlib import Path
import unittest
from orders import Orders


class CatalogStub:
    def reserve(self, reservation_id, items):
        # Local legacy-facing checks accept either generation of the catalog wire.
        return {"items": [{"sku": "tea", "title": "Tea", "quantity": 2, "price": 2.5}],
                "total": 5.0, "lines": [{"sku": "tea", "title": "Tea", "quantity": 2,
                "unit_minor": 250, "line_minor": 500}], "total_minor": 500}

    def release(self, reservation_id):
        return True


class OrdersLegacyChecks(unittest.TestCase):
    def test_legacy_summary_and_idempotent_key(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "orders.json"
            orders = Orders(path, CatalogStub())
            items = [{"sku": "tea", "quantity": 2}]
            self.assertEqual(orders.place(key="a", items=items), "a")
            self.assertEqual(Orders(path, CatalogStub()).place("a", items), "a")
            self.assertEqual(orders.legacy(order_id="a")["total"], 5.0)

    def test_cancelled_summary(self):
        with tempfile.TemporaryDirectory() as temp:
            orders = Orders(Path(temp) / "orders.json", CatalogStub())
            orders.place("a", [{"sku": "tea", "quantity": 2}])
            orders.cancel(order_id="a")
            self.assertEqual(orders.legacy("a")["status"], "cancelled")
