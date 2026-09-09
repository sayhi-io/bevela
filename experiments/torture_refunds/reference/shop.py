"""Joint reference solution for oracle self-tests; NEVER supplied to workers."""
from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
import json


def cents_round(value):
    return int(Decimal(str(value)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def dollars(cents):
    return cents / 100


def reset():
    global PRICES, DISCOUNTS, STOCK, ORDERS, REQUESTS, RECEIPTS
    PRICES = {'tea': 1250, 'odd': 101}
    DISCOUNTS = {'tea': 10, 'odd': 33.33}
    STOCK = {'tea': {'on_hand': 10, 'reserved': 2}, 'odd': {'on_hand': 20, 'reserved': 0}}
    ORDERS, REQUESTS, RECEIPTS = {}, {}, {}


def available(sku):
    return STOCK[sku]['on_hand'] - STOCK[sku]['reserved']


def purchase(order_id, sku, quantity=1):
    if type(quantity) is not int or quantity <= 0 or quantity > available(sku) or order_id in ORDERS:
        raise ValueError('Invalid purchase')
    charged = cents_round(Decimal(PRICES[sku]) * quantity *
                          (1 - Decimal(str(DISCOUNTS[sku])) / 100))
    ORDERS[order_id] = {'sku': sku, 'quantity': quantity, 'unit_price': PRICES[sku],
        'charged': charged, 'refunded': 0, 'returned': 0, 'status': 'paid'}
    STOCK[sku]['on_hand'] -= quantity
    return dollars(charged)


def refund(order_id, request_id, quantity=None):
    if quantity is not None and (type(quantity) is not int or quantity <= 0):
        raise ValueError('Invalid refund quantity')
    if request_id in REQUESTS:
        previous = REQUESTS[request_id]
        if previous['order_id'] != order_id or previous['quantity'] != quantity:
            raise ValueError('Conflicting request')
        return deepcopy(previous['result'])
    order = ORDERS[order_id]
    count = order['quantity'] - order['returned'] if quantity is None else quantity
    if count <= 0 or count > order['quantity'] - order['returned']:
        raise ValueError('Over-refund')
    returned = order['returned'] + count
    cumulative = cents_round(Decimal(order['charged']) * returned / order['quantity'])
    amount = cumulative - order['refunded']
    status = 'refunded' if returned == order['quantity'] else 'partially_refunded'
    STOCK[order['sku']]['on_hand'] += count
    order.update(refunded=cumulative, returned=returned, status=status)
    result = {'amount': dollars(amount), 'refunded': dollars(cumulative),
              'remaining': order['quantity'] - returned, 'status': status}
    REQUESTS[request_id] = {'order_id': order_id, 'quantity': quantity, 'result': deepcopy(result)}
    RECEIPTS.pop(order_id, None)
    return result


def receipt(order_id):
    if order_id not in RECEIPTS:
        order = ORDERS[order_id]
        RECEIPTS[order_id] = {'order_id': order_id, 'quantity': order['quantity'],
            'unit_price': f"${dollars(order['unit_price']):.2f}",
            'charged': f"${dollars(order['charged']):.2f}",
            'refunded': f"${dollars(order['refunded']):.2f}",
            'net': f"${dollars(order['charged'] - order['refunded']):.2f}",
            'returned': order['returned'], 'status': order['status']}
    return deepcopy(RECEIPTS[order_id])


def save():
    return json.dumps({'version': 2, 'prices': PRICES, 'discounts': DISCOUNTS,
                       'stock': STOCK, 'orders': ORDERS, 'requests': REQUESTS})


def load(text):
    global PRICES, DISCOUNTS, STOCK, ORDERS, REQUESTS, RECEIPTS
    data = json.loads(text)
    if data['version'] == 1:
        data['prices'] = {key: cents_round(Decimal(str(value)) * 100) for key, value in data['prices'].items()}
        data['stock'] = {key: {'on_hand': value, 'reserved': data['reserved'][key]} for key, value in data['stock'].items()}
        for order in data['orders'].values():
            for field in ('unit_price', 'charged', 'refunded'):
                order[field] = cents_round(Decimal(str(order[field])) * 100)
    elif data['version'] != 2:
        raise ValueError('Unknown schema')
    PRICES, DISCOUNTS, STOCK, ORDERS = data['prices'], data['discounts'], data['stock'], data['orders']
    REQUESTS = data.get('requests', {})
    RECEIPTS = {}


reset()
