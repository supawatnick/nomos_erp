# Sales & CRM Module

Sales & CRM is one of NOMOS ERP's four first-class core modules. It owns customer-facing commercial intent and traceability from lead through quotation and order fulfillment.

## Scope
- leads and opportunities
- customer/partner relationship view
- contacts, activities, notes and owner/assignee
- quotations (QT) and quotation lines
- quotation revision/version history
- sales orders and lines
- reservations
- deliveries/returns
- sales recording and order-status tracking
- source linkage into customer invoice/AR in Finance

## Lifecycle

Lead/Opportunity:
OPEN -> QUALIFIED -> WON/LOST/CANCELLED

Quotation:
DRAFT -> SENT -> ACCEPTED / REJECTED / EXPIRED / CANCELLED

A material edit after SENT creates a new revision or returns through an explicit audited transition. Acceptance records who/when/version and preserves the accepted commercial snapshot.

Sales Order:
DRAFT -> CONFIRMED -> RESERVED/PARTIALLY_RESERVED -> PROCESSING -> PARTIALLY_FULFILLED -> FULFILLED -> CLOSED
Exception states: ON_HOLD / CANCELLED.

Delivery:
DRAFT -> POSTED -> REVERSED/RETURNED as applicable.

## QT requirements
- Human QT number uses concurrency-safe document numbering.
- Store quotation validity/expiry, customer, salesperson/owner, currency, price, discount, tax context and terms.
- QT line amounts use exact decimals.
- Revisions remain traceable; accepted revision is immutable as commercial evidence.
- QT acceptance may create/seed an SO with source linkage; it does not post stock or accounting.
- QT list/detail must expose status, validity, customer, owner, total and linked SO.

## Order tracking requirements
Every SO exposes an auditable status timeline and derived operational progress:
- ordered quantity
- reserved quantity
- delivered quantity
- returned quantity
- invoiced quantity/amount when Finance is enabled
- payment state when Finance is enabled
- remaining-to-deliver
- current owner and last meaningful transition

Status is derived/transitioned by domain rules, never manually overwritten merely for display.

## Inventory relationship
- confirmation alone does not reduce on-hand
- reservation reduces available, not on-hand
- delivery invokes Inventory issue
- sales return invokes Inventory receive
- cancellation releases reservation
- partial fulfillment is first-class
- retries are idempotent
- sales code never directly edits inventory balance/ledger

## Finance relationship
- SO/QT do not create GL postings.
- Customer Invoice/credit note/receipt are Finance-owned and reference Sales source documents.
- Delivery may emit costing/COGS posting facts according to configured accounting policy.
- Sales exposes deterministic source facts; Finance owns journal mapping and fiscal controls.
- Financial posting failure must not be hidden by cosmetic Sales status changes.

## Rules
- tenant-scoped lead/customer/QT/SO
- exact decimal prices, discounts, tax bases and amounts
- explicit currency context
- stock availability follows reservation policy
- order changes affecting reservation reconcile atomically
- permission/approval applies to discount, price override, credit exceptions and cancellation when configured
- guessed cross-tenant IDs resolve as not found
- critical transitions create audit evidence and outbox events

## Reporting
Minimum operational views: quotation pipeline, conversion QT->SO, sales by period/customer/product/owner, open orders, partially fulfilled orders, overdue fulfillment, delivery progress and later invoice/payment status.

## Acceptance
Tests cover QT revision/expiry/acceptance, QT->SO traceability, partial reservation/delivery, cancellation/release, cross-tenant references, concurrency, idempotent delivery, order-status timeline and Sales-to-Inventory/Finance contract boundaries.
