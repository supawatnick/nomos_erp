# Phase 6 Review — Inventory Operations / Internal ERP MVP

Date: 2026-10-02
Status: **PASS**

## Outcome
Phase 6 completes the planned Internal Inventory MVP (Phases 0–6). NOMOS now has tenant-safe master data, immutable inventory ledger/balances, Web posting workflows, stock count, reorder signals and bounded operational reporting.

## Stock count
Migration 0006 adds stock_counts and stock_count_lines.
A count:
1. validates active tenant warehouse/legal entity,
2. snapshots current inventory balances and base units,
3. accepts physical counted quantities while DRAFT/COUNTED,
4. calculates variance against the immutable snapshot,
5. posts non-zero variance only through the Phase 4 ADJUST application contract,
6. records source_type=STOCK_COUNT/source_id/source_number,
7. becomes POSTED and is no longer editable.

Posting is permission-gated and replay-safe. Count variance is normalized to product unit precision before calling Inventory. Posted variance therefore inherits Phase 4 locking, no-negative-stock, idempotency, audit/outbox and reconciliation rules.

## Reorder
reorder_policies are tenant/product/location scoped with exact reorder_point and target_quantity.
The actionable reorder view compares current Phase 4 balance to policy and calculates suggested_quantity up to target.

Phase 6 deliberately does **not** create PR/RFQ/PO. Reorder is an inventory replenishment signal. Phase 8 Procurement owns purchasing documents.

## Operational reports
A bounded summary API and Web report expose:
- positive stock positions
- total on hand
- movement count
- posted stock counts
- low-stock/reorder count

The Web can export the bounded summary as CSV. Reporting does not expose arbitrary SQL.

## Web
Added:
- /inventory/operations
- /inventory/counts
- /inventory/reorder
- /inventory/reports

Inventory navigation links these operational surfaces to the Phase 5 workspace.

## Security and audit
Permissions:
- inventory.count
- inventory.count.post
- inventory.reorder.manage
- inventory.report

All records and queries are tenant scoped.
Cross-tenant reorder references are rejected.
Stock-count posting writes audit/outbox and uses the Inventory ledger rather than direct balance mutation.

## Acceptance
PostgreSQL acceptance covers:
- count snapshot
- variance adjustment and final balance
- source provenance
- reconciliation
- posted count immutability
- replay-safe posting
- reorder threshold/suggested quantity
- Procurement boundary
- cross-tenant reorder rejection

Web acceptance covers Phase 6 routes, count idempotency, Procurement boundary and CSV report export.

## Verification
Implementation gate PASS:
- Ruff
- mypy
- Alembic upgrade through 0006_phase6_inventory_operations
- PostgreSQL pytest suite
- pip-audit
- npm ci
- npm audit high
- Web lint/typecheck/tests/build
- gitleaks

Final closure additionally requires this documentation commit to pass the same CI and host73 to be synchronized/clean.

## Internal ERP MVP gate
**Phases 0–6 are complete.**
This milestone is an Internal **Inventory ERP MVP**, not yet the four-core ERP V1.
The four-core ERP V1 still requires Business Partners/CRM, Procurement/Purchasing, Sales/CRM, controls/reporting and Finance/Accounting through Phase 12.

## Next
Phase 7 — Business Partners & CRM Foundation.
