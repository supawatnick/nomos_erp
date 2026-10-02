# Phase 8 Review — Procurement & Purchasing

Status: IN PROGRESS

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
