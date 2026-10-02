# NOMOS ERP — Project Status & Next Actions

> Operational handoff/source of truth. Read after `AGENTS.md` before every work session.

## Current stage
Phase 1 — Engineering Foundation

Overall status: **PHASE 1 PASS — READY FOR PHASE 2**

Primary objective: begin Phase 2 SaaS Platform Core on host 73 only while preserving all Phase 0/1 contracts.

## Completed

### Phase 0 — Specification and Architecture
- [x] Phase 0 architecture review PASS — `docs/PHASE-0-REVIEW.md`.
- [x] Domain, ERD, organization, authorization, inventory execution, API/audit, import/opening stock, operations, acceptance and Web Design contracts locked.

### Infrastructure / execution
- [x] Host 72 is control/orchestration only; no NOMOS runtime, DB, dependency, build, test or migration workload runs there.
- [x] Host 73 (`nomos-erp`) is the NOMOS development execution host at `/root/nomos_erp`.
- [x] Verified 72 -> SSH -> 73 control path and recorded it in `docs/OPERATIONS.md`.
- [x] Host 73 GitHub authentication and repository sync work using host 73 credentials.
- [x] Verified Phase 1 runtime on host 73: Node.js 22.23.3, npm 10.9.9, Python 3.12.3, Docker 29.1.3, Docker Compose 2.40.3, Git 2.43.0.

### Phase 1 — Engineering Foundation
- [x] Web skeleton: Next.js + TypeScript under `apps/web`.
- [x] API skeleton: FastAPI with core/application/domain/infrastructure boundaries under `apps/api`.
- [x] Worker skeleton under `apps/worker`.
- [x] PostgreSQL 17 development service through Docker Compose.
- [x] Alembic migration baseline and empty-database upgrade.
- [x] Configuration validation through Pydantic settings; no production secret committed.
- [x] Request ID middleware and structured request log baseline.
- [x] Liveness `/health` and dependency readiness `/ready`.
- [x] CI gates for Python/Web lint, type checking, tests, migration, build, dependency audit and secret scan.
- [x] Deterministic clean-boot instructions — `docs/ENGINEERING-FOUNDATION.md`.
- [x] Web dependency audit reports zero known vulnerabilities after moving to Node 22 and patched Next.js 16.3.8.

## Phase 1 acceptance evidence
Executed on host 73:
- API Ruff: PASS — `All checks passed!`
- API mypy: PASS — `Success: no issues found in 6 source files`
- API pytest: PASS — 2 tests passed
- Empty PostgreSQL migration: PASS — fresh `nomos_phase1_gate` DB upgraded to `alembic_version` + `system_metadata`
- Web ESLint: PASS
- Web TypeScript: PASS
- Web production build: PASS — Next.js 16.3.8 static route build completed
- npm dependency audit: PASS — 0 vulnerabilities
- API liveness with PostgreSQL running: `GET /health` -> 200 + `X-Request-ID`
- API readiness with PostgreSQL running: `GET /ready` -> 200
- API readiness with PostgreSQL stopped: `GET /ready` -> 503 `{"status":"not_ready"}`
- PostgreSQL restored after the negative readiness test.

## Decisions passed / locked
- Security/tenant isolation remains highest priority.
- Web ERP is primary; LINE remains Phase 13 and reuses application use cases.
- PostgreSQL is authoritative; modular monolith remains the initial architecture.
- Shared DB/shared schema multi-tenancy requires strict tenant scoping.
- Inventory ledger is authoritative; posted inventory history is immutable.
- Host 72 remains control-plane only; all NOMOS development/runtime execution remains on host 73.
- Phase 1 supported Web runtime is Node.js 22.x; CI pins 22.23.3.
- Health means process liveness; readiness includes PostgreSQL dependency availability.

## Current blockers
- None for Phase 2.
- Platform safety gates may occasionally require a permitted single-command SSH pattern; this is an execution-tool constraint, not a NOMOS architecture blocker.

## In progress / not yet passed
- Phase 2 SaaS Platform Core has not started.
- Two preserved pre-sync stashes remain on host 73 from conflicting local scaffold work; do not drop them until reviewed. They are not part of the Phase 1 PASS source tree.

## NEXT ACTIONS — execute in this order

### NEXT 1 — Phase 2 tenant/organization persistence
Implement tenant, legal entity, branch, user and tenant membership persistence using Phase 0 ERD constraints, including same-tenant composite FK strategy and migrations.

### NEXT 2 — Phase 2 auth/RBAC/session context
Implement session/authentication foundation, server-derived tenant context, deny-by-default permissions and disabled membership/session behavior.

### NEXT 3 — Phase 2 audit/idempotency/outbox + isolation gate
Implement audit, idempotency and outbox foundations; add cross-tenant guessed-ID/read/update/delete/reference tests and RBAC matrix tests. Phase 2 passes only when the automated tenant-isolation/RBAC gate is green.

## Latest activity
- Phase 1 acceptance gate completed on host 73 and marked PASS.
- Node upgraded on host 73 to 22.23.3 to support the patched Next.js 16 line and eliminate dependency audit findings.
- PostgreSQL empty-database migration, positive/negative readiness behavior, API quality gates, Web lint/type/build and dependency audit were verified.
- Immediate next executable action: Phase 2 tenant/organization persistence on host 73.
