from catalog import PRICES


def total(items):
    return sum(PRICES[name] for name in items)
