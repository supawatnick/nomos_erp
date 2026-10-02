# Sales Module

Sales is a post-inventory-MVP module.

## Entities

- customers
- sales_orders
- sales_order_lines
- reservations
- pick/issue references
- deliveries

## Suggested lifecycle

DRAFT -> CONFIRMED -> RESERVED -> PARTIALLY_FULFILLED -> FULFILLED/CANCELLED

The exact states may evolve, but transitions must be explicit and auditable.

## Inventory relationship

Sales fulfillment uses inventory services:
- reservation reduces available stock but not on-hand
- picking/issue posts physical stock movement
- cancellation releases reservation
- retries are idempotent

No sales code directly edits inventory balance.

## Rules

- tenant-scoped customer/order
- exact decimal prices/amounts
- stock availability checked according to reservation policy
- partial fulfillment is explicit
- order changes that affect reservation reconcile atomically
- permission and approval policies apply when configured

## Future

Pricing rules, discounts, tax, invoices, returns, credit control and accounting integration.