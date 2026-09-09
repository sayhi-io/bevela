"""Frozen post-exit probes for the refund/migration concurrent-edit study."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
PROBLEMS = ('units', 'both_features', 'rounding', 'inventory', 'retry_safety', 'persistence', 'receipts')


def equal(actual, expected):
    if actual != expected:
        raise AssertionError(f'Expected {expected!r}, got {actual!r}')


def rejected_without_change(shop, action):
    before = json.loads(shop.save())
    try:
        action()
    except ValueError:
        equal(json.loads(shop.save()), before)
    else:
        raise AssertionError('Expected ValueError without business-state mutation')


def probe(root):
    root = Path(root).resolve()
    sys.path.insert(0, str(root))
    spec = importlib.util.spec_from_file_location('shop', root / 'shop.py')
    shop = importlib.util.module_from_spec(spec)
    sys.modules['shop'] = shop
    try:
        spec.loader.exec_module(shop)
    except Exception as exc:
        return {'score': 0, 'out_of': 7, 'problems': {name: {'passed': False, 'error': f'{type(exc).__name__}: {exc}'} for name in PROBLEMS}}

    def units():
        equal(type(shop.PRICES['tea']), int)
        equal(shop.PRICES['tea'], 1250)
        shop.DISCOUNTS['tea'] = 0
        equal(shop.purchase('a', 'tea', 3), 37.5)
        equal(shop.ORDERS['a']['charged'], 3750)
        equal(type(shop.ORDERS['a']['charged']), int)
        equal(shop.refund('a', 'one', quantity=1), {'amount': 12.5, 'refunded': 12.5, 'remaining': 2, 'status': 'partially_refunded'})
        equal(shop.ORDERS['a']['refunded'], 1250)
        equal(type(shop.ORDERS['a']['refunded']), int)

    def both_features():
        equal(shop.purchase(order_id='a', sku='tea', quantity=3), 33.75)
        equal(shop.refund('a', 'first', quantity=1)['amount'], 11.25)
        equal(shop.refund('a', 'rest')['amount'], 22.5)
        equal(shop.available('tea'), 8)
        equal(shop.receipt('a')['status'], 'refunded')
        state = json.loads(shop.save())
        equal(state['version'], 2)
        equal(state['prices']['tea'], 1250)
        equal(state['orders']['a']['charged'], 3375)
        equal(state['stock']['tea'], {'on_hand': 10, 'reserved': 2})
        if 'reserved' in state:
            raise AssertionError('Version 2 retained the separate reservation dictionary')
        rejected_without_change(shop, lambda: shop.purchase('a', 'tea', 1))
        rejected_without_change(shop, lambda: shop.purchase('b', 'tea', 99))

    def rounding():
        for cents, discount, charged, pieces in (
                (101, 33.33, 2.02, [0.67, 0.68, 0.67]),
                (50, 33.33, 1.0, [0.33, 0.34, 0.33]),
                (1, 0, 0.03, [0.01, 0.01, 0.01])):
            shop.reset()
            shop.PRICES['odd'], shop.DISCOUNTS['odd'] = cents, discount
            equal(shop.purchase('a', 'odd', 3), charged)
            shop.PRICES['odd'], shop.DISCOUNTS['odd'] = 9900, 0
            refunds = [shop.refund('a', f'r{n}', quantity=1)['amount'] for n in range(3)]
            equal(refunds, pieces)
            equal(round(sum(refunds), 2), charged)
            equal(shop.receipt('a')['net'], '$0.00')

    def inventory():
        shop.purchase('a', 'tea', 3)
        equal(shop.STOCK['tea'], {'on_hand': 7, 'reserved': 2})
        equal(shop.available('tea'), 5)
        first = shop.refund('a', 'r', quantity=1)
        equal(shop.STOCK['tea'], {'on_hand': 8, 'reserved': 2})
        equal(shop.available('tea'), 6)
        equal(shop.refund('a', 'r', quantity=1), first)
        equal(shop.available('tea'), 6)
        shop.refund('a', 'rest')
        equal(shop.STOCK['tea'], {'on_hand': 10, 'reserved': 2})
        rejected_without_change(shop, lambda: shop.refund('a', 'extra', quantity=1))

    def retry_safety():
        shop.purchase('a', 'tea', 3)
        shop.purchase('b', 'tea', 1)
        first = shop.refund('a', 'r', quantity=1)
        for bad in (0, -1, True, 1.5, '1', 3):
            rejected_without_change(shop, lambda bad=bad: shop.refund('a', f'bad-{bad!r}', quantity=bad))
        rejected_without_change(shop, lambda: shop.refund('b', 'r', quantity=1))
        rejected_without_change(shop, lambda: shop.refund('a', 'r', quantity=2))
        final = shop.refund('a', 'tail')
        saved = shop.save()
        shop.reset()
        shop.load(saved)
        before = json.loads(shop.save())
        equal(shop.refund('a', 'r', quantity=1), first)
        equal(shop.refund('a', 'tail'), final)
        equal(json.loads(shop.save()), before)
        rejected_without_change(shop, lambda: shop.refund('b', 'r', quantity=1))
        rejected_without_change(shop, lambda: shop.refund('a', 'tail', quantity=2))

    def persistence():
        legacy = {'version': 1, 'prices': {'tea': 12.5}, 'discounts': {'tea': 10},
            'stock': {'tea': 7}, 'reserved': {'tea': 2}, 'orders': {
                'old': {'sku': 'tea', 'quantity': 3, 'unit_price': 12.5, 'charged': 33.75,
                        'refunded': 0.0, 'returned': 0, 'status': 'paid', 'note': {'keep': 'history'}}}}
        shop.load(json.dumps(legacy))
        equal(shop.ORDERS['old']['unit_price'], 1250)
        equal(shop.available('tea'), 5)
        first = shop.refund('old', 'r', quantity=1)
        for _ in range(3):
            saved = shop.save()
            shop.reset()
            shop.load(saved)
            equal(shop.ORDERS['old']['note'], {'keep': 'history'})
            equal(shop.ORDERS['old']['charged'], 3375)
            equal(shop.ORDERS['old']['refunded'], 1125)
            equal(shop.refund('old', 'r', quantity=1), first)
        equal(shop.refund('old', 'rest')['amount'], 22.5)
        equal(shop.available('tea'), 8)

    def receipts():
        shop.purchase('a', 'tea', 3)
        original = shop.receipt('a')
        equal(original, {'order_id': 'a', 'quantity': 3, 'unit_price': '$12.50',
            'charged': '$33.75', 'refunded': '$0.00', 'net': '$33.75', 'returned': 0, 'status': 'paid'})
        shop.PRICES['tea'], shop.DISCOUNTS['tea'] = 9900, 0
        shop.refund('a', 'r', quantity=1)
        expected = dict(original, refunded='$11.25', net='$22.50', returned=1, status='partially_refunded')
        equal(shop.receipt('a'), expected)
        returned = shop.receipt('a')
        returned['charged'] = '$0.00'
        equal(shop.receipt('a'), expected)
        saved = shop.save()
        shop.refund('a', 'rest')
        equal(shop.receipt('a')['net'], '$0.00')
        shop.load(saved)
        equal(shop.receipt('a'), expected)
        equal(original['refunded'], '$0.00')

    cases = dict(zip(PROBLEMS, (units, both_features, rounding, inventory, retry_safety, persistence, receipts)))
    outcomes = {}
    for name, case in cases.items():
        try:
            shop.reset()
            case()
            outcomes[name] = {'passed': True, 'error': None}
        except Exception as exc:
            outcomes[name] = {'passed': False, 'error': f'{type(exc).__name__}: {exc}'}
    return {'score': sum(row['passed'] for row in outcomes.values()), 'out_of': 7, 'problems': outcomes,
            'meaning': 'Seven correlated contract groups, not proof of race causation or general correctness.'}


if __name__ == '__main__':
    print(json.dumps(probe(sys.argv[1]), indent=2))
