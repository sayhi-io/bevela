# Catalog restore receipt

restore returns {hold: reservation_id, ticket: return_id, items: canonical basket,
credit: this return's incremental cents, original: original hold total in cents}.
The stable ticket is scoped to hold. The receipt is immutable and identical on
retry, including after release; credit is allocated when restoration is accepted.
All values are JSON. Consumers use these fields, never Catalog state or helpers.
