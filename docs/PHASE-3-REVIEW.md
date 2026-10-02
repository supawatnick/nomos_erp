# NOMOS ERP — Phase 3 Review

Status: **PASS — Catalog and Warehouse**

## Scope completed

Phase 3 establishes tenant-scoped master data required by the Inventory engine.

### Catalog
- Categories with same-tenant hierarchy and archive lifecycle.
- Units with precision 0–8.
- Products with SKU uniqueness, category/base-unit ownership, STOCKABLE/CONSUMABLE/SERVICE type and NONE/LOT/SERIAL tracking.
- Product-unit conversions use NUMERIC(24,8), require positive factors and reject excess application precision.
- Tenant-unique product barcodes with optional product-unit binding.
- Stable UUID identifiers are preserved across archive operations.

### Warehouse
- Warehouses belong to a legal entity and optionally a branch.
- Composite database FK guarantees an assigned branch belongs to the same tenant and legal entity.
- Warehouse locations have tenant/warehouse-scoped codes.
- Composite parent FK prevents cross-warehouse parent references.
- Application hierarchy validation rejects self-parenting and cycles.
- Warehouse/location masters use archive semantics rather than destructive deletion.

### Document numbering
- document_sequences supports tenant/document/legal-entity/branch/period scope.
- PostgreSQL NULLS NOT DISTINCT uniqueness protects nullable scopes.
- Allocation locks the sequence row with FOR UPDATE and increments atomically.
- Human document numbers remain separate from UUID primary keys.

### API and authorization
- Product, category, unit, warehouse and location master endpoints are under /api/v1.
- Product conversion and barcode mutation endpoints are implemented.
- Protected master-data operations resolve authenticated tenant context server-side.
- product.read/product.manage and warehouse.read/warehouse.manage permissions are seeded and enforced.
- Product list supports bounded search, status filter, allowlisted sort and opaque cursor pagination.
- Critical catalog/warehouse mutations write audit evidence.

### Web
- Sign-in surface establishes the Phase 2 session used by master-data screens.
- Master-data navigation and pages exist for Products, Categories, Units, Warehouses and Locations.
- Products expose search, status filter, sort, pagination, loading, empty and error states.
- Pages send authenticated tenant context to the API and do not treat UI visibility as authorization.
- Phase 3 Web regression tests cover required routes and product list controls.

## Automated acceptance coverage
- same-tenant catalog FK enforcement;
- duplicate SKU and barcode rejection;
- cross-tenant product lookup isolation;
- exact conversion validation;
- warehouse branch/legal-entity mismatch rejection at DB boundary;
- cross-warehouse location parent rejection;
- location hierarchy cycle rejection;
- document sequence allocation/increment;
- stable product ID after archive;
- Phase 2 tenant/RBAC/session/audit/idempotency regression suite;
- Web route/control regression tests.

## Migration
- 0004_phase3_catalog_warehouse.py adds catalog, warehouse/location and document sequence persistence plus Phase 3 permissions.
- PostgreSQL 17 migration upgrade to Phase 3 head is part of CI before integration tests.

## Decisions locked
- Product master remains tenant-scoped across legal entities in Phase 1–6.
- Unit conversion factors use exact decimals only.
- Warehouse branch assignment is an organization invariant enforced by the database.
- Location hierarchy cannot cross warehouses and cycles are application-invalid.
- Master records archive; stable IDs remain import-safe.
- Document numbering uses transactional allocation, never SELECT MAX + 1.
- Stock-bearing archive enforcement becomes active with Phase 4 inventory balance/ledger persistence; Phase 3 contains no stock state to bypass.

## Exit gate
Phase 3 is PASS when Ruff, mypy, PostgreSQL migration, unit/integration tests, dependency audit, Web lint/type/test/build, gitleaks and final GitHub Actions are green; host 73 is migrated and clean; PROJECT-STATUS.md points to Phase 4.

## Next phase
Phase 4 — Inventory Engine: immutable posted ledger, balances projection, receive/issue/transfer/adjust/reversal/opening posting, deterministic locking, no-negative-stock, idempotency, concurrency and reconciliation.
