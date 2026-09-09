import unittest

from checkout import total
from inventory import available
from shipping import parcel_kg
from promotions import discounted_total
from delivery import days
from customers import email
from orders import is_paid


class ExistingBehavior(unittest.TestCase):
    def test_checkout(self):
        self.assertEqual(total(["tea", "cake"]), 19.75)
        self.assertEqual(total([]), 0)

    def test_inventory(self):
        self.assertEqual([available("tea"), available("cake")], [8, 4])

    def test_shipping(self):
        self.assertEqual(parcel_kg(["tea", "cake"]), 0.75)

    def test_promotions(self):
        self.assertEqual([discounted_total("tea"), discounted_total("cake")], [11.25, 5.8])

    def test_delivery(self):
        self.assertEqual([days("tea"), days("cake")], [2, 1])

    def test_contacts(self):
        self.assertEqual(email("ada"), "ada@example.test")

    def test_orders(self):
        self.assertEqual([is_paid("P-1"), is_paid("P-2"), is_paid("R-3")], [True, False, False])


if __name__ == "__main__":
    unittest.main()
