import unittest

from checkout import total


class CheckoutTests(unittest.TestCase):
    def test_total(self):
        self.assertEqual(total(["tea", "cake"]), 19.75)
        self.assertEqual(total(["tea", "tea"]), 25.00)
        self.assertEqual(total([]), 0)
