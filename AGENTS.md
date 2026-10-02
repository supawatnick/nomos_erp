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