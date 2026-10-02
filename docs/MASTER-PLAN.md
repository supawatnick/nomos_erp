# NOMOS ERP Master Development Plan

## Product goal
NOMOS is a commercial multi-tenant Web ERP. Web is the primary product surface. LINE is a later adapter over the same application services.

## Architecture strategy
- Modular monolith first.
- Next.js + TypeScript Web.
- FastAPI + Python API.
- PostgreSQL is the business system of record.
- Redis is optional infrastructure for cache, queues, short-lived coordination, never authoritative business state.
- Inventory uses an immutable posted ledger plus a rebuildable balance projection.
- Modules communicate through explicit application contracts/domain events; no cross-module table mutation.
- All tenant business operations receive trusted tenant/actor/request/channel context.

## Delivery gates

### Phase 0 — Specification and architecture
Deliver: product/domain vocabulary, data model, document lifecycle, authorization model, accounting boundary, module boundaries, engineering rules.
Exit: critical invariants are unambiguous; Inventory, Purchasing and Sales stock effects are defined; schema direction does not block accounting, multi-company, branch, lot/serial or reservations.

### Phase 1 — Engineering foundation
Deliver: Web/API/worker skeleton, configuration, Docker Compose on host 73, PostgreSQL migrations, CI, lint/type/test/build gates, health/readiness.
Exit: clean environment can boot and migrate deterministically; CI is green.

### Phase 2 — SaaS platform core
Deliver: tenant, legal entity/company, branch, users, memberships, sessions, RBAC, audit, idempotency, outbox, settings.
Exit: cross-tenant read/write/reference tests deny access; permissions are server enforced.

### Phase 3 — Catalog and warehouse
Deliver: products, categories, units/conversions, barcodes, warehouses, locations, document numbering.
Exit: tenant-scoped master data works via API and Web with import-safe identifiers and archive lifecycle.

### Phase 4 — Inventory engine
Deliver: receive, issue, transfer, adjust, reversal, ledger, balance projection, concurrency and idempotency.
Exit: ledger reconciles to balances; concurrent issue cannot oversell under default policy; transfers are atomic; posted history is immutable.

### Phase 5 — Inventory Web ERP
Deliver: operational dashboard, stock, receive/issue/transfer/adjust, movements, master-data administration, users/roles/audit.
Exit: complete operator workflow works in Web with Thai/English-ready UI, permission states, validation and error recovery.

### Phase 6 — Inventory operations
Deliver: stock count, reorder rules/low-stock, imports, operational reports and exports.
Exit: opening stock/import/count workflows are traceable and never bypass ledger rules.

### Phase 7 — Business partners
Deliver: customer/supplier views backed by a shared partner identity/address/contact model.
Exit: a partner may safely be customer, supplier or both.

### Phase 8 — Purchasing
Deliver: purchase request, purchase order, goods receipt, purchase return, partial receipts.
Exit: PR/PO never change physical stock; goods receipt/return use Inventory application services and reconcile.

### Phase 9 — Sales
Deliver: quotation, sales order, reservation, delivery, return, partial delivery.
Exit: order/reservation/on-hand/available semantics are explicit and concurrency tested.

### Phase 10 — Approval
Deliver: policy, request, steps, decisions, expiry/cancel/revalidation and separation-of-duties option.
Exit: stale approval cannot execute changed business state.

### Phase 11 — Operational reporting
Deliver: inventory, purchasing, sales reports; CSV/XLSX export; reporting query protections.
Exit: common reports do not require arbitrary SQL or destabilize OLTP workloads.

### Phase 12 — Accounting and costing
Deliver: chart of accounts, journals/GL, AR/AP, invoice/payment, fiscal periods, tax integration and chosen costing methods.
Exit: business documents create balanced, auditable accounting effects through explicit posting rules.

### Phase 13 — LINE
Deliver: tenant LINE config, secure account linking, signed/deduplicated webhook, read queries, confirmation-based inventory mutations.
Exit: Web and LINE execute the same use cases and permissions; retries cannot duplicate stock.

### Phase 14 — Commercial SaaS layer
Deliver: tenant onboarding, plans/subscriptions/entitlements, limits, trial/suspend/cancel/export/retention lifecycle.
Exit: entitlement is separate from RBAC and tenant provisioning is repeatable.

### Phase 15 — Commercial hardening
Deliver: security review, performance/load/concurrency tests, backup/PITR and restore drills, observability/alerts, upgrade/migration runbooks, incident readiness.
Exit: controlled pilot SLA/RPO/RTO and restore targets are demonstrated, not merely documented.

## Release milestones
- Internal Inventory MVP: phases 0–6.
- Web ERP V1: phases 0–11.
- Integrated ERP V1: phases 0–13.
- Commercial pilot: phases 0–15.
- GA only after pilot feedback and remediation.

## Rules for sequencing
A phase is gate-based, not calendar-based. A later phase may be designed early but must not bypass failed security, tenant, data-integrity or inventory gates.

## Definition of Done
Every feature includes domain behavior, migration when needed, tenant isolation, authorization, API contract, Web UX when applicable, validation/error handling, audit, tests, docs and operational telemetry. Stock-changing features additionally require transactionality, idempotency, concurrency tests and reconciliation coverage.
