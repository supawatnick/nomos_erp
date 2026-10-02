# NOMOS ERP — Project Status & Next Actions

> Operational handoff/source of truth. Read after AGENTS.md before every work session.

## Current stage
Phase 2 — SaaS Platform Core

Overall status: **PHASE 2 PASS — READY FOR PHASE 3**

Primary objective: begin Phase 3 Catalog and Warehouse on host 73 only while preserving Phase 0–2 security and tenant-isolation contracts.

## Completed

### Phase 0 — Specification and Architecture
- [x] Phase 0 architecture review PASS — docs/PHASE-0-REVIEW.md.
- [x] Domain, ERD, organization, authorization, inventory execution, API/audit, import/opening stock, operations, acceptance and Web Design contracts locked.

### Phase 1 — Engineering Foundation
- [x] Web/API/worker skeletons, PostgreSQL 17, Alembic, configuration validation, request logging, health/readiness and CI foundation.
- [x] Phase 1 acceptance and GitHub Actions gates PASS.

### Phase 2 — SaaS Platform Core
- [x] Tenant, tenant settings, legal entity and branch persistence.
- [x] Global users plus tenant membership persistence.
- [x] Tenant-scoped roles, global permissions, role-permission and membership-role persistence.
- [x] Session persistence with hashed tokens, active membership/user enforcement and revocation.
- [x] PBKDF2-SHA256 password hashing primitives.
- [x] Server-derived trusted tenant context and effective permission resolution.
- [x] Deny-by-default permission enforcement and RBAC allow/deny matrix.
- [x] Same-tenant composite FK strategy for tenant-owned organization/RBAC references.
- [x] Idempotency persistence with same-fingerprint replay vs conflicting-fingerprint semantics.
- [x] Append-oriented audit and transactional outbox foundations.
- [x] Tenant-scoped legal-entity repository prevents cross-tenant read/update/archive guessed-ID access.
- [x] Authorized organization mutation writes correlated audit and outbox rows in the same transaction.
- [x] Auth transport surface: /api/v1/auth/login, /api/v1/auth/logout and /api/v1/auth/context.
- [x] Server owns canonical X-Request-ID; X-Correlation-ID is logging/correlation input only.
- [x] Phase 2 review documented in docs/PHASE-2-REVIEW.md.

## Phase 2 acceptance evidence
- API Ruff: PASS.
- API mypy strict: PASS.
- PostgreSQL Alembic upgrade through 0003_phase2_completion: PASS.
- Unit + PostgreSQL integration suite: PASS in CI.
- Cross-tenant composite reference rejection: PASS.
- Cross-tenant read/update/archive isolation: PASS.
- Disabled membership and revoked-session rejection: PASS.
- RBAC permission matrix: PASS.
- Idempotency replay/conflict gate: PASS.
- Critical administration audit + outbox correlation: PASS.
- Python dependency audit: PASS.
- Web npm install/audit/lint/typecheck/test/build regression gates: PASS.
- gitleaks: PASS.
- GitHub Actions code gate: PASS — run 36972680322 on commit f50fa9fccffdf3320d69fd881a2cdadd1f2a9b17.

## Decisions passed / locked
- Security/tenant isolation remains highest priority.
- Tenant identity is resolved from authenticated active membership, never trusted from business request payloads.
- Authorization checks permission codes, not role names, and denies by default.
- Default branch remains UX-only context and grants no authorization.
- Cross-tenant guessed IDs must not reveal foreign object existence.
- Session tokens are never stored raw.
- Critical committed administration mutations create correlated append-oriented audit records and transactional outbox rows.
- Host 72 remains control/orchestration only; NOMOS development/runtime/build/test/database execution remains on host 73.
- PostgreSQL remains authoritative and modular monolith remains the initial architecture.

## Current blockers
- None for Phase 3.
- Platform safety gates may occasionally require a permitted single-command SSH pattern; this is an execution-tool constraint, not a NOMOS architecture blocker.

## In progress / not yet passed
- Phase 3 Catalog and Warehouse has not started.
- Two preserved pre-sync stashes remain on host 73 from conflicting local scaffold work; do not drop them until reviewed.

## NEXT ACTIONS — execute in this order

### NEXT 1 — Phase 3 catalog persistence
Implement categories, units, products, product units and barcodes with tenant-scoped composite FKs, exact conversion factors, archive lifecycle and duplicate constraints.

### NEXT 2 — Phase 3 warehouse/location persistence
Implement warehouses and locations with legal-entity/branch consistency, same-warehouse parent constraints, archive rules and document sequence persistence.

### NEXT 3 — Phase 3 APIs/Web + acceptance
Implement tenant-scoped list/search/filter/sort/pagination APIs and Web master-data flows, then run archive/duplicate/isolation tests and the Phase 3 acceptance gate.

## Latest activity
- Phase 2 SaaS Platform Core implemented and acceptance suite green.
- Final Phase 2 code verification PASS in GitHub Actions run 36972680322.
- Phase 2 implementation/review contract recorded in docs/PHASE-2-REVIEW.md.
- Immediate next executable action: Phase 3 catalog persistence on host 73.
