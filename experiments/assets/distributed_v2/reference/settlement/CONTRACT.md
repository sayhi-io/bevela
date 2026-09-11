# Settlement return-refund wire

Consumes Orders' documented return_note. Emits fixed schema-3
payment.return_refund envelopes with refund_position:[original_total_minor,
cumulative_refunded_minor]. This position is recorded once when that return is
refunded; future events do not rewrite it. event_id is
JSON([order_id,"credit",return_id]); revision 3. Readers take the maximum confirmed
cumulative position, not the sum. Positions imply a capture has occurred, even
when its event is delayed. Old payment.refunded means full refund of original
amount and dominates all partial positions. A zero position is a real refund.
