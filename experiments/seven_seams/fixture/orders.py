STATUS = {"P-1": True, "P-2": False, "R-3": False}
REFUNDED = {"R-3"}


def is_paid(order):
    return bool(STATUS[order])
