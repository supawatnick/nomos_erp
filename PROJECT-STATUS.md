# NOMOS ERP — Project Status & Next Actions

> Operational handoff/source of truth. Read after AGENTS.md before every work session.

## Current stage
Phase 9 Sales & CRM Closure

Overall status: **PHASE 9 PASS — READY FOR PHASE 10**

Primary objective: begin Phase 10 Approval & commercial controls from the clean Phase 9 baseline on host 73 only.

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

## Current blockers
- No Phase 0–7 functional blocker remains for Phase 8.
- Two preserved pre-sync stashes on host 73 remain an operational housekeeping item; do not drop them until reviewed.

## Phase 8 — Procurement & Purchasing
- [x] Purchase Request lifecycle with dedicated commands and server-side numbering.
- [x] RFQ supplier invitation, line-level quotation comparison and award.
- [x] Purchase Order lifecycle with approval fingerprint/version and server-side numbering.
- [x] Goods Receipt with partial receipt and atomic Inventory RECEIVE orchestration.
- [x] Purchase Return with cumulative received/returned validation and Inventory ISSUE orchestration.
- [x] Procurement receipt/return idempotency and stock/order reconciliation.
- [x] Procurement Web operations surface.
- [x] Phase 8 review — docs/PHASE-8-REVIEW.md.
- [x] Implementation acceptance CI 36996602994 PASS on 7ddc082348b14f4397559dca2cfed02f6f7f5235.

## Current blockers
- No Phase 8 functional blocker remains.
- Preserved host 73 pre-sync stashes remain housekeeping only; do not apply/drop without review.

## Phase 9 — Sales & CRM
- [x] QT numbering, exact commercial lines, validity/expiry and revision snapshots.
- [x] QT send/revise/accept with accepted revision evidence and QT -> SO traceability.
- [x] Sales Order confirmation without physical stock mutation.
- [x] Reservation/release with on-hand vs available semantics and row-lock concurrency boundary.
- [x] Partial delivery through Inventory ISSUE and sales return through Inventory RECEIVE.
- [x] Idempotent fulfillment and quantity/status reconciliation.
- [x] Order status timeline.
- [x] Sales Web operations surface.
- [x] Phase 9 review — docs/PHASE-9-REVIEW.md.
- [x] Implementation acceptance CI 36998921435 PASS on 65415e9369354c378f359cd40b5b07dc50283302.
- [x] Final closure CI 37000090937 PASS on 9a5872695d492b8c669ddf47957cbeebe85d7bfe; full-history Gitleaks CLI scan PASS.

## Current blockers
- No Phase 9 functional blocker remains.
- Preserved host 73 historical stashes remain housekeeping only; do not apply/drop without review.

## NEXT ACTIONS — execute in this order

### NEXT 1 — Phase 10 contract read and clean-baseline verification
Read approval/commercial-control contracts and verify host 73 is synced to final Phase 9 documentation commit with a clean working tree.

### NEXT 2 — Approval policy and stale-state binding
Implement approval policy/request/step/decision persistence with version/fingerprint revalidation and separation-of-duties boundaries.

### NEXT 3 — Commercial controls integration
Apply approval controls to purchasing, sales discount/credit exceptions, inventory adjustments and later Finance-ready controls without bypassing module permissions.

## Phase 0–8 repository re-audit — 2026-10-02
- [x] Phase 0 architecture review PASS and Phase 0–7 remediation closure PASS.
- [x] Phase 8 Procurement review PASS with CI 36996602994.
- [x] Current main HEAD CI 37000290630 PASS with full-history Gitleaks scan.
- [x] Host 73 main matches origin/main with 0/0 divergence and clean working tree; preserved stashes untouched.
- [x] Host 73 PostgreSQL upgraded to Alembic 0012 head; full PostgreSQL suite 61 passed.
- [x] Migration chain 0001 through 0012 present and current.
- [x] Stale escaped-newline and Phase 4 pending-gate status text reconciled.

## Clean-baseline remediation — 2026-10-02
- [x] Replaced deprecated Starlette/httpx test-client dependency with supported httpx2 2.13.1; API PostgreSQL suite now reports 61 passed with no pytest warning summary.
- [x] Fixed Phase 2 fixture teardown to avoid rollback-on-closed-transaction SQLAlchemy warnings.
- [x] Fixed Procurement and Sales React hook dependency warnings using stable useCallback loaders.
- [x] Web lint now completes with no application lint warnings.
- [x] ESLint remains on the Next-compatible 9.x peer range; upstream npm deprecation metadata is non-actionable until eslint-config-next dependencies support ESLint 10. npm audit reports 0 vulnerabilities.
- [x] Clean-baseline CI 37001928091 PASS: Ruff, mypy, migrations, 61 PostgreSQL tests, dependency audits, Web lint/typecheck/tests/build and Gitleaks.

## Latest activity
- Phase 9 Sales & CRM implementation complete.
- Implementation acceptance GitHub Actions run 36998921435 PASS.
- Final Phase 9 closure GitHub Actions run 37000090937 PASS, including full-history Gitleaks CLI scan.
- QT revisions/expiry/acceptance and QT -> SO traceability completed.
- Reservation available-stock semantics, release, partial delivery/return and Inventory integration completed.
- Sales order timeline and Web operations surface completed.
- Immediate next executable action is Phase 10 contract read after final Phase 9 documentation CI is green.
