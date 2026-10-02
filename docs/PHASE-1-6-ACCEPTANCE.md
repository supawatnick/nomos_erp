# Phase 1–6 Acceptance Gates

Status: PASS — Phase 0 specification.

A phase advances only when its gate passes.

## Phase 1 Engineering Foundation
- Web/API/worker skeleton exists on host 73 only.
- deterministic documented boot from clean checkout;
- PostgreSQL migration upgrade works from empty DB;
- lint/type/unit/integration/build gates in CI;
- health and readiness distinguish process health from dependency readiness;
- configuration validates missing secrets/settings and does not commit secrets;
- structured request IDs/log baseline;
- no application/database runtime installed on host 72.
Exit evidence: commands, CI run, migration output and health checks recorded in PROJECT-STATUS.

## Phase 2 SaaS Platform Core
- tenant/legal entity/branch/user/membership/session/RBAC/audit/idempotency/outbox implemented;
- server-derived tenant context;
- deny-by-default permission enforcement;
- same-tenant composite FK strategy in migrations;
- cross-tenant read/update/delete/reference/guessed-ID tests pass;
- disabled membership/session behavior tested;
- critical administration audit records verified.
Exit: automated tenant-isolation and RBAC matrix green.

## Phase 3 Catalog and Warehouse
- categories/units/conversions/products/barcodes/warehouses/locations/document sequence implemented;
- archive lifecycle and duplicate constraints;
- warehouse/branch/legal-entity consistency enforced;
- location hierarchy/cycle/cross-warehouse validation;
- list search/filter/sort/pagination API + Web;
- import-safe stable IDs and exact decimals.
Exit: master data works end-to-end with tenant isolation and archive semantics.

## Phase 4 Inventory Engine
- receive/issue/transfer/adjust/reversal/opening use same Inventory application layer;
- only POSTED ledger changes stock;
- deterministic aggregate-before-lock posting;
- negative stock rejected;
- idempotency replay/conflict/concurrent-key tests;
- concurrent issue test proves no oversell;
- transfer atomic/no partial write;
- posted immutable and reversal linked;
- ledger reconciliation equals balance projection;
- audit/outbox correlated with committed posting.
Exit: all Inventory Execution required tests green.

## Phase 5 Inventory Web ERP
- Dashboard, Stock, Receive, Issue, Transfer, Adjustment, Movements, Products, Warehouse/Locations, Users/Roles and Audit screens;
- approved NOMOS Web Design Contract implemented consistently;
- search/filter/sort/pagination and loading/empty/error/retry states;
- permission-aware actions but API remains authority;
- destructive/high-impact confirmation;
- Thai/English-ready strings/layout;
- keyboard/accessibility basics and desktop/tablet usability;
- no false optimistic success for stock mutation.
Exit: selected Web E2E operator flows pass against real API/database.

## Phase 6 Inventory Operations
- stock count snapshot/count/review/post adjustment;
- reorder/low-stock rules;
- PRODUCT/master and OPENING_STOCK import lifecycle;
- operational inventory reports/export;
- count/import never direct-edit balance;
- import validation preview and traceability;
- opening stock retry cannot duplicate;
- report queries bounded and tenant scoped.
Exit: Internal Inventory MVP acceptance suite green and operational handoff documented.

## Universal DoD
Every feature: tenant isolation, authorization, invariant, migration, validation/error behavior, audit where critical, tests including negatives, docs/OpenAPI, logs/metrics and safe defaults. Stock-changing features additionally require transactionality, idempotency, concurrency and reconciliation evidence.
