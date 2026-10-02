# Phase 8 Review — Procurement & Purchasing

Status: **PASS — PHASE 8 COMPLETE**

## Scope
Phase 8 implements Purchase Request, RFQ/supplier quotation comparison, Purchase Order, Goods Receipt, Purchase Return, partial receipt and procurement reconciliation.

## Locked boundaries
- PR/RFQ/PO are commercial intent and never mutate physical stock.
- Goods Receipt/Return invoke the Phase 4 Inventory application contract.
- Supplier identities come from Phase 7 business partners and must have `is_supplier=true`.
- Quantities and money use exact Decimal / NUMERIC semantics.
- Cross-tenant supplier/product/unit/location/document references fail.
- PO receipt status derives from line-level ordered/received/returned quantities.
- Cross-core stock effects are idempotent and procurement state advances only after Inventory succeeds.
- Finance-owned Supplier Invoice/AP/payment are out of Phase 8.

## Work log
### 2026-10-02 — Phase 8 start
- Read AGENTS.md, PROJECT-STATUS.md, MASTER-PLAN, HOST-73-RUNBOOK, WEB-DESIGN-CONTRACT and procurement/domain contracts before implementation.
- Runtime verified on host 73 at `/root/nomos_erp`.
- Added migration `0009_phase8_procurement` as the first Phase 8 schema slice.
- Added tenant-scoped Purchase Request header/lines.
- Added tenant-scoped RFQ and supplier-response/comparison persistence.
- Activated reserved Phase 8 permission namespace.
- Purchase Order and Goods Receipt/Return remain intentionally pending; Phase 8 is not PASS yet.

## Acceptance gate
Phase 8 may be marked PASS only after migrations, PostgreSQL tests, Ruff, mypy, API/Web acceptance, dependency/security checks and GitHub Actions are green, with PR/RFQ/PO/receipt/return reconciliation tests passing.


### 2026-10-02 — Phase 8 closure
- Added Purchase Order persistence and dedicated submit/approve/send lifecycle with server-side PO numbering and approval fingerprint/version binding.
- Added Goods Receipt and Purchase Return persistence with line-level PO traceability.
- Goods Receipt posts Inventory RECEIVE atomically before received quantities and PO operational status advance.
- Purchase Return posts Inventory ISSUE atomically and rejects cumulative return above cumulative received quantity.
- Partial receipts are first-class: PO status derives from ordered/received line facts as SENT, PARTIALLY_RECEIVED or RECEIVED.
- Receipt/return retries use stable idempotency keys; successful replay does not duplicate Inventory transactions or stock effects.
- Procurement Inventory orchestration uses the shared Inventory validation, locking, no-negative-stock, ledger, audit and outbox core while authorizing the caller with procurement.receive.
- RFQ created from a Purchase Request copies line facts into RFQ lines; supplier responses can persist exact per-line quantity/price/discount/tax totals and expose a comparison API.
- Replaced the arbitrary Purchase Request transition API with dedicated submit/approve/reject/cancel commands.
- PR and RFQ human document numbers are allocated server-side from concurrency-safe document sequences; client-supplied numbers were removed from API input.
- Added Procurement Web operations surface for PO progress, partial Goods Receipt and Purchase Return. Web waits for server success before presenting posted success.
- PR/RFQ/PO continue to have no physical Inventory side effects.

## Final acceptance evidence
- Implementation head before review: `7ddc082348b14f4397559dca2cfed02f6f7f5235`.
- GitHub Actions implementation gate: run `36996602994` — SUCCESS.
- Ruff: PASS.
- mypy: PASS.
- Alembic upgrade through `0011_phase8_receipts_returns`: PASS.
- PostgreSQL/API pytest suite: PASS, including PR/RFQ/PO and partial receipt/return reconciliation coverage.
- pip-audit: PASS.
- npm ci and npm audit high: PASS.
- Web lint, TypeScript typecheck, tests and production build: PASS.
- gitleaks: PASS.
- Phase 8 exit invariants verified: PR/RFQ/PO do not change stock; receipt/return use Inventory; partial receipt and remaining quantities reconcile; tenant and permission boundaries remain server-side.

## Handoff
Phase 8 Procurement & Purchasing is complete. The next implementation phase is Phase 9 Sales & CRM commercial documents per MASTER-PLAN. Do not begin Phase 9 from a dirty or failing baseline.
