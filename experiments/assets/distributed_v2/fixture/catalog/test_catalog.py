import tempfile
from pathlib import Path
import unittest
from catalog import Catalog


class CatalogLegacyChecks(unittest.TestCase):
    def test_legacy_price_and_stock_survive_restart(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "catalog.json"
            cat = Catalog(path)
            cat.put(sku="tea", title="Tea", price=2.5, stock=5)
            self.assertEqual(Catalog(path).get(sku="tea")["price"], 2.5)
            self.assertEqual(Catalog(path).get("tea")["stock"], 5)

    def test_reservation_release(self):
        with tempfile.TemporaryDirectory() as temp:
            cat = Catalog(Path(temp) / "catalog.json")
            cat.put("tea", "Tea", 2.5, 5)
            cat.reserve(reservation_id="r", items=[{"sku": "tea", "quantity": 2}])
            self.assertEqual(cat.get("tea")["stock"], 3)
            cat.release("r")
            self.assertEqual(cat.get("tea")["stock"], 5)
