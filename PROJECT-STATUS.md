# NOMOS ERP — Project Status & Next Actions

> Operational handoff/source of truth. Read after AGENTS.md before every work session.

## Current stage
Phase 11 Operational Reporting Closure

Overall status: **PHASE 11 PASS — READY FOR PHASE 12**

Primary objective: begin Phase 12 Finance & Accounting from the clean Phase 11 baseline on host 73 only.

## Completed

### Phase 0 — Specification and Architecture
- [x] Architecture/domain/ERD/authorization/inventory/API/Web contracts locked.

### Phase 1 — Engineering Foundation
- [x] Next.js Web, FastAPI API, worker, PostgreSQL 17, Alembic, configuration, logging, health/readiness and CI foundation.
- [x] Phase 1 acceptance PASS.

### Phase 2 — SaaS Platform Core
- [x] Tenant/organization/user/membership/session/RBAC persistence.
- [x] Server-derived tenant context and deny-by-default permissions.
- [x] Audit, idempotency and transactional outbox foundations.
- [x] Tenant-isolation/RBAC acceptance PASS.
- [x] Phase 2 review — docs/PHASE-2-REVIEW.md.

### Phase 3 — Catalog and Warehouse
- [x] Categories with same-tenant hierarchy and archive lifecycle.
- [x] Units with precision constraints.
- [x] Products with tenant-unique SKU, product type, tracking type, category/base-unit ownership and archive lifecycle.
- [x] Product-unit exact NUMERIC(24,8) conversions and positive-factor validation.
- [x] Tenant-unique barcodes with optional product-unit binding.
- [x] Warehouses with DB-enforced tenant/legal-entity/branch consistency.
- [x] Locations with same-warehouse parent FK and application cycle validation.
- [x] Document sequences with NULLS NOT DISTINCT scope uniqueness and FOR UPDATE allocation.
- [x] Phase 3 product.read/product.manage/warehouse.read/warehouse.manage permission seeds.
- [x] Tenant-scoped master-data API for Products, Categories, Units, Warehouses and Locations.
- [x] Product conversion and barcode API.
- [x] Product list search/status filter/allowlisted sort/opaque cursor pagination.
- [x] Web sign-in + Master Data navigation/pages for Products, Categories, Units, Warehouses and Locations.
- [x] Product Web search/filter/sort/pagination and loading/empty/error states.
- [x] Web Phase 3 regression tests.
- [x] Phase 3 review — docs/PHASE-3-REVIEW.md.

### Phase 4 — Inventory Engine
- [x] PostgreSQL inventory_transactions, inventory_transaction_lines and inventory_balances.
- [x] Exact NUMERIC(24,8) ledger/base quantities and non-negative balance projection.
- [x] One posting layer for RECEIVE/ISSUE/TRANSFER/ADJUST/OPENING/REVERSAL.
- [x] Aggregate-before-lock and deterministic product/location balance locking.
- [x] Atomic transfer and default no-negative-stock.
- [x] Immutable POSTED history and linked reversal.
- [x] Idempotency replay/conflict/concurrent-key protection.
- [x] Tenant/product/unit/location/legal-entity validation.
- [x] Correlated audit and transactional outbox.
- [x] Ledger-to-balance reconciliation.
- [x] Stock-bearing warehouse/location archive protection activated.
- [x] Inventory API for posting, reversal, movement history, balances and reconciliation.
- [x] Concurrent issue/no-oversell acceptance.
- [x] Phase 4 review — docs/PHASE-4-REVIEW.md.

### Phase 5 — Inventory Web ERP
- [x] Inventory operational dashboard.
- [x] Stock-on-hand view with product/warehouse/location labels.
- [x] Immutable movement-history view.
- [x] Receive workflow.
- [x] Issue workflow.
- [x] Transfer workflow.
- [x] Adjustment workflow with explicit direction.
- [x] Phase 4 API-only posting; no direct Web balance mutation.
- [x] Idempotency-Key generation and same-key safe retry.
- [x] Loading/empty/login/permission/insufficient-stock/conflict/network/success states.
- [x] Authenticated Authorization + X-Tenant-ID context.
- [x] Web acceptance coverage for routes, headers, posting, error and retry behavior.
- [x] Users/Roles/Audit administration API + Web remediation completed.
- [x] Phase 5 review + remediation addendum — docs/PHASE-5-REVIEW.md.

### Phase 6 — Inventory Operations / Internal ERP MVP
- [x] Stock-count document and immutable system snapshot.
- [x] Physical count entry and variance calculation.
- [x] Controlled count variance posting through Phase 4 ADJUST only.
- [x] Posted count immutability and replay-safe posting.
- [x] Stock-count source provenance, audit and outbox.
- [x] Reorder policies by product/location.
- [x] Low-stock/reorder actionable signals and suggested quantity.
- [x] Procurement boundary preserved: no PR/RFQ/PO created by Inventory.
- [x] Operational inventory summary and CSV export.
- [x] Web operations/count/reorder/report surfaces.
- [x] PRODUCT + OPENING_STOCK staged import/validate/preview/atomic commit remediation.
- [x] Opening Stock permission corrected to inventory.adjust.
- [x] PostgreSQL and Web acceptance coverage.
- [x] Phase 6 review — docs/PHASE-6-REVIEW.md.
- [x] Internal Inventory ERP MVP scope (Phases 0–6) complete after remediation closure.

