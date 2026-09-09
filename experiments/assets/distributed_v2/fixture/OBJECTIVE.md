# Depot migration and partial-return contract — candidate2

Implement the complete contract in this file: the original migration below plus
its partial-return extension. All business requirements are protected and equally
visible to ordinary and PI workers. The original twelve groups remain required.

Migrate the working dollar-based product to reliable integer-minor-unit commerce.
Preserve its legacy entry points while implementing the complete contract below.
All requirements are shared across ordinary and PI treatments. Four components
have distinct owned roots; there is no additional private acceptance requirement.
The observer reference implementation is not a worker input.

## Common rules and persistence

Public classes are `catalog.Catalog(path)`, `orders.Orders(path, catalog)`,
`settlement.Settlement(path)`, and `reporting.Reporting(path)`. `path` is a JSON
file path (str or Path), not a directory. Missing files mean empty state; create
parent directories as needed. Each component owns only its own file. Constructors
must read existing state, migrate version 1 to version 2, and persist migration.
New state is version 2. Reopening any component preserves completed operations,
deduplication, pending events and acknowledgments. JSON objects returned to callers
must not let subsequent caller mutation alter stored state.

Persist each state update with a same-directory temporary file and atomic replace.
Malformed JSON or unsupported stored versions must raise, not reset data. No
power-loss durability, concurrent process locking or distributed transaction is
required. Validation errors leave logical state unchanged. Do not implement sleeps,
random IDs, background workers, external services or implicit delivery.

Money is nonnegative USD integer cents in all v2 data. Booleans are invalid for
both dollar inputs and integer money/quantity validation. Dollar inputs are finite decimal strings or
numbers: interpret their decimal spelling, then round to cents with ROUND_HALF_UP.
Round each unit price before multiplication: 2.675 dollars becomes 268 cents;
three units cost 804 cents. Historical recorded totals and payments are converted
individually, not recomputed using current catalog prices. Never use binary-float
rounding for money conversion. Legacy adapters return dollars as numbers or the
specified fixed-two-decimal receipt string.

Identifiers and titles are nonempty strings. Quantities are positive integers.
A basket is a nonempty list of `{sku, quantity}`; coalesce repeated SKUs and sort
by SKU. The canonical basket determines retry identity, independent of input order.
Unknown SKU, unknown order/reservation, conflicting retry, invalid money/quantity,
unsupported event version/kind/revision, or conflicting event ID raises ValueError.
Reusing a released reservation ID is an error; repeating release is harmless.

## Catalog root: prices and inventory reservations

Keep `put(sku, title, price, stock)` accepting legacy dollar prices; add
`put_minor(sku, title, unit_minor, stock)`. Stock is a nonnegative integer of
currently available units. Updating a product changes its current price/title and
available stock, but does not rewrite existing reservation price snapshots.

Keep `get(sku)` returning `{sku, title, price, stock}` with legacy dollars and
current available stock. Add `quote(sku, quantity=1)` returning a line:
`{sku, title, quantity, unit_minor, line_minor}`. Public arguments must also work
by keyword with the names given here.

`reserve(reservation_id, items)` returns
`{schema:2, reservation_id, lines:[line...], total_minor}`. It reserves the entire
basket or nothing, decrements available inventory exactly once, and freezes prices
and titles. Identical canonical retries return the original reservation even if
prices changed. Conflicting retries raise before changing stock. Insufficient
stock in one line leaves every product unchanged. `release(reservation_id)` restores
the reserved quantities once, retaining the reservation's identity across restart.

Legacy catalog file:
`{version:1, products:{sku:{title, price:<dollars>, stock}}}`.
Version 2 retains `products`, replaces `price` with `unit_minor`, and adds persistent
reservation bookkeeping. Its internal reservation representation is your choice.
Existing v1 `reservations`, when present, map IDs to
`{reservation_id, items:[legacy order-item...], total:<dollars>, released:<bool>}`.
Preserve these original holds so legacy orders can be cancelled without reserving
again. A legacy order requiring release has its matching persisted hold; the
working v1 product already writes those records.

