# NOMOS ERP — Project Status & Next Actions

> Operational handoff/source of truth. Read after AGENTS.md before every work session.

## Current stage
Phase 3 — Catalog and Warehouse

Overall status: **PHASE 3 PASS — READY FOR PHASE 4**

Primary objective: begin Phase 4 Inventory Engine on host 73 only while preserving Phase 0–3 tenant, security, catalog and organization invariants.

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

## Current blockers
- None for Phase 4.
- Platform safety gates may require permitted single-command SSH patterns; this is an execution-tool constraint, not an architecture blocker.

## In progress / not yet passed
- Phase 4 Inventory Engine has not started.
- Two preserved pre-sync stashes remain on host 73 from conflicting local scaffold work; do not drop them until reviewed.

## NEXT ACTIONS — execute in this order

### NEXT 1 — Phase 4 inventory persistence
Implement inventory transactions/lines/balances and required constraints/indexes using the approved ledger contract.

### NEXT 2 — Phase 4 posting engine
Implement receive/issue/transfer/adjust/reversal/opening through one application posting layer with aggregate-before-lock, deterministic locks, no-negative-stock and immutable POSTED history.

### NEXT 3 — Phase 4 concurrency/reconciliation acceptance
Implement idempotency replay/conflict/concurrent-key tests, concurrent issue/no-oversell, atomic transfer, reversal linkage, ledger-to-balance reconciliation and correlated audit/outbox gates.

## Latest activity
- Phase 3 Catalog and Warehouse implementation completed.
- Phase 3 PostgreSQL/API/Web/security regression gate PASS in GitHub Actions run 36974731001.
- Phase 3 review recorded in docs/PHASE-3-REVIEW.md.
- Immediate next executable action: Phase 4 inventory persistence on host 73.
