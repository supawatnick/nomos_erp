# NOMOS ERP Master Development Plan

## Product goal
NOMOS is a commercial multi-tenant Web ERP built around four first-class business cores:

1. **Finance & Accounting**
2. **Inventory & Warehouse**
3. **Procurement & Purchasing**
4. **Sales & CRM**

Web is the primary product surface. LINE is a later adapter over the same application services. A release is not a complete ERP merely because inventory works; the four cores must integrate through explicit business contracts.

## Core business flow
- Lead/Customer -> Quotation (QT) -> Sales Order -> Reservation -> Delivery -> Customer Invoice -> AR -> Receipt.
- Supplier -> Purchase Request/RFQ -> Purchase Order -> Goods Receipt -> Supplier Invoice -> AP -> Payment.
- Inventory owns physical quantity and movement.
- Accounting owns financial truth and posting.
- Sales and Purchasing own commercial intent/documents and invoke Inventory/Accounting contracts; they never mutate those modules' tables directly.

## Architecture strategy
- Modular monolith first; four core modules have explicit ownership and application contracts.
- Next.js + TypeScript Web.
- FastAPI + Python API.
- PostgreSQL is the business system of record.
- Redis is optional infrastructure for cache, queues and short-lived coordination, never authoritative business state.
- Inventory uses an immutable posted ledger plus rebuildable balance projection.
- Accounting uses immutable posted journal entries with balanced debits/credits and auditable reversals.
- Modules communicate through application contracts/domain events; no cross-module table mutation.
- All tenant business operations receive trusted tenant/actor/request/channel context.
- Money and quantity use exact decimals; currency, tax and exchange-rate context are explicit.
- Human document numbers are separate from immutable database IDs.
- Posted effects are immutable; correction uses reversal/credit/debit/adjustment documents as appropriate.

## Delivery gates

### Phase 0 — Specification and architecture
Deliver: product/domain vocabulary, data model, document lifecycle, authorization model, accounting boundary, module boundaries, engineering rules.
Exit: critical invariants are unambiguous and schema direction does not block the four ERP cores.

### Phase 1 — Engineering foundation
Deliver: Web/API/worker skeleton, configuration, Docker Compose on host 73, PostgreSQL migrations, CI, lint/type/test/build gates, health/readiness.
Exit: clean environment can boot and migrate deterministically; CI is green.

### Phase 2 — SaaS platform core
Deliver: tenant, legal entity/company, branch, users, memberships, sessions, RBAC, audit, idempotency, outbox, settings.
Exit: cross-tenant read/write/reference tests deny access; permissions are server enforced.

### Phase 3 — Catalog and warehouse master data
Deliver: products, categories, units/conversions, barcodes, warehouses, locations, document numbering.
Exit: tenant-scoped master data works via API and Web with import-safe identifiers and archive lifecycle.

### Phase 4 — Inventory engine
Deliver: receive, issue, transfer, adjust, reversal, ledger, balance projection, concurrency and idempotency.
Exit: ledger reconciles to balances; concurrent issue cannot oversell under default policy; transfers are atomic; posted history is immutable.

### Phase 5 — Inventory Web ERP
Deliver: operational dashboard, stock, receive/issue/transfer/adjust, movements, master-data administration, users/roles/audit.
Exit: complete operator workflow works in Web with permission states, validation and recovery.

### Phase 6 — Inventory operations
Deliver: stock count, reorder/low-stock, imports, operational reports and exports.
Exit: opening stock/import/count workflows are traceable and never bypass ledger rules.

### Phase 7 — Business partners & CRM foundation
Deliver: shared partner identity, customer/supplier roles, contacts, addresses, CRM leads/opportunities, activities/notes and ownership.
Exit: a partner may safely be customer, supplier or both; lead/customer history is tenant-scoped and auditable.

### Phase 8 — Procurement & Purchasing
Deliver: Purchase Request, RFQ/supplier quotation comparison, Purchase Order, Goods Receipt, Purchase Return, partial receipt, procurement status tracking.
Exit: PR/RFQ/PO never change physical stock; receipt/return invoke Inventory; supplier/order status and remaining quantities reconcile.

