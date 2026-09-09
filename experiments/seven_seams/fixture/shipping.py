WEIGHTS = {"tea": 0.250, "cake": 0.500}


def parcel_kg(items):
    return sum(WEIGHTS[name] for name in items)
