"""Post-exit original-contract probes; never called inside the worker loop."""
from contextlib import contextmanager
import importlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
PROBLEMS = ('prices', 'stock', 'weights', 'discounts', 'delivery', 'contacts', 'orders')


def equal(actual, expected):
    if actual != expected:
        raise AssertionError(f'Expected {expected!r}, got {actual!r}')


@contextmanager
def changed(module, attribute, key, value):
    values = getattr(module, attribute)
    original = values[key]
    values[key] = value
    try:
        yield
    finally:
        values[key] = original


def probe(checkout):
    # Run this in its own process; no persistent imports or edits in worker state.
    sys.path.insert(0, str(Path(checkout).resolve()))
    modules = {}
    errors = {}
    for name in ('catalog', 'checkout', 'inventory', 'shipping', 'promotions', 'delivery', 'customers', 'orders', 'presentation'):
        try:
            modules[name] = importlib.import_module(name)
        except Exception as exc:
            errors[name] = f'{type(exc).__name__}: {exc}'

    def module(name):
        if name not in modules:
            raise ValueError(errors[name])
        return modules[name]

    def labels(function, names, expected):
        equal([getattr(module('presentation'), function)(name) for name in names], expected)

    def data(name, attr, expected, integers=False):
        values = getattr(module(name), attr)
        for key, value in expected.items():
            if isinstance(value, dict):
                for field, field_value in value.items():
                    equal(values[key][field], field_value)
            else:
                equal(values[key], value)
            if integers and type(values[key]) is not int:
                raise AssertionError('Stored units must be integers, not floats/bools')

    def dynamic(name, attr, key, value, callback):
        with changed(module(name), attr, key, value):
            callback()

    items = ['tea', 'cake']
    cases = {
        'prices': {
            'producer': [lambda: data('catalog', 'PRICES', {'tea': 1250, 'cake': 725}, True),
                lambda: equal([module('checkout').total(items), module('checkout').total([])], [19.75, 0]),
                lambda: dynamic('catalog', 'PRICES', 'tea', 1500, lambda: equal(module('checkout').total(items), 22.25))],
            'consumer': [lambda: labels('price_label', items, ['$12.50', '$7.25']),
                lambda: dynamic('catalog', 'PRICES', 'tea', 1500, lambda: labels('price_label', ['tea'], ['$15.00']))],
        },
        'stock': {
            'producer': [lambda: data('inventory', 'STOCK', {'tea': {'on_hand': 10, 'reserved': 2}, 'cake': {'on_hand': 5, 'reserved': 1}}),
                lambda: equal([module('inventory').available(n) for n in items], [8, 4]),
                lambda: dynamic('inventory', 'STOCK', 'tea', {'on_hand': 12, 'reserved': 3}, lambda: equal(module('inventory').available('tea'), 9))],
            'consumer': [lambda: labels('stock_label', items, ['8 available', '4 available']),
                lambda: dynamic('inventory', 'STOCK', 'tea', {'on_hand': 12, 'reserved': 3}, lambda: labels('stock_label', ['tea'], ['9 available']))],
        },
        'weights': {
            'producer': [lambda: data('shipping', 'WEIGHTS', {'tea': 250, 'cake': 500}, True),
                lambda: equal(module('shipping').parcel_kg(items), 0.75),
                lambda: dynamic('shipping', 'WEIGHTS', 'tea', 375, lambda: equal(module('shipping').parcel_kg(items), 0.875))],
            'consumer': [lambda: labels('weight_label', items, ['0.250 kg', '0.500 kg']),
                lambda: dynamic('shipping', 'WEIGHTS', 'tea', 375, lambda: labels('weight_label', ['tea'], ['0.375 kg']))],
        },
        'discounts': {
            'producer': [lambda: data('promotions', 'DISCOUNTS', {'tea': 1000, 'cake': 2000}, True),
                lambda: equal([module('promotions').discounted_total(n) for n in items], [11.25, 5.8]),
                lambda: equal(module('promotions').discounted_total('tea', 2), 22.5),
                lambda: dynamic('promotions', 'DISCOUNTS', 'tea', 2000, lambda: equal(module('promotions').discounted_total('tea'), 10)),
                lambda: dynamic('catalog', 'PRICES', 'tea', 1600, lambda: equal(module('promotions').discounted_total('tea'), 14.4))],
            'consumer': [lambda: labels('discount_label', items, ['10% off; $11.25', '20% off; $5.80']),
                lambda: dynamic('promotions', 'DISCOUNTS', 'tea', 2000, lambda: labels('discount_label', ['tea'], ['20% off; $10.00'])),
                lambda: dynamic('catalog', 'PRICES', 'tea', 1600, lambda: labels('discount_label', ['tea'], ['10% off; $14.40']))],
        },
        'delivery': {
            'producer': [lambda: data('delivery', 'LEAD_TIME', {'tea': 48, 'cake': 24}, True),
                lambda: equal([module('delivery').days(n) for n in items], [2, 1]),
                lambda: dynamic('delivery', 'LEAD_TIME', 'tea', 72, lambda: equal(module('delivery').days('tea'), 3))],
            'consumer': [lambda: labels('delivery_label', items, ['2 days', '1 day']),
                lambda: dynamic('delivery', 'LEAD_TIME', 'tea', 72, lambda: labels('delivery_label', ['tea'], ['3 days']))],
        },
        'contacts': {
            'producer': [lambda: data('customers', 'CONTACTS', {'ada': {'email': 'ada@example.test', 'display_name': 'Ada'}, 'lin': {'email': 'lin@example.test', 'display_name': 'Lin'}}),
                lambda: equal([module('customers').email(n) for n in ('ada', 'lin')], ['ada@example.test', 'lin@example.test']),
                lambda: dynamic('customers', 'CONTACTS', 'ada', {'email': 'ada2@example.test', 'display_name': 'Ada Lovelace'}, lambda: equal(module('customers').email('ada'), 'ada2@example.test'))],
            'consumer': [lambda: labels('contact_label', ['ada', 'lin'], ['Ada <ada@example.test>', 'Lin <lin@example.test>']),
                lambda: dynamic('customers', 'CONTACTS', 'ada', {'email': 'ada2@example.test', 'display_name': 'Ada Lovelace'}, lambda: labels('contact_label', ['ada'], ['Ada Lovelace <ada2@example.test>']))],
        },
        'orders': {
            'producer': [lambda: data('orders', 'STATUS', {'P-1': 'paid', 'P-2': 'pending', 'R-3': 'refunded'}),
                lambda: equal([module('orders').is_paid(n) for n in ('P-1', 'P-2', 'R-3')], [True, False, False]),
                lambda: dynamic('orders', 'STATUS', 'P-2', 'paid', lambda: equal(module('orders').is_paid('P-2'), True))],
            'consumer': [lambda: labels('status_label', ['P-1', 'P-2', 'R-3'], ['Paid', 'Awaiting payment', 'Refunded']),
                lambda: dynamic('orders', 'STATUS', 'P-2', 'paid', lambda: labels('status_label', ['P-2'], ['Paid']))],
        },
    }
    keyword_contracts = {
        'prices': ('checkout', 'total', {'items': items}, 19.75),
        'stock': ('inventory', 'available', {'name': 'tea'}, 8),
        'weights': ('shipping', 'parcel_kg', {'items': items}, 0.75),
        'discounts': ('promotions', 'discounted_total', {'name': 'tea', 'quantity': 2}, 22.5),
        'delivery': ('delivery', 'days', {'name': 'tea'}, 2),
        'contacts': ('customers', 'email', {'customer': 'ada'}, 'ada@example.test'),
        'orders': ('orders', 'is_paid', {'order': 'P-1'}, True),
    }
    for problem, (name, function, kwargs, expected) in keyword_contracts.items():
        cases[problem]['producer'].append(
            lambda name=name, function=function, kwargs=kwargs, expected=expected:
                equal(getattr(module(name), function)(**kwargs), expected))
    results = {}
    for problem in PROBLEMS:
        row = {}
        for role, checks in cases[problem].items():
            failures = []
            for index, check in enumerate(checks):
                try:
                    check()
                except Exception as exc:
                    failures.append({'check': index + 1, 'error': f'{type(exc).__name__}: {exc}'})
            row[role] = {'passed': not failures, 'failures': failures, 'checks': len(checks)}
        row['both_preserved'] = row['producer']['passed'] and row['consumer']['passed']
        results[problem] = row
    return {'problems': results, 'score': sum(r['both_preserved'] for r in results.values()), 'out_of': 7,
            'meaning': 'Original task examples and current-data behavior only; not broad correctness or causal PI benefit'}


if __name__ == '__main__':
    print(json.dumps(probe(sys.argv[1]), indent=2))
