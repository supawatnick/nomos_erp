# Phase 9 Review — Sales & CRM

Status: **PASS — PHASE 9 COMPLETE**

## Scope delivered
- Existing Phase 7 lead/customer/opportunity/activity foundation retained as CRM entry path.
- Quotation (QT) with server-side numbering, exact Decimal commercial lines, validity/expiry, send and immutable revision snapshots.
- Material QT revision after send creates a new explicit revision and returns the quotation to DRAFT.
- QT acceptance binds accepted revision/evidence and creates a Sales Order preserving source quotation ID + revision.
- QT/SO creation and confirmation have no physical Inventory side effect.
- Sales Order confirmation, explicit reservation, release and high-risk cancellation boundaries.
- Reservation records reduce derived available stock only; on-hand remains Inventory-ledger authoritative.
- Reservation availability is checked under Inventory balance locking and existing active reservations are included.
- Delivery posts Inventory ISSUE atomically; sales return posts Inventory RECEIVE atomically.
- Delivery/return are idempotent and preserve Inventory source identity.
- Partial delivery, return and order progress quantities are first-class.
- Order status timeline persists confirmation, reservation, release, delivery and cancellation transitions.
- Sales API exposes quotation pipeline, QT commands, SO tracking, reservation, delivery/return and timeline.
- Sales Web surface exposes quotation pipeline, order progress, reservation and fulfillment and waits for server commit before POSTED success.
- Finance boundary preserved: QT/SO/delivery code does not write Finance/GL/AR tables.

## Schema
Migration `0012_phase9_sales` adds quotations/revisions/lines, sales orders/lines/events, reservations, deliveries/lines, returns/lines and Sales permission namespaces.

## Acceptance evidence
Implementation head: `65415e9369354c378f359cd40b5b07dc50283302`.
Implementation GitHub Actions run `36998921435`: **SUCCESS**.
Final closure GitHub Actions run `37000090937`: **SUCCESS** on `9a5872695d492b8c669ddf47957cbeebe85d7bfe`.
CI secret scanning now uses pinned Gitleaks CLI `v8.28.0` directly, avoiding the licensed Action/API dependency; full-history scan passes with one narrowly reviewed historical documentation false-positive allowlist.
- Ruff: PASS.
- mypy: PASS.
- Alembic through 0012: PASS.
- PostgreSQL/API pytest: PASS, including QT revision/acceptance traceability, expiry, cross-tenant customer rejection, reservation availability, release/timeline, partial delivery, idempotent replay and return reconciliation.
- pip-audit: PASS.
- npm ci/audit high: PASS.
- Web lint/typecheck/tests/build: PASS.
- gitleaks: PASS.

## Exit gate
- QT -> SO traceability preserved: PASS.
- Sales pipeline/order state explicit and auditable: PASS.
- Reservation/on-hand/available semantics tested transactionally: PASS.
- Delivery/return invoke Inventory rather than mutating balances directly: PASS.
- Partial fulfillment and retry safety: PASS.
- Finance ownership boundary: PASS.

## Handoff
Phase 9 Sales & CRM is complete. Next phase is Phase 10 Approval & commercial controls. Begin only from a clean, green Phase 9 baseline.