## Orders root: durable orders, recovery and outbox

`place(key, items, fail_after_reserve=False)` returns `key` as the stable order ID.
It uses Catalog's reservation API with reservation ID equal to key. Preserve the
canonical basket and original reservation's price snapshot, not a new quote.
Same-key retries are idempotent across restart; different baskets raise ValueError.

The explicit test fault `fail_after_reserve=True` raises RuntimeError after the
catalog reservation is persisted but before the new order is persisted. It does
not apply to an already persisted identical order. Retrying normally, with reopened
components, creates exactly one order and never reserves twice. No other crash
point or two-file atomic commit is required.

`get(order_id)` returns `{schema:2, order_id, lines, total_minor, status}`, with
status `placed` or `cancelled`. `legacy(order_id)` returns
`{order_id, total:<dollars>, status}`. `cancel(order_id)` releases stock once,
persists cancellation, and is idempotent. A cancelled key cannot be repurposed;
an identical place retry returns its existing ID without reserving again.

`events()` returns unacknowledged order events sorted by `(order_id, revision)`.
`ack(event_id)` durably suppresses a known emitted event; repeated ack is harmless,
but an unknown event ID raises ValueError. Stable event IDs are `key:placed` and
`key:cancelled`. Both carry the same original snapshot, even after catalog changes.
Do not discard unacknowledged placement merely because cancellation also exists.

Legacy order file:
`{version:1, orders:{key:{order_id, items:[{sku,title,quantity,price:<dollars>}],
total:<dollars>, status:"placed"|"cancelled"}}, acked:[event_id...]}`.
Migrate these orders without reserving their inventory again. Retain their IDs,
status, snapshots, and acknowledged event IDs.

## Wire event contract (all readers must accept both versions)

Every event has `schema`, `event_id`, `kind`, `order_id`, `revision`.
Order kinds are `order.placed` revision 1 and `order.cancelled` revision 2.
Payment kinds are `payment.captured` revision 1 and `payment.refunded` revision 2.
V2 order events additionally carry `lines` (Catalog line shape) and `total_minor`.
V2 payment events carry `amount_minor`. V1 order events instead carry `items`
(legacy order-item shape) and `total` in dollars; v1 payment events carry `amount`
in dollars. Readers must validate these fields and normalize v1 money. Order
lines must have valid quantities/money and `line_minor == quantity * unit_minor`.
The recorded total is authoritative; old rounding may differ from summed lines.
Extra fields need not be retained. Unknown schemas/kinds/revision combinations fail.

For a given event ID, an identical *normalized* event is a no-op and returns False
from `handle(event)`; a different normalized body raises ValueError without state
change. A new valid event returns True. This includes equivalent v1/v2 redelivery.
Different events for one order must agree on its recorded total/payment amount;
conflicting amounts fail before changing state or consuming the event ID.
Within an order stream, placed/cancelled events also share the same line snapshot.
Deliveries can be delayed, duplicated, or arrive in any order. Greater revisions
dominate smaller ones; a late placement/capture must not undo cancellation/refund.

## Settlement root: deferred capture, cancellation and redelivery

`handle(event)` accepts the two order kinds in either wire version. It records
intents durably but does not capture payment merely upon delivery. `drain()` captures
every placed, not-cancelled, not-already-captured order and returns the number newly
captured. It can be called repeatedly and after restart. Cancellation before drain
prevents capture, including cancellation delivered before placement. A cancellation
after capture refunds exactly once; a later placement cannot cause recapture.

`events()` exposes pending v2 payment events sorted by `(order_id, revision)`.
IDs are `key:captured` and `key:refunded`. Both use the original order amount;
refund amount is positive (reporting subtracts it). Capture remains available until
acked even if a refund was produced. `ack(event_id)` follows the Orders rules.
`balance()` is captured cents minus refunded cents across all orders, an integer.

