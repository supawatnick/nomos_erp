# NOMOS ERP — Project Status & Next Actions

> This file is the operational handoff/source of truth for current execution state. Update it at the end of every meaningful work session and whenever a blocker/status materially changes.

## Current stage
Phase 0 — Specification and Architecture

Overall status: PHASE 0 PASS — READY FOR PHASE 1

Primary objective: begin Phase 1 Engineering Foundation on host 73 only, preserving all Phase 0 contracts.

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
- [x] Web Design Contract — `docs/WEB-DESIGN-CONTRACT.md`
- [x] Phase 0 architecture review — `docs/PHASE-0-REVIEW.md`
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

- [x] Detailed ERD: columns, keys, constraints and relationships for Phase 1–6 tables — `docs/ERD-PHASE-1-6.md`.
- [x] Permission matrix: actor/role examples mapped to permissions and high-risk actions — `docs/AUTHORIZATION-MATRIX.md`.
- [x] Inventory state machine and exact posting/reversal rules — `docs/INVENTORY-EXECUTION.md`.
- [x] Inventory concurrency/locking/idempotency contract — `docs/INVENTORY-EXECUTION.md`.
- [x] Organization model details — `docs/ORGANIZATION.md`.
- [x] API conventions: versioning, pagination/filtering, request context, idempotency, errors — `docs/API-AUDIT-CONTRACT.md`.
- [x] Audit event taxonomy — `docs/API-AUDIT-CONTRACT.md`.
- [x] Import/opening-stock contract — `docs/IMPORT-OPENING-STOCK.md`.
- [x] Phase 1–6 acceptance criteria/checklists — `docs/PHASE-1-6-ACCEPTANCE.md`.
- [x] Phase 0 cross-document consistency review — PASS in `docs/PHASE-0-REVIEW.md`.

## NEXT ACTIONS — execute in this order

### NEXT 1 — Phase 1 environment verification on host 73
Before scaffolding:
1. sync `/root/nomos_erp` on host 73 to current main using host 73 credentials;
2. verify working tree/branch and do not overwrite uncommitted work;
3. inventory installed Node, package manager, Python, dependency manager, Docker/Compose and Git versions on host 73;
4. record chosen supported runtime versions/tooling in engineering docs;
5. confirm required ports/storage and that no NOMOS workload is placed on host 72.

Exit: host 73 is verified ready for deterministic scaffold or missing dependencies are explicitly identified for installation on 73.

### NEXT 2 — Scaffold Phase 1 on host 73
Create Web/API/worker/module/infra/test structure, configuration, PostgreSQL development service, migration baseline, health/readiness and shared request context foundations.

### NEXT 3 — Phase 1 CI and clean-boot gate
Add lint/type/unit/integration/migration/build/secret/dependency checks, document clean boot, execute the Phase 1 acceptance gate and record evidence.

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
- Phase 0 final architecture review PASS — `docs/PHASE-0-REVIEW.md`.
- Closed Organization, Import/Opening Stock, Phase 1–6 Acceptance and Web Design contracts.
- Review found warehouse branch/legal-entity DB-integrity ambiguity; resolved in ERD with composite organization FK.
- All critical Phase 0 findings resolved; no architecture blocker remains.
- Phase 0 status: PASS. Immediate next action: Phase 1 environment verification on host 73 only.
- NEXT 1 Inventory execution/concurrency contract PASS — `docs/INVENTORY-EXECUTION.md`.
- NEXT 2 Authorization matrix PASS — `docs/AUTHORIZATION-MATRIX.md`.
- NEXT 3 API/Audit contract PASS — `docs/API-AUDIT-CONTRACT.md`.
- Locked deterministic aggregate-before-lock inventory posting, exact idempotency behavior, reversal constraints, tenant-wide Phase 1–6 permission matrix, stable API/error/pagination conventions and audit taxonomy.
- No new architecture blocker found.
- Immediate next action: close remaining Phase 0 organization/import/acceptance/design contracts, then run final Phase 0 architecture review.
- NEXT 1 Detailed ERD completed and PASS: `docs/ERD-PHASE-1-6.md`.
- Locked database safeguards: composite same-tenant foreign keys, exact numeric/time conventions, append-oriented ledger/audit, balance projection key, idempotency/outbox persistence, concurrency-safe sequence persistence and traceable imports.
- No new architecture blocker found.
- Immediate next action: Inventory execution/concurrency contract.
- Phase 0 architecture documentation set created and registered in `AGENTS.md`.
- Current Phase 0 status remains IN PROGRESS.
- Immediate next action: detailed Phase 1–6 ERD/schema contract.
