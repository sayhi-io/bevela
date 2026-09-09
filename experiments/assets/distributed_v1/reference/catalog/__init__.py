import copy
import json
import os
from pathlib import Path
import tempfile
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def _minor(value):
    if isinstance(value, bool):
        raise ValueError("Invalid dollars")
    try:
        number = Decimal(str(value))
        if not number.is_finite() or number < 0:
            raise ValueError("Invalid dollars")
        return int((number * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except (InvalidOperation, TypeError):
        raise ValueError("Invalid dollars") from None


def _integer(value, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError("Invalid integer")
    return value


def _identity(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Invalid identifier")
    return value


def _save(path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix="." + path.name)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(state, stream, sort_keys=True)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def _load(path, empty):
    state = json.loads(path.read_text()) if path.exists() else empty
    if state.get("version") not in (1, 2):
        raise ValueError("Unsupported stored version")
    return state

def _basket(items):
    if not isinstance(items, list) or not items:
        raise ValueError("Empty or invalid basket")
    quantities = {}
    for item in items:
        try:
            sku = _identity(item["sku"])
            quantity = _integer(item["quantity"], 1)
        except (KeyError, TypeError):
            raise ValueError("Invalid basket item") from None
        quantities[sku] = quantities.get(sku, 0) + quantity
    return [{"sku": sku, "quantity": quantities[sku]} for sku in sorted(quantities)]


def _old_lines(items):
    return sorted([{"sku": i["sku"], "title": i["title"], "quantity": i["quantity"],
                    "unit_minor": _minor(i["price"]),
                    "line_minor": _minor(i["price"]) * i["quantity"]}
                   for i in items], key=lambda i: i["sku"])

class Catalog:
    def __init__(self, path):
        self.path = Path(path)
        self.state = _load(self.path, {"version": 2, "products": {}, "reservations": {}})
        if self.state["version"] == 1:
            for product in self.state["products"].values():
                product["unit_minor"] = _minor(product.pop("price"))
            reservations = {}
            for key, old in self.state.get("reservations", {}).items():
                reservations[key] = {"basket": _basket(old["items"]), "released": old["released"],
                    "receipt": {"schema": 2, "reservation_id": key, "lines": _old_lines(old["items"]),
                                "total_minor": _minor(old["total"])}}
            self.state.update(version=2, reservations=reservations)
        _save(self.path, self.state)

    def put(self, sku, title, price, stock):
        self.put_minor(sku, title, _minor(price), stock)

    def put_minor(self, sku, title, unit_minor, stock):
        _identity(sku)
        _identity(title)
        _integer(unit_minor)
        _integer(stock)
        state = copy.deepcopy(self.state)
        state["products"][sku] = {"title": title, "unit_minor": unit_minor, "stock": stock}
        _save(self.path, state)
        self.state = state

    def get(self, sku):
        _identity(sku)
        try:
            p = self.state["products"][sku]
        except (KeyError, TypeError):
            raise ValueError("Unknown SKU") from None
        return {"sku": sku, "title": p["title"], "price": p["unit_minor"] / 100, "stock": p["stock"]}

    def quote(self, sku, quantity=1):
        _integer(quantity, 1)
        self.get(sku)
        p = self.state["products"][sku]
        return {"sku": sku, "title": p["title"], "quantity": quantity,
                "unit_minor": p["unit_minor"], "line_minor": p["unit_minor"] * quantity}

    def reserve(self, reservation_id, items):
        _identity(reservation_id)
        basket = _basket(items)
        prior = self.state["reservations"].get(reservation_id)
        if prior:
            if prior["basket"] != basket or prior["released"]:
                raise ValueError("Conflicting or released reservation")
            return copy.deepcopy(prior["receipt"])
        lines = [self.quote(**item) for item in basket]
        if any(self.state["products"][i["sku"]]["stock"] < i["quantity"] for i in basket):
            raise ValueError("Insufficient stock")
        receipt = {"schema": 2, "reservation_id": reservation_id, "lines": lines,
                   "total_minor": sum(i["line_minor"] for i in lines)}
        state = copy.deepcopy(self.state)
        for item in basket:
            state["products"][item["sku"]]["stock"] -= item["quantity"]
        state["reservations"][reservation_id] = {"basket": basket, "receipt": receipt, "released": False}
        _save(self.path, state)
        self.state = state
        return copy.deepcopy(receipt)

    def release(self, reservation_id):
        _identity(reservation_id)
        if reservation_id not in self.state["reservations"]:
            raise ValueError("Unknown reservation")
        if self.state["reservations"][reservation_id]["released"]:
            return False
        state = copy.deepcopy(self.state)
        reservation = state["reservations"][reservation_id]
        for item in reservation["basket"]:
            state["products"][item["sku"]]["stock"] += item["quantity"]
        reservation["released"] = True
        _save(self.path, state)
        self.state = state
        return True