Legacy settlement file:
`{version:1, payments:{key:{order_id, amount:<dollars>, status:"captured"|"refunded"}},
seen:{event_id:<original v1 order event>}, acked:[event_id...]}`.
`seen` may be empty; otherwise retain its normalized duplicate/conflict semantics.
Preserve existing captures/refunds and acknowledgments;
drain must not recapture them. Their order line snapshot may be initially unknown.
When a later order event arrives, bind that snapshot and require the same amount.

## Reporting root: late joins, legacy receipts and revenue

`handle(event)` accepts all four wire kinds in both versions, durably deduplicates,
and validates agreement as above. Payment events can precede any order event.
`receipt(order_id)` returns None until an order snapshot (placed or cancelled) is
known; afterward it returns `{schema:2, order_id, lines, total_minor, paid_minor,
status}`. `paid_minor` is captured amount, or zero after a refund/no capture.
Status precedence is `refunded`, then `cancelled`, then `paid`, then `placed`.
A cancellation before its refund therefore shows `cancelled` but still paid funds.
Once a refund is known, a delayed capture never revives revenue or paid status.

`revenue()` sums paid_minor for receipts with known order snapshots; payment-only
records are excluded until the order arrives. `legacy_receipt(order_id)` returns
None for an unknown snapshot, otherwise `"<order_id>: $<total with 2 decimals> (<status>)"`.
This adapter formats the original order total, not outstanding balance/current price.

Legacy reporting file:
`{version:1, receipts:{key:{order_id, items:[legacy order-item...], total:<dollars>,
paid:<dollars>, status:"placed"|"paid"|"cancelled"|"refunded"}},
seen:{event_id:<original v1 order or payment event>}}`.
`seen` may be empty; preserve normalized duplicate/conflict semantics when populated.
Preserve old receipt state and migrate money. A late duplicate capture cannot revive
a migrated refunded receipt. Internal v2 join/deduplication layout is your choice.
Historical paid amounts are zero or the full recorded total, not partial payments.
Zero-priced paid orders remain `paid`; zero is not evidence that no capture occurred.

## Acceptance and scope

Canonical boundaries, also in architecture.json with the same information for all:

- catalog: `contracts/catalog-quote`, `contracts/inventory-reservation`
- orders: `contracts/catalog-quote`, `contracts/inventory-reservation`, `contracts/order-state`
- settlement: `contracts/order-state`, `contracts/settlement-event`
- reporting: `contracts/order-state`, `contracts/settlement-event`, `contracts/legacy-receipt`

These labels describe shared APIs, not a coordination sequence. Each component
also owns its own store's migration and restart behavior.

Implement only your assigned component root(s); all component contracts are visible.
You may add focused tests inside those roots. Preserve existing legacy tests.
Do not modify this objective, supplied role tasks, or the acceptance checker.
The solo task owns all four roots with identical functional requirements.

The public checker covers unit rounding/legacy reads, reservation atomicity/retries,
order recovery, durable outboxes, four-store migration, delayed settlement,
cancellation reorder, reporting late joins, mixed-version events, validation without
partial mutation, a replayed multi-order product workflow, and legacy workflow.
Tests use fresh temporary state and changed data, not only the example SKU/amount.
Component-local tests and integrated acceptance are reported separately. A passing
focused test is not a claim that another component accepts the changed contract.
The overall accepted flag requires every contract group and each component's
nonempty focused test suite to pass. Ordinary contract failures still produce a
complete JSON result and checker exit 0; checker infrastructure failure is distinct.
Each component-local test process has a five-second limit. Exceeding it fails that
component check, not checker infrastructure, and later component checks still run.

Acceptance measures functional integration, including logical all-or-nothing
validation and restart behavior. Same-directory temporary-file atomic replacement
remains an implementation requirement, but this checker does not verify that write
mechanism or certify filesystem atomicity or power-loss durability. A passing
functional result alone is not evidence of those properties; no particular Python
replacement API is prescribed by the checker.

## Candidate2 extension: durable partial returns

