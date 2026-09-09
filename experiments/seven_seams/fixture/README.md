# Small shop

Python standard-library code. Existing tests: python3 -m unittest -v.
Customer-facing presentation functions are currently unimplemented.

The public helpers use current data and have these existing contracts:

- checkout.total(items): dollars; tea+cake = 19.75, empty = 0.
- inventory.available(name): sellable units; tea = 8, cake = 4.
- shipping.parcel_kg(items): kilograms; tea+cake = 0.75.
- promotions.discounted_total(name, quantity=1): dollars; tea = 11.25,
  cake = 5.80, two tea = 22.50.
- delivery.days(name): days; tea = 2, cake = 1.
- customers.email(customer): address string; ada@example.test and lin@example.test.
- orders.is_paid(order): True for P-1, False for P-2 and R-3.

The source contains the current representations and seed data. Preserve the public
helper names/signatures and data-driven behavior when making changes.
