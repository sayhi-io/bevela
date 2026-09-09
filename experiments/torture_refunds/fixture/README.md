# Small shop: purchase and full refund

Python standard library. Run existing checks with `python3 -m unittest -v`.
The shop is single-process; these tasks do not require simultaneous HTTP requests,
threads, a database or filesystem locks. Edit/restructure the implementation as needed.

Existing public contracts:

- `reset()` restores the seed shop. `available(sku)` excludes other customers' reservations.
- `purchase(order_id, sku, quantity=1)` deducts physical stock and returns dollars.
  Tea costs $12.50 with a 10% discount: three tea charge $33.75. Odd costs
  $1.01 with a 33.33% discount: three odd charge $2.02. Round the total once,
  to the nearest cent with ties rounded up. Reject invalid/duplicate purchases
  with ValueError before changing state.
- `refund(order_id, request_id)` refunds the full order, restocks purchased units,
  and returns `amount`, cumulative `refunded` (both dollars), `remaining` units,
  and `status`. Replaying the same request in memory returns the same result.
- `receipt(order_id)` returns a detached dict containing order_id, quantity,
  unit_price, charged, refunded, net, returned and status. Money is formatted as
  `$12.50`; original purchase amounts survive later catalog changes. Existing
  receipt caching must not serve stale data after mutations. Mutating a returned
  receipt must not change the shop.
- `save()` returns JSON text; `load(text)` replaces state from that text.
  Version 1 stores dollar amounts and separate stock/reservation dictionaries.
  Existing orders must survive round trips. Caches are not durable business state.

The present implementation supports only full refunds. Current code and tests
describe the existing schema; each task describes its requested extensions.
