# Orders return wire

Consumes Catalog's CONTRACT.md restore receipt. Emits the fixed schema-3
order.returned envelope with return_note:{ticket, units, credit, original}.
ticket is the per-order return ID; units is canonical returned SKU/quantity;
credit is incremental refund cents allocated by Catalog; original is the original
order total. event_id is JSON([order_id,"return",return_id]). revision is 3.
Each event is immutable. Distinct tickets accumulate; duplicate event IDs do not.
Legacy schema-2 placed/cancelled messages remain unchanged.