### Phase 7 — Business Partners & CRM Foundation
- [x] Shared tenant-scoped Business Partner identity.
- [x] Customer-only, supplier-only and dual customer+supplier roles.
- [x] Partner contacts and addresses.
- [x] CRM leads and explicit lifecycle.
- [x] CRM opportunities with exact amount/currency.
- [x] Activities/notes and tenant-user ownership.
- [x] Partner/CRM permissions, tenant isolation and audit.
- [x] No premature QT/SO/PR/RFQ/PO coupling.
- [x] Business Partners and CRM Web surfaces.
- [x] PostgreSQL and Web acceptance.
- [x] Phase 7 review — docs/PHASE-7-REVIEW.md.

## Phase 7 acceptance evidence
- Ruff: PASS.
- mypy: PASS.
- Alembic upgrade through 0007_phase7_crm: PASS.
- PostgreSQL pytest suite: PASS.
- Partner dual-role/contact/address acceptance: PASS.
- Cross-tenant partner child rejection: PASS.
- Lead/opportunity/activity acceptance: PASS.
- Phase 7 commercial-document boundary acceptance: PASS.
- pip-audit: PASS.
- npm ci/audit high: PASS.
- Web lint/typecheck/tests/build: PASS.
- gitleaks: PASS.
- Terminal Phase 7 evidence superseded by Phase 0–7 remediation acceptance and final documentation CI.

## Phase 6 acceptance evidence
- API Ruff: PASS.
- API mypy strict: PASS.
- Alembic upgrade through 0006_phase6_inventory_operations: PASS.
- PostgreSQL suite: PASS, including stock-count/reorder acceptance.
- Count snapshot/variance/ADJUST provenance/reconciliation: PASS.
- Posted-count immutability and replay-safe posting: PASS.
- Reorder signal and Procurement-boundary acceptance: PASS.
- Cross-tenant reorder rejection: PASS.
- pip-audit: PASS.
- npm ci/audit high: PASS.
- Web lint/typecheck/tests/build: PASS.
- gitleaks: PASS.
- Phase 6 closure reconciled by docs/PHASE-0-7-REMEDIATION.md and remediation CI.

## Phase 5 acceptance evidence
- Host 73 Web lint: PASS before documentation closure.
- API Ruff/mypy/Alembic/PostgreSQL pytest: PASS on Phase 5 implementation gate.
- pip-audit: PASS.
- npm ci/audit high: PASS.
- Web lint/typecheck/tests/production build: PASS on Phase 5 implementation gate.
- gitleaks: PASS.
- Phase 5 closure reconciled by docs/PHASE-0-7-REMEDIATION.md and remediation CI.

## Phase 4 acceptance evidence
- API Ruff: PASS.
- API mypy strict: PASS.
- PostgreSQL Alembic upgrade through 0005_phase4_inventory_engine: PASS.
- PostgreSQL suite: PASS, including Phase 4 concurrency/idempotency/reconciliation acceptance.
- Receive/Issue/Transfer/Adjust/Opening/Reversal: PASS.
- Idempotency replay/conflict/concurrent-key: PASS.
- Concurrent issue/no oversell: PASS.
- Atomic transfer/no-negative-stock: PASS.
- Reversal linkage and ledger-to-balance reconciliation: PASS.
- Cross-tenant location rejection: PASS.
- Audit/outbox and stock-bearing archive guard: PASS.
- Phase 4 closure was superseded and revalidated by the Phase 0–7 remediation acceptance and subsequent green CI gates.
- Host 73 runtime baseline was reverified on 2026-10-02 during the Phase 0–8 repository audit.

## Phase 3 acceptance evidence
- API Ruff: PASS.
- API mypy strict: PASS.
- PostgreSQL Alembic upgrade through 0004_phase3_catalog_warehouse: PASS.
- Unit + PostgreSQL integration suite: PASS.
- Duplicate SKU/barcode constraints: PASS.
- Cross-tenant catalog isolation: PASS.
- Exact conversion validation: PASS.
- Warehouse branch/legal-entity mismatch rejection at DB boundary: PASS.
- Cross-warehouse location parent rejection and hierarchy cycle rejection: PASS.
- Document sequence allocation/increment: PASS.
- Stable product ID/archive semantics: PASS.
- Python dependency audit: PASS.
- Web lint/typecheck: PASS.
- Web tests: PASS — 2 Phase 3 tests.
- Web production build: PASS — routes /login, /products, /categories, /units, /warehouses, /locations.
- npm dependency audit: PASS.
- gitleaks: PASS.
- GitHub Actions code gate: PASS — run 36974731001 on commit 2900c66a657ca4c4662d4ca18804349d3390bd39.