### Phase 9 — Sales & CRM
Deliver: lead/customer workflow, **Quotation (QT)**, quotation revision/expiry/acceptance, Sales Order, reservation, delivery, return, partial fulfillment, sales recording and order-status tracking.
Exit: QT -> SO traceability is preserved; sales pipeline/order status is explicit; reservation/on-hand/available semantics are concurrency tested; delivery invokes Inventory.

### Phase 10 — Approval & commercial controls
Deliver: approval policies for purchasing, sales discounts/credit exceptions, inventory adjustments and financial controls; request/steps/decisions/expiry/cancel/revalidation/separation of duties.
Exit: stale approval cannot execute changed business state.

### Phase 11 — Operational reporting
Deliver: inventory, procurement, sales/CRM and management reports; CSV/XLSX export; reporting query protections.
Exit: common operational and pipeline/order-tracking reports do not require arbitrary SQL or destabilize OLTP.

### Phase 12 — Finance & Accounting
Deliver: Chart of Accounts, journals/GL, AR/AP, customer/supplier invoices, receipts/payments, fiscal periods, tax/VAT framework, accounting posting rules, inventory valuation/costing integration and financial statements foundation.
Exit: eligible Inventory/Purchasing/Sales documents create balanced, idempotent and auditable financial effects; subledgers reconcile to GL; closed periods reject posting.

### Phase 13 — LINE
Deliver: tenant LINE config, secure account linking, signed/deduplicated webhook and confirmation-based ERP operations.
Exit: Web and LINE execute the same use cases and permissions; retries cannot duplicate business effects.

### Phase 14 — Commercial SaaS layer
Deliver: onboarding, plans/subscriptions/entitlements, limits, trial/suspend/cancel/export/retention lifecycle.
Exit: entitlement is separate from RBAC and tenant provisioning is repeatable.

### Phase 15 — Commercial hardening
Deliver: security review, performance/load/concurrency tests, backup/PITR/restore drills, observability/alerts, upgrade/migration runbooks, incident readiness and end-to-end four-core reconciliation.
Exit: controlled pilot SLA/RPO/RTO/restore and cross-module reconciliation targets are demonstrated.

## Release milestones
- Internal Inventory MVP: phases 0–6.
- Commercial Operations Beta: phases 0–11 (Inventory + Procurement + Sales/CRM; accounting integration points preserved).
- **Core ERP V1: phases 0–12 — all four core modules operational.**
- Integrated Channel ERP V1: phases 0–13.
- Commercial pilot: phases 0–15.
- GA only after pilot feedback and remediation.

## Cross-module invariants
- QT acceptance may create/seed an SO but never posts inventory or accounting by itself.
- PO approval does not post stock or accounting by itself.
- Goods Receipt/Purchase Return invoke Inventory before procurement completion states advance.
- Sales Delivery/Return invoke Inventory before fulfillment states advance.
- Invoice/payment are Accounting-owned financial documents and do not rewrite physical stock.
- Inventory/Procurement/Sales emit durable idempotent posting facts/contracts for Accounting.
- No module infers critical effects by scraping another module's UI or mutable presentation data.
- Every cross-module reference validates tenant ownership.
- Partial receipt/delivery/invoice/payment is first-class and line-level quantities/amounts reconcile.
- Business document status is an explicit auditable state machine.

## Rules for sequencing
A phase is gate-based, not calendar-based. Later modules may be designed early but may not bypass failed security, tenant, data-integrity, inventory or accounting-boundary gates.

## Definition of Done
Every feature includes domain behavior, migration when needed, tenant isolation, authorization, API contract, Web UX when applicable, validation/error handling, audit, tests, docs and telemetry. Stock-changing features additionally require transactionality, idempotency, concurrency and reconciliation. Financial-posting features additionally require balanced entries, fiscal-period controls, idempotency, reversal/correction semantics and subledger-to-GL reconciliation.
