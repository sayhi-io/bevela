"""Working v1 dollar catalog with persisted inventory holds."""
import copy
import json
from pathlib import Path


class Catalog:
    def __init__(self, path):
        self.path = Path(path)
        self.state = json.loads(self.path.read_text()) if self.path.exists() else {
            "version": 1, "products": {}, "reservations": {}}
        self.save()

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.state, sort_keys=True))

    def put(self, sku, title, price, stock):
        self.state["products"][sku] = {"title": title, "price": float(price), "stock": stock}
        self.save()

    def get(self, sku):
        if sku not in self.state["products"]:
            raise ValueError("Unknown SKU")
        return dict(sku=sku, **self.state["products"][sku])

    def reserve(self, reservation_id, items):
        if reservation_id in self.state["reservations"]:
            return copy.deepcopy(self.state["reservations"][reservation_id])
        lines = []
        for item in items:
            product = self.get(item["sku"])
            if product["stock"] < item["quantity"]:
                raise ValueError("Insufficient stock")
            lines.append({"sku": item["sku"], "title": product["title"],
                          "quantity": item["quantity"], "price": product["price"]})
        for item in items:
            self.state["products"][item["sku"]]["stock"] -= item["quantity"]
        record = {"reservation_id": reservation_id, "items": lines,
                  "total": sum(i["price"] * i["quantity"] for i in lines), "released": False}
        self.state["reservations"][reservation_id] = record
        self.save()
        return copy.deepcopy(record)

    def release(self, reservation_id):
        record = self.state["reservations"][reservation_id]
        if record["released"]:
            return False
        for item in record["items"]:
            self.state["products"][item["sku"]]["stock"] += item["quantity"]
        record["released"] = True
        self.save()
        return True
