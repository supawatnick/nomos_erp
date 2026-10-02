# NOMOS ERP — Project Status & Next Actions

> Operational handoff/source of truth. Read after AGENTS.md before every work session.

## Current stage
Phase 6 — Inventory Operations / Internal ERP MVP

Overall status: **PHASE 6 PASS — INTERNAL INVENTORY ERP MVP COMPLETE — READY FOR PHASE 7**

Primary objective: begin Phase 7 Business Partners & CRM Foundation on host 73 only while preserving the completed Internal Inventory ERP MVP and four-core boundaries.

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
- [x] Phase 5 review — docs/PHASE-5-REVIEW.md.

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
- [x] PostgreSQL and Web acceptance coverage.
- [x] Phase 6 review — docs/PHASE-6-REVIEW.md.
- [x] Internal Inventory ERP MVP scope (Phases 0–6) complete.

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
- Final documentation commit CI and host73 clean-state verification required for terminal closure.

## Phase 5 acceptance evidence
- Host 73 Web lint: PASS before documentation closure.
- API Ruff/mypy/Alembic/PostgreSQL pytest: PASS on Phase 5 implementation gate.
- pip-audit: PASS.
- npm ci/audit high: PASS.
- Web lint/typecheck/tests/production build: PASS on Phase 5 implementation gate.
- gitleaks: PASS.
- Final documentation commit CI and host73 clean-state verification are required for terminal Phase 5 closure.

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
- Final full CI/documentation gate: pending final documentation commit run at time of this status update; Phase 4 closure requires it to be green.
- Host 73 clean-state verification: required after final sync.

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

## Current blockers
- None for Phase 4.
- Platform safety gates may require permitted single-command SSH patterns; this is an execution-tool constraint, not an architecture blocker.

## In progress / not yet passed
- Phase 4 Inventory Engine has not started.
- Two preserved pre-sync stashes remain on host 73 from conflicting local scaffold work; do not drop them until reviewed.

## NEXT ACTIONS — execute in this order

### NEXT 1 — Phase 7 partner identity
Implement tenant-scoped business partner identity with customer/supplier roles, contacts and addresses.

### NEXT 2 — Phase 7 CRM foundation
Implement leads/opportunities, activities/notes and ownership without coupling to future Sales Orders.

### NEXT 3 — Phase 7 acceptance
Verify customer+supplier dual role, tenant isolation, audit, Web workflows and CRM history before Phase 8 Procurement.

## Latest activity
- Phase 3 Catalog and Warehouse implementation completed.
- Phase 3 PostgreSQL/API/Web/security regression gate PASS in GitHub Actions run 36974731001.
- Phase 3 review recorded in docs/PHASE-3-REVIEW.md.
- Four-core ERP plan/framework/skills revision and Phase 0–3 alignment patch completed without invalidating Phase 0–3 acceptance.
- Phase 4 Inventory Engine implemented with concurrency/idempotency/reconciliation acceptance and cross-core source contracts.\n- Phase 5 Inventory Web ERP implemented with operational stock/movement views and idempotent posting workflows.\n- Phase 6 Inventory Operations completed; Internal Inventory ERP MVP (Phases 0–6) is complete.\n- Immediate next executable action is Phase 7 Business Partners & CRM Foundation on host 73.
