# NOMOS ERP Engineering Instructions

This repository is the source of truth for NOMOS ERP.

## Non-negotiable principles
1. Inventory is ledger-based. Never silently mutate stock balances.
2. Every business record is tenant-scoped.
3. Web and LINE use the same application/service layer.
4. LINE never writes directly to the database.
5. Every stock-changing operation is authenticated, authorized, validated, idempotent where appropriate, and auditable.
6. High-impact actions require explicit confirmation and configurable approval.
7. AI may interpret intent, but deterministic services validate and execute actions.
8. Monetary and quantity calculations use exact decimal types, never binary floating point.
9. Database migrations are versioned and reversible where practical.
10. Tests accompany business-critical behavior.

## Initial stack
- Web: Next.js + TypeScript
- API: Python + FastAPI
- Database: PostgreSQL
- Cache/queue: Redis when needed
- Local runtime: Docker Compose
- Scale target: Kubernetes
- LINE: LINE Messaging API webhook

## Repository target layout
```
apps/
  web/
  api/
docs/
skills/
infra/
tests/
```

Before implementing a module, read its relevant document under `docs/` and skill under `skills/`. Update documentation when architecture or business rules change.
