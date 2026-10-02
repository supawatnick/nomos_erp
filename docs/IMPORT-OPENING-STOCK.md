# Import and Opening Stock Contract

Status: PASS — Phase 0.

## Principle
Imports are staged, validated, previewable, auditable and retry-safe. Imports never bypass normal domain/application services merely for speed.

## Import lifecycle
UPLOADED -> VALIDATING -> VALIDATED_WITH_ERRORS|READY_TO_COMMIT -> COMMITTING -> COMMITTED|FAILED|CANCELLED.

Validation is side-effect free. Commit is explicit and permission checked. A committed batch is immutable; correction uses normal business workflows.

## Phase 1–6 import types
PRODUCT, CATEGORY, UNIT, WAREHOUSE_LOCATION and OPENING_STOCK. Customer/Supplier imports arrive with Partner phase.

Each batch records source attachment, actor, tenant, counts and per-row source/normalized/errors. Validation errors use stable codes and row/field coordinates.

## Product/master imports
Normalize identifiers and decimals first. Validate duplicate rows within file and conflicts with tenant data. Commit must use the same master-data use cases/constraints as Web API. Partial commit is NOT the default: a batch commits atomically unless an import type explicitly documents chunk semantics and resumability.

## Opening stock
Opening stock is a controlled Inventory transaction type, not a direct balance load.
Required permission: inventory.adjust.
Every committed opening-stock row resolves tenant, legal entity, product, unit, warehouse/location, positive quantity and optional documented unit cost/currency context.
Commit groups rows into one or more deterministic OPENING transactions according to legal entity/document-size policy. Each transaction uses Inventory posting, balance locking, ledger, audit, outbox and idempotency rules.

Opening stock may only ADD physical opening quantity. Corrections after posting use reversal/adjustment. Re-running the same committed batch cannot duplicate stock.

## Idempotency
Batch commit has a stable idempotency scope keyed by tenant + import batch. Row target identities/results are persisted. COMMITTED batch commit returns prior result. A changed source requires a new batch/version, never reuse of the committed batch.

## Security
File object access is tenant scoped. File type/size limits and safe parsing are required. Spreadsheet formulas/macros are data, never executed. User-provided filenames do not become object paths. Errors must not expose other tenants' conflicts/existence.

## Required tests
- validate causes no business writes;
- malformed/precision/unknown references produce row errors;
- duplicate SKU/barcode/file row handled deterministically;
- cross-tenant reference rejected without disclosure;
- commit permission enforced;
- failed atomic commit leaves no partial master/stock writes;
- opening stock creates POSTED ledger and reconciled balance;
- same batch commit twice does not duplicate;
- concurrent commit creates one result;
- correction uses reversal/adjustment, not balance edit;
- audit records validation/commit/failure safely.