This extends the preceding v1 migration. Its twelve acceptance groups and all
original no-return behavior remain required. Both sections are one objective.
No replacements, shipping service, taxes, discounts, or refund-provider calls are
part of this task. Calls are sequential; event delivery may be delayed, duplicated
or reordered. Development can be concurrent. Nothing prescribes worker waiting,
messages, repair ownership, or an implementation sequence.

## Public business contract

All new arguments work by keyword with exactly the names below. JSON values must
be detached. Existing identifier, basket, integer and error rules still apply.
A return ID is scoped to its order/reservation, not globally unique.
Canonical basket identity coalesces repeated SKUs; retry order does not matter.

Catalog adds `restore(reservation_id, return_id, items)`. A new valid return adds
these quantities to available stock exactly once and remembers its original
receipt durably. Every SKU must belong to the original hold; the cumulative
returned quantity per SKU must not exceed the held quantity. Validate the entire
basket before changing anything. Identical retries return the identical JSON
receipt, even after release; a different basket with the same ID raises ValueError.
New returns against a released hold raise ValueError. Unknown holds also raise.
The original reserve receipt stays unchanged. Catalog.release now restores ONLY
the not-yet-returned quantities, then retires the hold exactly as before.

Orders adds `return_items(order_id, return_id, items, fail_after_restore=False)`,
returning return_id. It calls Catalog.restore for the same IDs and basket, consumes
the documented Catalog JSON receipt, and persists one return record and one new
order-return event. `returns(order_id)` returns records sorted by return_id:
`{return_id, items:[{sku,quantity}...], refund_minor}`. An unknown order raises
ValueError; a known order without returns yields []. Do not change get/legacy
shapes, original order snapshots, or the placed/cancelled statuses they expose.

The explicit fault raises RuntimeError after Catalog's restore is durable but
BEFORE Orders' return record/event is durable. Reopen and retry to finish without
restoring stock twice. The fault does not fire on an already journaled identical
retry. No additional crash window or cross-file transaction is required. Multiple
unfinished returns can be retried by their IDs; Catalog's retained receipts are
authoritative for their individual credit allocation.

Cancellation is allowed after partial or full returns, or after the injected
unjournaled restoration. It restores only remaining stock and cancels the whole
order. Once cancelled, new returns are rejected; already journaled identical
return retries remain successful, including fail_after_restore=True. An
unjournaled interrupted return need not be journaled after cancellation and its
retry is rejected. Existing journaled returns and their pending events survive
cancellation. Identical place/cancel retries retain the old behavior.

## Snapshot money and financial effects

For ordinary new orders, a returned unit credits its ORIGINAL rounded unit price,
never a current quote. More than one return may accumulate against the same SKU.
For historical totals that differ from rounded line sums, define cumulative
credit as min(original recorded total, sum of returned quantities * original
rounded unit prices), except returning ALL held units credits the full recorded
total. Each return's refund_minor is the increase in cumulative credit at the
moment Catalog accepts that return. This avoids both over-refunding a historical
total and leaving historical rounding residue after full return. Receipts retain
their individual allocations across restart and changed prices.

Settlement accepts actual new order-return events in addition to old order
events. Return notifications do not trigger capture. They can precede placement
or arrive in any order, including after cancellation. Keep independent durable
return identities; duplicate delivery is not a second entitlement.
Without cancellation, drain still captures the ORIGINAL recorded order amount
once and then refunds all known returns. If already captured, handling a new
return refunds it without another drain. Return credits received before capture
are pending until capture. A zero-cent return is still a completed operation.

Cancellation before capture prevents both capture and monetary refund. After
capture, cancellation makes total refunded equal the original recorded amount,
not original amount PLUS prior return refunds. Previously emitted partial-refund
events remain stable and acknowledgeable. Later returns, captures or replay
cannot revive a cancelled payment or exceed the original total refund.
balance() is original captured money minus cumulative refunded money.
No-return payment events and their full-cancellation meanings remain unchanged.

