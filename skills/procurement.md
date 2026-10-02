# Procurement & Purchasing Skill

Before procurement work read docs/PURCHASING.md, docs/DOCUMENT-LIFECYCLE.md, docs/INVENTORY.md and docs/ACCOUNTING-BOUNDARY.md.

- Procurement is a first-class ERP core.
- Own PR, RFQ, supplier quote comparison, PO and procurement tracking.
- PO approval/sending never changes physical stock.
- Goods Receipt/Return invoke Inventory application contracts; never edit inventory tables.
- Supplier Invoice/AP/payment belong to Finance and reference procurement source documents.
- Partial receipt and remaining-to-receive are first-class line-level facts.
- Material PO changes after approval invalidate/re-enter approval according to policy.
- Use exact Decimal quantity/money and explicit currency/tax context.
- Cross-tenant supplier/product/location/document references must fail.
- Preserve PR/RFQ/PO/Receipt/Invoice traceability.
- Test retries/idempotency, partial receipt, status reconciliation and approval invalidation.
