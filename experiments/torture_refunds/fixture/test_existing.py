import unittest
import shop


class ExistingContracts(unittest.TestCase):
    def setUp(self):
        shop.reset()

    def test_purchase_and_full_refund(self):
        self.assertEqual(shop.purchase('a', 'tea', 3), 33.75)
        self.assertEqual(shop.available('tea'), 5)
        shop.receipt('a')
        result = shop.refund('a', 'r')
        self.assertEqual(result, {'amount': 33.75, 'refunded': 33.75, 'remaining': 0, 'status': 'refunded'})
        self.assertEqual(shop.refund('a', 'r'), result)
        self.assertEqual(shop.available('tea'), 8)
        self.assertEqual(shop.receipt('a')['net'], '$0.00')

    def test_roundtrip_and_snapshot(self):
        shop.purchase('a', 'tea', 3)
        expected = shop.receipt('a')
        shop.load(shop.save())
        self.assertEqual(shop.receipt('a'), expected)
        self.assertEqual(shop.purchase('odd', 'odd', 3), 2.02)


if __name__ == '__main__':
    unittest.main()
