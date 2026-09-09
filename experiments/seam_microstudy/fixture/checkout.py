from catalog import PRICES


def total(items):
    """Basket total in dollars; items is a list of product names."""
    return sum(PRICES[item] for item in items)
