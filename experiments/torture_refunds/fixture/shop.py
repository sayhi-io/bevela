"""Small in-memory shop; public money is dollars, persisted state is JSON."""
from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
import json


def rounded(value):
    return float(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def reset():
    global PRICES, DISCOUNTS, STOCK, RESERVED, ORDERS, REQUESTS, RECEIPTS
    PRICES = {'tea': 12.50, 'odd': 1.01}
    DISCOUNTS = {'tea': 10, 'odd': 33.33}
    STOCK = {'tea': 10, 'odd': 20}
    RESERVED = {'tea': 2, 'odd': 0}
    ORDERS, REQUESTS, RECEIPTS = {}, {}, {}


def available(sku):
    return STOCK[sku] - RESERVED[sku]


def purchase(order_id, sku, quantity=1):
    if type(quantity) is not int or quantity <= 0 or quantity > available(sku) or order_id in ORDERS:
        raise ValueError('Invalid purchase')
    charged = rounded(Decimal(str(PRICES[sku])) * quantity *
                      (1 - Decimal(str(DISCOUNTS[sku])) / 100))
    order = {'sku': sku, 'quantity': quantity, 'unit_price': PRICES[sku],
             'charged': charged, 'refunded': 0.0, 'returned': 0, 'status': 'paid'}
    ORDERS[order_id] = order
    STOCK[sku] -= quantity
    return charged


def refund(order_id, request_id):
    if request_id in REQUESTS:
        return deepcopy(REQUESTS[request_id])
    order = ORDERS[order_id]
    if order['status'] == 'refunded':
        raise ValueError('Already refunded')
    amount = order['charged']
    STOCK[order['sku']] += order['quantity']
    order.update(refunded=amount, returned=order['quantity'], status='refunded')
    result = {'amount': amount, 'refunded': amount, 'remaining': 0, 'status': 'refunded'}
    REQUESTS[request_id] = deepcopy(result)
    RECEIPTS.pop(order_id, None)
    return result


def receipt(order_id):
    if order_id not in RECEIPTS:
        order = ORDERS[order_id]
        RECEIPTS[order_id] = {'order_id': order_id, 'quantity': order['quantity'],
            'unit_price': f"${order['unit_price']:.2f}", 'charged': f"${order['charged']:.2f}",
            'refunded': f"${order['refunded']:.2f}",
            'net': f"${order['charged'] - order['refunded']:.2f}",
            'returned': order['returned'], 'status': order['status']}
    return deepcopy(RECEIPTS[order_id])


def save():
    fields = ('sku', 'quantity', 'unit_price', 'charged', 'refunded', 'returned', 'status')
    return json.dumps({'version': 1, 'prices': PRICES, 'discounts': DISCOUNTS,
        'stock': STOCK, 'reserved': RESERVED,
        'orders': {key: {field: order[field] for field in fields} for key, order in ORDERS.items()}})


def load(text):
    global PRICES, DISCOUNTS, STOCK, RESERVED, ORDERS, REQUESTS, RECEIPTS
    data = json.loads(text)
    if data['version'] != 1:
        raise ValueError('Unknown schema')
    PRICES, DISCOUNTS = data['prices'], data['discounts']
    STOCK, RESERVED, ORDERS = data['stock'], data['reserved'], data['orders']
    REQUESTS, RECEIPTS = {}, {}


reset()
