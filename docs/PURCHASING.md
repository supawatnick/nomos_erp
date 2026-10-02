# Purchasing Module

Purchasing is a post-inventory-MVP module and must reuse inventory receiving rather than creating a second stock logic path.

## Entities

- suppliers
- purchase_requests
- purchase_request_lines
- purchase_orders
- purchase_order_lines
- goods_receipts / reference to inventory receive transactions

## Suggested lifecycle

Purchase Request:
DRAFT -> PENDING_APPROVAL -> APPROVED/REJECTED -> CONVERTED/CANCELLED

Purchase Order:
DRAFT -> PENDING_APPROVAL -> APPROVED -> SENT -> PARTIALLY_RECEIVED -> RECEIVED/CLOSED/CANCELLED

## Rules

- Tenant-scoped supplier and documents.
- Exact decimal price/tax/amount handling.
- Approval policy may depend on amount.
- Goods receipt posts inventory through the inventory receive use case.
- Partial receipt is supported by quantity tracking.
- PO changes after approval follow policy and audit rules.
- Do not mark a PO received unless corresponding inventory receipt succeeds.

## Future

Supplier returns, landed cost, tax/localization, 3-way matching and accounting integration.