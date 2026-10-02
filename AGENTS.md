# NOMOS ERP Engineering Instructions

This repository is the engineering and product source of truth for NOMOS ERP.

## Priority order

When instructions conflict, use this order:
1. Security and tenant isolation
2. Domain invariants and auditability
3. API/data contracts
4. Product requirements
5. Channel/UI convenience

## Non-negotiable principles

1. Inventory is ledger-based. Never silently mutate a stock balance as the source of truth.
2. Every tenant-owned business record carries tenant context and every query is tenant-scoped.
3. Web, LINE and future AI use the same application/service layer.
4. LINE, UI code and AI adapters never write directly to the database.
5. Stock-changing operations are authenticated, authorized, validated, transactional and auditable.
6. Retriable mutations use idempotency protection.
7. High-impact actions require explicit confirmation and configurable approval.
8. AI may interpret intent, but deterministic services validate and execute actions.
9. Money and fractional quantities use exact decimal types, never binary floating point.
10. Posted transactions are immutable in normal operation; corrections use reversal or compensating entries.
11. Database migrations are versioned and reviewed. Destructive migrations require an explicit rollout/rollback plan.
12. Tests accompany business-critical behavior.
13. Never expose secrets, arbitrary SQL, unrestricted file access or internal admin tools to LINE/AI.
14. Never log credentials, tokens, secrets or unnecessary personal data.

## Infrastructure control-plane rule

- Host 72 is the NOMOS control/orchestration host only.
- Do not install application runtimes, databases, project dependencies, build tools, Docker workloads, or NOMOS application services on host 72.
- Do not use host 72 as a development, test, staging, or production execution target.
- Host 72 may hold the ntap-office/MCP control plane and use it to instruct other hosts.
- Workloads must execute on their designated target hosts. For the current NOMOS ERP test/development environment, host 73 is the execution target.
- Git operations for a target host should be performed by that target host using its own credentials whenever possible; host 72 must not act as a Git credential proxy for host 73.
- If a required capability is missing on a target host, install or configure it on the target host, not on host 72.
- Any exception to this rule requires explicit user approval.

## Mandatory pre-work procedure

Before starting any NOMOS ERP task, read this `AGENTS.md` first and follow it as the project operating contract.

- Development work for NOMOS ERP must run on host 73 (`nomos-erp`) under `/root/nomos_erp`.
- This includes editing code, Git operations, dependency installation, builds, tests, migrations, Docker/Compose workloads, databases, Redis, and application services.
- Host 72 is control/orchestration only. It may issue commands to host 73, but NOMOS development workloads must not execute on host 72.
- Before making changes, confirm the intended command or operation will execute on host 73.
- Read any additional relevant files under `docs/` and `skills/` before implementing the affected module.

## Target architecture

- Web: Next.js + TypeScript
- API: Python + FastAPI
- Database: PostgreSQL
- Queue/cache: Redis when required
- Local: Docker Compose
- Production: containerized; Kubernetes is an evolution path
- External channel: LINE Messaging API

## Required code boundaries

API route/controller -> application use case -> domain -> repository/integration adapters.

A route may parse input and map errors, but must not contain inventory calculations, authorization policy or transaction orchestration.

## Required context for protected operations

Every protected use case receives a trusted context containing at least:
- actor user ID
- tenant ID
- roles/permissions
- request/correlation ID
- channel (WEB, LINE, API, WORKER)
- locale/timezone when presentation depends on it

Tenant identity must be derived from authenticated membership, never trusted from arbitrary request text/body.

## Definition of Done

A feature is not complete until:
- acceptance criteria are met
- authorization and tenant isolation are enforced server-side
- domain invariants are enforced
- migrations are included when schema changes
- unit/integration tests cover critical behavior
- negative/error cases are tested
- audit events exist for critical mutations
- API/OpenAPI and docs are updated
- logs/metrics are sufficient to operate the feature
- no secret or unsafe default is introduced

Before implementing a module, read the relevant file under docs/ and skill under skills/. Update those documents when behavior changes.

## Planning source of truth

- `docs/MASTER-PLAN.md` is the authoritative phase/release plan.
- Phase 0 architecture contracts include `docs/DOMAIN.md`, `docs/DATA-MODEL.md`, `docs/DOCUMENT-LIFECYCLE.md`, `docs/AUTHORIZATION.md`, `docs/ACCOUNTING-BOUNDARY.md`, `docs/MODULES.md`, `docs/NUMBERING.md`, `docs/ERROR-CODES.md`, and `docs/OPERATIONS.md`.
- Do not start a later implementation phase merely because its UI is understood; satisfy the prior phase exit gate first.


## Mandatory execution-status procedure

`PROJECT-STATUS.md` is the operational handoff and next-action source of truth.

Before every NOMOS work session:
1. Read `AGENTS.md`.
2. Read `PROJECT-STATUS.md`.
3. Read the docs/skills relevant to the current next action.

At the end of every meaningful work session, update `PROJECT-STATUS.md` with:
- work completed
- checks/exit gates that passed
- blockers or failures
- work still in progress
- decisions that became authoritative
- ordered NEXT ACTIONS, with NEXT 1 being the actual next executable task
- latest meaningful result/handoff

Do not leave a session without a clear next action unless the project is complete or explicitly blocked pending user/external input.
