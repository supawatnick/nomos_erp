# Four-Core ERP Framework Revision

Date: 2026-10-02
Status: **APPROVED / ACTIVE**
Applied after Phase 3 and before Phase 4.

## Decision
NOMOS ERP has four mandatory first-class business cores:
1. Finance & Accounting
2. Inventory & Warehouse
3. Procurement & Purchasing
4. Sales & CRM

This revision does not invalidate Phase 0–3. Existing tenancy, organization, RBAC/audit and catalog/warehouse foundations remain valid. The revision strengthens future module contracts before transactional ERP phases begin.

## Product changes
- Sales is expanded to Sales & CRM.
- Quotation (QT) is mandatory, including numbering, revision, validity/expiry, acceptance evidence and QT->SO traceability.
- Sales Order tracking must expose ordered/reserved/delivered/returned/invoiced/paid progress.
- CRM foundation includes lead/opportunity, activities/notes and ownership.
- Procurement includes PR, RFQ, supplier quotation comparison, PO, receipt/return and order tracking.
- Finance & Accounting is mandatory for Core ERP V1, not optional future scope.
- Finance includes GL, AR/AP, invoices, receipt/payment, fiscal controls, tax framework, valuation/costing integration and reconciliation.

## Framework changes
- Four cores have explicit ownership and cannot mutate one another's persistence directly.
- Canonical sales flow: Lead/Customer -> QT -> SO -> Reservation -> Delivery -> Customer Invoice -> AR -> Receipt.
- Canonical procurement flow: Supplier -> PR/RFQ -> PO -> Goods Receipt -> Supplier Invoice -> AP -> Payment.
- Inventory remains physical quantity authority.
- Finance remains financial posting authority.
- Cross-core integration uses application contracts or durable idempotent posting facts/outbox.
- Exact decimals, explicit currency/unit context, tenant/legal-entity validation and source provenance are mandatory.
- Posted inventory/journal effects are immutable and corrected by explicit reversal/correction.

## Skill changes
Added:
- skills/finance.md
- skills/procurement.md
- skills/sales-crm.md

Updated:
- skills/README.md
- skills/product.md

Agents/contributors touching cross-core workflows must read all affected core skills.

## Roadmap changes
Phase 7: Business partners & CRM foundation.
Phase 8: Procurement & Purchasing.
Phase 9: Sales & CRM including QT and order tracking.
Phase 10: Approval & commercial controls.
Phase 11: Operational reporting across Inventory/Procurement/Sales/CRM.
Phase 12: Finance & Accounting.

Release terminology:
- Phase 0–6: Internal Inventory MVP.
- Phase 0–11: Commercial Operations Beta.
- Phase 0–12: **Core ERP V1** with all four mandatory cores.
- Phase 0–13: Integrated Channel ERP V1.
- Phase 0–15: Commercial Pilot.

## Phase 4 implications
Phase 4 scope remains Inventory Engine, but it must expose clean contracts/events for later Sales delivery/return, Procurement receipt/return and Finance valuation posting. No Phase 4 shortcut may couple inventory posting to future Sales/Procurement/Finance tables.

## Documentation updated
- docs/MASTER-PLAN.md
- docs/ROADMAP.md
- docs/MODULES.md
- docs/ARCHITECTURE.md
- docs/SALES.md
- docs/PURCHASING.md
- docs/ACCOUNTING-BOUNDARY.md
- skills/README.md
- skills/product.md
- PROJECT-STATUS.md

## Acceptance
This planning revision is complete when documentation is internally consistent, repository gates remain green, host 73 is synchronized/clean and Phase 4 remains the next executable phase.
