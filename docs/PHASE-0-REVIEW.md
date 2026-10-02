# Phase 0 Architecture Review

Status: PASS
Review scope: Phase 0 architecture contracts through Phase 1–6 implementation readiness.

## Reviewed
Master plan; Domain; Data Model and detailed ERD; Module boundaries; Organization; Document lifecycle/numbering; Authorization and matrix; Inventory and execution/concurrency; Import/opening stock; API/Audit; Accounting boundary; Operations; Phase 1–6 acceptance gates; Web Design Contract.

## Findings and resolutions

### F-001 Warehouse branch/legal-entity integrity — RESOLVED
Finding: ERD stated that branch must belong to warehouse legal entity but left exact database enforcement as migration design.
Risk: application bug could persist a warehouse with branch from a different legal entity inside the same tenant.
Resolution: ORGANIZATION.md makes this invariant normative; ERD now requires branches UNIQUE(tenant_id,legal_entity_id,id) and warehouse composite FK (tenant_id,legal_entity_id,branch_id).
Severity before resolution: HIGH.

### F-002 Opening stock bypass risk — RESOLVED
Finding: OPENING existed as inventory transaction type but import execution path was not normative.
Resolution: IMPORT-OPENING-STOCK.md requires staged validation and commit through Inventory posting/idempotency/ledger/balance/audit/outbox; no direct balance load.
Severity: HIGH.

### F-003 Stock-count posting permission ambiguity — RESOLVED
Finding: inventory.count and inventory.adjust could be interpreted as interchangeable.
Resolution: AUTHORIZATION-MATRIX.md requires count plus adjust for variance posting unless an explicit approved workflow delegates posting.
Severity: MEDIUM.

### F-004 Reversal negative-stock behavior — RESOLVED
Finding: reverse semantics needed current-stock rule.
Resolution: INVENTORY-EXECUTION.md rejects reversal that would make current stock negative; correction cannot rewrite history.
Severity: HIGH.

### F-005 Web design versus domain state — RESOLVED
Finding: design source is visual and cannot define ERP stock/document semantics.
Resolution: WEB-DESIGN-CONTRACT.md preserves approved visual language while explicitly deferring status, authorization and stock behavior to domain/API contracts.
Severity: MEDIUM.

## Consistency conclusions
Tenant isolation: PASS. Tenant-owned references use composite tenant integrity; polymorphic references require use-case validation/tests.
Organization: PASS after F-001.
Inventory authority: PASS. Ledger authoritative, balance projection rebuildable, only POSTED effects.
Concurrency/idempotency: PASS specification. Deterministic aggregate-before-lock and retry-safe idempotency are defined.
Document lifecycle: PASS. Cancel/reversal distinction and immutable posted history align.
Authorization: PASS. Permission-based deny-default model aligns with API and acceptance tests.
API/Audit: PASS. Stable error, exact decimal, trusted context and correlated audit conventions align.
Import/opening stock: PASS after F-002.
Purchasing/Sales future compatibility: PASS at architecture level. PO/SO do not mutate physical stock; receipt/delivery call Inventory.
Accounting future compatibility: PASS. Physical quantity separated from valuation/GL; outbox/contracts preserve integration path.
LINE future compatibility: PASS. Adapter will call same application use cases; no LINE stock logic.
Web design: PASS for scaffold/component direction, based on user-approved design source.

## Deferred implementation choices — not blockers
- PostgreSQL CHECK versus enum details.
- Exact RLS DDL (application tenant scoping remains mandatory; RLS defense-in-depth).
- physical index tuning based on EXPLAIN/telemetry.
- exact session implementation choice within security contract.
- production font delivery/fallback implementation respecting licensing.
These cannot weaken normative contracts without architecture review.

## Phase 0 exit gate
Critical invariants are unambiguous; Inventory/Purchasing/Sales stock effects are defined; schema direction preserves multi-company, future lot/serial/reservation, Accounting and LINE boundaries; Phase 1–6 gates are executable.

PHASE 0: PASS.

Next: Phase 1 Engineering Foundation on host 73 only.
