# Phase 4 Review — Inventory Engine

Date: 2026-10-02
Status: **PASS**

## Scope completed
Phase 4 establishes Inventory as the authoritative physical-quantity engine for NOMOS ERP.

### Persistence
Migration 0005 adds:
- inventory_transactions
- inventory_transaction_lines
- inventory_balances
- inventory permissions

Transactions are POSTED immutable history. Lines store exact quantity/base quantity and direction. Balances are a rebuildable projection keyed by tenant/product/location. Database constraints enforce positive line quantities, valid direction, non-negative projected on-hand, tenant ownership and reversal linkage.

### Posting engine
One application posting layer implements:
- RECEIVE
- ISSUE
- TRANSFER
- ADJUST
- OPENING
- REVERSAL

Posting aggregates effects before locking. Balance rows are created safely and locked in deterministic product/location order. Default policy rejects negative stock. Transfer source decrease and destination increase commit atomically. Adjustment direction is explicit. Posted history is not edited/deleted; reversal creates opposite lines and bidirectional linkage.

### Unit/location/organization validation
Posting validates:
- active tenant-owned stockable/consumable product
- configured unit/base conversion
- unit precision and max 8-decimal base quantity
- active stock-enabled location and warehouse
- warehouse legal entity matches transaction legal entity
- transfer destination is distinct, active and same legal entity

Archived hierarchy cannot accept new posting. Phase 4 activates the deferred Phase 3 rule that stock-bearing locations/warehouses cannot be archived.

### Idempotency
Stock commands require a stable Idempotency-Key at the API boundary.
Fingerprint includes transaction type, organization scope, lines/directions/destinations, reference/reason and source contract.
Same key/same payload replays the durable transaction identity.
Same key/different payload conflicts.
Concurrent same-key requests cannot create duplicate stock effects.
Reversal is also replay-safe.

### Audit/outbox
Committed posting writes correlated inventory.transaction.posted audit and transactional outbox event.
Committed reversal writes inventory.transaction.reversed audit/outbox.
Rollback does not leave committed business/audit/outbox effects.

### Cross-core contract
Inventory transactions retain source_type/source_id/source_number and request/idempotency provenance so later Procurement Goods Receipt/Return and Sales Delivery/Return can invoke Inventory without mutating its tables. Finance may consume durable valuation/posting facts later; Inventory does not own journals.

### API
FastAPI version 0.4.0 includes:
- POST /api/v1/inventory/transactions
- POST /api/v1/inventory/transactions/{id}/reverse
- GET /api/v1/inventory/transactions
- GET /api/v1/inventory/balances
- GET /api/v1/inventory/reconciliation

Server-derived tenant/session context and permissions remain authoritative.

## PostgreSQL acceptance
Phase 4 tests cover:
- receive and issue
- opening stock
- positive/negative adjustment
- no-negative-stock rejection
- atomic transfer
- idempotent replay
- idempotency payload conflict
- concurrent same-key duplicate prevention
- concurrent issue/no oversell
- reversal linkage
- ledger-to-balance reconciliation
- cross-tenant location rejection
- audit/outbox creation
- stock-bearing location archive rejection

## Verification
Required final gate:
- Ruff
- mypy
- Alembic upgrade through 0005
- pytest PostgreSQL suite
- pip-audit
- npm ci/audit
- Web lint/typecheck/tests/build
- gitleaks
- synchronized clean host 73
- GitHub Actions success on final documentation commit

## Phase 4 exit
Phase 4 is complete when the final gate above is green. Phase 5 is Inventory Web ERP and must consume these application/API contracts rather than reimplement stock rules in UI.
