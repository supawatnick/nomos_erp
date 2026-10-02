# NOMOS ERP — Project Status & Next Actions

> This file is the operational handoff/source of truth for current execution state. Update it at the end of every meaningful work session and whenever a blocker/status materially changes.

## Current stage
Phase 0 — Specification and Architecture

Overall status: IN PROGRESS

Primary objective: finish the architecture contracts and acceptance gates required before Phase 1 engineering scaffold begins.

## Completed

### Infrastructure / repository
- [x] GitHub repository established.
- [x] Host 72 designated control/orchestration only.
- [x] Host 73 (`nomos-erp`) designated the only NOMOS development execution host.
- [x] Host 73 authenticates to GitHub using its own SSH identity.
- [x] Repository cloned on host 73 at `/root/nomos_erp`.
- [x] Pre-work rule recorded in `AGENTS.md`.

### Phase 0 planning contracts
- [x] Master phased delivery plan — `docs/MASTER-PLAN.md`
- [x] Domain vocabulary/invariants — `docs/DOMAIN.md`
- [x] Architectural data-model direction — `docs/DATA-MODEL.md`
- [x] Document lifecycle — `docs/DOCUMENT-LIFECYCLE.md`
- [x] Authorization model — `docs/AUTHORIZATION.md`
- [x] Accounting/costing boundary — `docs/ACCOUNTING-BOUNDARY.md`
- [x] Module boundaries — `docs/MODULES.md`
- [x] Document numbering contract — `docs/NUMBERING.md`
- [x] Stable API error-code baseline — `docs/ERROR-CODES.md`
- [x] Operations baseline — `docs/OPERATIONS.md`
- [x] Roadmap aligned to Master Plan.
- [x] Inventory/Documents/RBAC/Multi-tenancy implementation skills added.

## Decisions passed / locked
- [x] Web ERP is the primary product surface.
- [x] LINE is Phase 13 and must reuse Web/application use cases.
- [x] PostgreSQL is the authoritative business database.
- [x] Initial architecture is a modular monolith.
- [x] Shared DB/shared schema multi-tenancy with strict tenant scoping.
- [x] Tenant, Legal Entity, Branch, Warehouse and Location are distinct concepts.
- [x] Inventory ledger is authoritative; balance is a projection.
- [x] Posted inventory history is immutable; correction uses reversal/compensation.
- [x] PO does not change physical stock; Goods Receipt does.
- [x] Sales Order does not reduce on-hand; Delivery/Issue does.
- [x] Accounting/costing is separated from physical quantity semantics.
- [x] Human document numbers are separate from immutable database IDs.
- [x] Host 72 must not run NOMOS development workloads; development runs on host 73.

## Current blockers
No architecture blocker currently known.

Operational note: nested SSH Git commands from the control host may sometimes be blocked by platform safety gates. This does not change the architecture rule; host 73 remains the development target. Do not work around this by moving workloads to host 72.

## In progress / not yet passed
Phase 0 is NOT complete. The following contracts still require completion and review:

- [ ] Detailed ERD: columns, keys, constraints and relationships for Phase 1–6 tables.
- [ ] Permission matrix: actor/role examples mapped to permissions and high-risk actions.
- [ ] Inventory state machine and exact posting/reversal rules.
- [ ] Inventory concurrency/locking/idempotency contract.
- [ ] Organization model details: legal entity/branch/warehouse ownership and defaults.
- [ ] API conventions: versioning, pagination/filtering, request context, idempotency, errors.
- [ ] Audit event taxonomy.
- [ ] Import/opening-stock contract.
- [ ] Phase 1–6 acceptance criteria/checklists.
- [ ] Phase 0 cross-document consistency review.

## NEXT ACTIONS — execute in this order

### NEXT 1 — Detailed ERD
Create a detailed Phase 1–6 ERD/spec covering:
1. tenants / settings
2. legal_entities / branches
3. users / memberships / roles / permissions / sessions
4. products / categories / units / conversions / barcodes
5. warehouses / locations
6. inventory transaction header/lines
7. balance projection
8. stock count / reorder rules
9. audit / idempotency / outbox
10. document sequences / imports / attachments

For every table define tenant ownership, PK/FK, unique constraints, indexes, exact decimal/time types, archive/delete policy and cross-tenant integrity strategy.

Exit: schema can be translated into initial migrations without unresolved ownership or inventory-integrity questions.

### NEXT 2 — Inventory execution contract
Specify state transitions, posting algorithm, deterministic row-lock order, negative-stock rule, transfer atomicity, idempotency replay/conflict behavior, reversal linkage and reconciliation algorithm.

Exit: concurrency tests can be written directly from the contract.

### NEXT 3 — Authorization matrix
Define baseline roles only as examples, map every Phase 1–6 operation to explicit permissions, identify stronger-permission actions and future approval hooks.

Exit: API authorization tests can be generated from the matrix.

### NEXT 4 — API and audit contracts
Finalize request context, pagination/filtering, mutation/idempotency headers, error mapping and audit-event taxonomy.

Exit: FastAPI skeleton has stable conventions before feature routers are added.

### NEXT 5 — Phase 0 architecture review
Cross-check all docs for contradictions, missing tenant scope, stock side effects, lifecycle conflicts and future Purchasing/Sales/Accounting compatibility.

Exit: Phase 0 marked PASS.

### NEXT 6 — Start Phase 1 on host 73 only
After Phase 0 PASS:
- sync repository on 73
- inspect installed runtime/tooling on 73
- scaffold Web/API/worker
- configure PostgreSQL/Redis via development infrastructure on 73
- migration baseline
- CI/lint/type/test/build
- health/readiness
- prove clean boot from documented commands

Do NOT begin NEXT 6 before Phase 0 exit gate passes.

## Session handoff procedure
Before starting NOMOS work:
1. Read `AGENTS.md`.
2. Read this file.
3. Read the relevant docs/skills for the current NEXT action.
4. Continue the first incomplete NEXT action unless the user changes priority.

Before ending meaningful work:
1. Update Completed.
2. Update Decisions passed/locked if a decision became authoritative.
3. Update Current blockers.
4. Update In progress/not yet passed.
5. Rewrite NEXT ACTIONS so NEXT 1 is the actual next executable task.
6. Record the latest meaningful result below.

## Latest activity
- Phase 0 architecture documentation set created and registered in `AGENTS.md`.
- Current Phase 0 status remains IN PROGRESS.
- Immediate next action: detailed Phase 1–6 ERD/schema contract.
