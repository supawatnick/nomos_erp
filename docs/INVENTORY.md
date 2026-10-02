# Inventory Domain

## MVP capabilities

- Product/SKU master
- Category and unit
- Multiple warehouses
- Warehouse locations/bins
- Receive
- Issue
- Transfer
- Adjustment
- Current on-hand balance
- Movement history
- Reorder level / low-stock
- Reversal/correction flow

## Ledger rule

Never implement an unexplained UPDATE stock = ... as the source of truth. Every stock change has:
- a business transaction
- one or more lines
- tenant
- actor
- channel
- timestamp
- reason/reference
- idempotency/request metadata
- audit trail

## Transaction states

Use explicit states when workflow needs them:
- DRAFT
- PENDING_CONFIRMATION where channel workflow requires it
- PENDING_APPROVAL
- POSTED
- REJECTED
- CANCELLED

Only POSTED entries affect stock.

## Invariants

- Quantity is positive on command input; direction is represented by transaction semantics.
- Quantity conforms to unit precision.
- Product, unit, warehouse and location belong to the same tenant.
- Source and destination of a transfer are distinct valid stock locations.
- A transfer posts source decrease + destination increase atomically.
- Retry with the same idempotency key does not duplicate movement.
- Negative stock is rejected by default.
- Posted movements are not edited/deleted in normal operation.
- Correction uses reversal or compensating adjustment with a reason.
- Permission and approval policy are evaluated before posting.

## Availability

MVP distinguishes:
- on_hand: posted physical ledger balance
- available: on_hand initially, unless reservations are later introduced

When reservations arrive:
available = on_hand - reserved according to documented reservation rules.

## Receive

Required: destination, product/quantity lines, reference/reason. Optional: supplier, purchase order, unit cost when purchasing/costing is enabled.

## Issue

Required: source, product/quantity lines, reason/reference. Validate sufficient stock within the posting transaction.

## Transfer

Required: source and destination locations plus lines. Lock balance rows in deterministic order to reduce deadlock risk.

## Adjustment

Adjustment requires a reason code/comment and stronger permission than routine receive/issue when configured. Large adjustments may require approval.

## Reversal

A reversal references the original posted transaction and creates opposite ledger effect. It does not erase the original audit history.

## Low stock

Reorder rules are tenant/product/warehouse scoped as configured. Alert generation must be duplicate-safe and avoid notification storms.

## Future dimensions

- reservations
- lot/batch
- serial number
- expiry
- cycle count
- barcode scanning
- costing methods
- inventory valuation