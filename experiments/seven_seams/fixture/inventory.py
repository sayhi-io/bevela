STOCK = {"tea": 10, "cake": 5}
RESERVED = {"tea": 2, "cake": 1}


def available(name):
    return STOCK[name] - RESERVED[name]