Reporting accepts actual new order-return and payment-return-refund events. It
keeps durable return facts separately from confirmed payment/refund facts.
The original order snapshot is still needed before receipt() or the new
`return_summary(order_id)` returns a value. A return event alone does not
establish that original snapshot, even if its payload contains enough prices.

return_summary yields:
`{returned_items:[{sku,quantity}...], refund_due_minor, refunded_minor}`.
returned_items aggregates journaled explicit returns, coalesced and sorted.
refund_due_minor sums their original allocated credits (not cancellation).
refunded_minor is the confirmed cumulative monetary refund, including any full
cancellation refund. Before returns/refunds these are [], 0, 0.

A confirmed payment.return_refund notification establishes that the original
capture occurred, even when its separate payment.captured notification is delayed.
Reporting may infer the original captured amount from this evidence; it must
still wait for the original order snapshot before exposing a receipt/revenue.
Zero-cent return-refund notifications are real completed financial operations,
not absence of payment evidence.

receipt retains its exact fields and original total/lines. paid_minor is the
confirmed captured amount less confirmed refunds. Payment-only records do not
contribute revenue before the original order snapshot is known. For return flows,
status precedence is: fully refunded, cancelled, partially_refunded, paid, placed.
partially_refunded requires a positive confirmed refund smaller than the total.
A confirmed return refund equal to a zero order total counts as refunded too.
Return intent alone does not change paid/status. legacy_receipt still formats the
ORIGINAL total and current status. Late smaller refunds/captures cannot regress
cumulative refunded money. Return/payment events may precede order events; joins
must survive restart and independent outbox acknowledgments.

## Producer-owned representations, not shared parser code

Fixed external APIs and business outputs above are the oracle. New internal
payload field names, nesting, delta/cumulative encoding and bookkeeping layouts
are NOT predefined. Producers must document their actual emitted JSON contracts
in their own root's CONTRACT.md; consumers integrate those actual contracts.
Catalog owns restore receipts; Orders owns return notifications; Settlement owns
return-refund payment notifications. Reporting documents the contracts it consumes.
Document identity/correlation, monetary meaning, replay and version behavior.
These documents are normal equally visible source in every treatment.

Only the new event ENVELOPE is fixed for routing and acknowledgments:
{schema:3, event_id:<nonempty opaque stable string>, order_id, revision:3,
kind:"order.returned"|"payment.return_refund", ...producer-defined payload...}.
All event IDs must be unique within their producer outbox, including old events.
Bodies remain identical across delivery, retry and restart. Order return events
identify distinct completed business returns. Payment events must convey enough
information to reconcile refunds under reordering; their representation is the
producer's choice. events() sorts by (order_id, revision, event_id); old no-return
ordering is unchanged. ack applies to old and new events. Invalid/conflicting
same-ID redelivery must not change state. Unsupported schemas/kinds remain errors.

Consumers exchange JSON-round-tripped values; they must not inspect another
component's state file or import its parser/helper functions. Normal Orders ->
Catalog public method calls remain allowed. Keep each component independently
importable. Legacy consumers here means existing public entry points and readers
of OLD events keep working; an unmodified legacy binary is not required to
understand the newly introduced event kinds. Preserve version-1 migration and
reopen your own no-return version-2 state with absent return fields treated as
empty; existing captures/holds/seen history/acknowledgments must survive.

## Acceptance and boundaries

New shared boundary contracts/partial-returns applies to all four roles, in
addition to the unchanged v1 boundary map. Source-root ownership remains the same.
Keep the supplied starting legacy modules and old focused tests as your baseline;
implement the migration and this extension, not a separate alternate product.

The three new public acceptance groups exercise inventory/retry recovery,
delayed cumulative settlement/reporting, and cancellation/legacy migration.
They pass ACTUAL producer JSON through actual consumers and use input-derived
stock/money expectations. They do not inspect new payload layouts or require a
reference encoding. The observer-only reference is never supplied to workers.
The public checker is not a filesystem/power-loss certification; the coverage
limit above still applies.
