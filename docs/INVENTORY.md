# Inventory Domain

## MVP capabilities
- SKU/product master
- Multi-warehouse and bin/location
- Receive
- Issue
- Transfer
- Adjustment
- Current availability
- Movement history
- Reorder level / low stock

## Ledger rule
Never implement an unexplained `UPDATE stock = ...` as the source of truth. Each change must have a transaction, lines, actor, timestamp, tenant, reason/reference, and audit trail.

## Invariants
- Quantity must satisfy configured precision and validation.
- Product/location must belong to the same tenant.
- Transfers cannot accidentally duplicate stock.
- Idempotency protects retried API/LINE requests.
- Negative stock policy is tenant-configurable; default MVP behavior should reject insufficient stock.
- Posted inventory transactions are not silently edited; correction uses reversal/adjustment.

## Future
Reservations, lot/serial tracking, expiry, costing methods, cycle count and barcode workflows.
