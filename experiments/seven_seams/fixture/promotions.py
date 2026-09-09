from checkout import total

DISCOUNTS = {"tea": 10, "cake": 20}


def discounted_total(name, quantity=1):
    return round(total([name] * quantity) * (1 - DISCOUNTS[name] / 100), 2)
