# Reporting return consumers

Locally parses Orders' return_note per its CONTRACT.md; distinct tickets aggregate
units and credit. Locally parses Settlement's refund_position; take maximum
cumulative confirmed refund, while old payment.refunded dominates at full total.
Neither notification alone creates an original order snapshot. No parser imports
or reads from another component's JSON state are used.
