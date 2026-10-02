# Procurement & Purchasing Module

Procurement & Purchasing is one of NOMOS ERP's four first-class core modules. It owns supplier sourcing and purchase intent; Inventory owns physical receipt/return and Finance owns AP/payment.

## Scope
- supplier/partner view
- purchase requests (PR)
- requests for quotation (RFQ)
- supplier quotation responses/comparison
- purchase orders (PO)
- goods receipt/return orchestration
- partial receipts
- procurement/order status tracking
- source linkage into supplier invoice/AP in Finance

## Lifecycle
PR: DRAFT -> PENDING_APPROVAL -> APPROVED / REJECTED -> SOURCING / CONVERTED / CANCELLED
RFQ: DRAFT -> SENT -> RESPONSES_RECEIVED -> AWARDED / CLOSED / CANCELLED
PO: DRAFT -> PENDING_APPROVAL -> APPROVED -> SENT -> PARTIALLY_RECEIVED -> RECEIVED -> CLOSED
Exception states: ON_HOLD / CANCELLED.
Goods Receipt: DRAFT -> POSTED -> REVERSED when correction is required.

## Rules
- Tenant-scoped supplier and documents.
- Exact decimal quantity/price/discount/tax/amount handling with currency context.
- RFQ comparison preserves supplier offers and awarded source.
- Approval policy may depend on amount, category, supplier or exception.
- PO approval/sending never changes physical stock.
- Goods Receipt invokes Inventory receive; Purchase Return invokes Inventory issue/decrease.
- Do not advance receipt quantities/status unless Inventory posting succeeds.
- Partial receipt and remaining-to-receive are first-class and line-level.
- PO material changes after approval require explicit policy/reapproval.
- Critical transitions are audited and emit outbox facts.
- Cross-tenant supplier/product/location/document references are rejected.

## Order tracking
Expose ordered, received, returned, invoiced and paid progress; remaining-to-receive; expected date; supplier; buyer/owner; last transition; and exception/hold state. Invoice/payment fields become active when Finance is enabled.

## Finance relationship
- Supplier Invoice/debit-credit note/payment are Finance-owned and reference procurement source documents.
- Goods Receipt may emit inventory valuation/accrual facts according to accounting policy.
- 3-way matching (PO/Receipt/Invoice) is a Finance/Procurement integration control, not a reason to duplicate receipt state.

## Acceptance
Tests cover PR/RFQ/PO transitions, partial receipt, duplicate/retry receipt, cross-tenant references, approval invalidation, PO->Inventory linkage, status reconciliation and later PO/Receipt/Invoice matching.
