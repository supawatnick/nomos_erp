# Sales & CRM Skill

Before Sales/CRM work read docs/SALES.md, docs/DOCUMENT-LIFECYCLE.md, docs/INVENTORY.md and docs/ACCOUNTING-BOUNDARY.md.

- Sales & CRM is a first-class ERP core.
- Lead/customer -> QT -> SO -> reservation -> delivery -> invoice/AR is the canonical flow.
- QT is mandatory: number, revision, validity/expiry, customer, owner, exact totals and acceptance evidence.
- Preserve accepted QT revision and QT->SO source linkage.
- QT/SO confirmation never directly changes on-hand stock.
- Reservation changes available stock; Delivery invokes Inventory issue; Return invokes Inventory receive.
- Customer Invoice/receipt belong to Finance; Sales references their state, never owns journal rows.
- Order tracking must reconcile ordered/reserved/delivered/returned/invoiced/paid progress.
- Status is a domain state machine, not a manually editable UI label.
- Use exact Decimal money/quantity and explicit currency/tax context.
- Cross-tenant IDs must fail without existence leakage.
- Test QT revisions/expiry/acceptance, partial fulfillment, cancellation/release, concurrency, idempotency and cross-core linkage.