## Decisions passed / locked
- Security and tenant isolation remain highest priority.
- Product master remains tenant-scoped across legal entities in Phase 1–6.
- Unit conversion factors use exact decimal semantics.
- Warehouse branch/legal-entity consistency is a database invariant.
- Location hierarchy cannot cross warehouse boundaries; cycles are rejected.
- Master data uses archive semantics and stable UUIDs for import safety.
- Human document numbering uses transactional sequence allocation and is separate from database IDs.
- Stock-bearing warehouse/location archive enforcement becomes active with Phase 4 inventory state; Phase 3 has no stock ledger/balance state.
- Host 72 remains control/orchestration only; NOMOS runtime/build/test/database execution remains on host 73.

## Planning revision after Phase 3
- [x] Four first-class ERP cores locked in MASTER-PLAN/ROADMAP/MODULES/ARCHITECTURE.
- [x] Sales expanded to Sales & CRM with mandatory QT, revision/acceptance and order-status tracking.
- [x] Procurement expanded with RFQ/supplier comparison and procurement status tracking.
- [x] Finance & Accounting promoted from future boundary to required Core ERP V1 module.
- [x] Cross-core flows locked: QT->SO->Inventory->Invoice/AR->Receipt and PR/RFQ->PO->Inventory Receipt->Invoice/AP->Payment.
- [x] Added skills/finance.md, skills/procurement.md and skills/sales-crm.md; updated product/skills index.
- [x] Core ERP V1 release gate moved to Phase 12 where all four cores are operational.
- [x] Phase 0–3 alignment patch completed: data/ERD, document lifecycle, authorization namespaces, API/audit and numbering contracts now preserve the four-core design.
- [x] Alignment review — docs/PHASE-0-3-ALIGNMENT.md.

## Phase 0–7 remediation closure
- [x] R-01 Users/Roles/Audit Web/API gap closed.
- [x] R-02 PRODUCT/OPENING_STOCK import lifecycle gap closed.
- [x] R-03 stale project/phase status reconciled.
- [x] R-04 remediation Web surfaces checked against WEB-DESIGN-CONTRACT.
- [x] Implementation acceptance CI 36986274423 PASS (47 PostgreSQL/API tests plus full Web/security/dependency gate).
- [x] Documentation reconciliation CI 36986587027 PASS.
- [x] Latest remediation permission-description migration CI 36986937445 PASS on c32a0e234cf31540e0c0275d25f93c90479b35ab.

## Phase 10 — Approval & Commercial Controls
- [x] Tenant-scoped approval policy/request/decision persistence.
- [x] Ordered policy steps with step-specific permissions.
- [x] Immutable snapshot + source version/fingerprint binding.
- [x] SoD/self-approval prohibition, expiry, cancel and tenant isolation.
- [x] Idempotent decisions and explicit APPROVED vs EXECUTED states.
- [x] Stale source version/fingerprint cannot execute.
- [x] Purchasing controlled approval integration; approval never replaces module permission.
- [x] Sales exception, inventory adjustment and future financial-control policy types supported by the shared engine.
- [x] Approval API and Web inbox.
- [x] Phase 10 implementation CI 37005603584 PASS.
- [x] Detailed review: docs/PHASE-10-REVIEW.md.

## Phase 11 — Operational Reporting
- [x] Allowlisted tenant-scoped Inventory, Procurement, Sales/CRM and management reports.
- [x] No arbitrary SQL or client-provided query fragments.
- [x] 366-day maximum date range and 2,000-row hard limit.
- [x] Server-side CSV/XLSX export from the same bounded report definitions.
- [x] Spreadsheet formula-injection protection.
- [x] report.read + report.export authorization boundary.
- [x] Operational Reports Web workspace.
- [x] PostgreSQL reporting acceptance; 70 total tests at implementation gate.
- [x] Phase 11 implementation CI 37007447637 PASS.
- [x] Detailed review: docs/PHASE-11-REVIEW.md.

## Current blockers
- No Phase 11 functional blocker remains.
- Historical host 73 stashes remain preserved housekeeping only.

## NEXT ACTIONS — execute in this order

### NEXT 1 — Phase 12 contract read
Read Finance/Accounting, accounting-boundary, authorization, document lifecycle and posting contracts; verify final Phase 11 documentation CI and host 73 clean sync.

### NEXT 2 — Finance foundation
Implement legal-entity-scoped Chart of Accounts, fiscal periods, journals/GL and balanced posting/reversal with idempotent source posting.

### NEXT 3 — AR/AP and cross-core accounting
Implement customer/supplier invoices, receipts/payments, tax/exchange-rate foundations and Inventory/Procurement/Sales posting contracts with subledger-to-GL reconciliation.

