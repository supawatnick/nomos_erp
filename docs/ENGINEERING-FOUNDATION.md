# Phase 1 Engineering Foundation

## Runtime baseline
Development execution host: host 73 (`nomos-erp`) only.

Verified baseline:
- Ubuntu 24.04 family (Noble repositories)
- Node.js 18.19.1
- npm 9.2.0
- Python 3.12.3
- Git 2.43.0
- Docker Engine 29.1.3
- Docker Compose 2.40.3

## Structure
- `apps/web`: Next.js + TypeScript Web shell.
- `apps/api`: FastAPI API with configuration, request ID/logging, health/readiness and Alembic.
- `apps/worker`: worker process skeleton.
- `docker-compose.yml`: PostgreSQL and Redis development dependencies.
- `.github/workflows/ci.yml`: API/Web/migration/security gates.

## Configuration
Copy `.env.example` to a local ignored `.env`. Real secrets must never be committed. The API requires `DATABASE_URL`; missing required configuration fails application startup.

## Health model
- `GET /health`: process liveness only.
- `GET /ready`: dependency readiness; returns 503 if PostgreSQL cannot be reached.

## Clean boot
On host 73:
1. `docker compose up -d postgres redis`
2. `python3 -m venv .venv`
3. `.venv/bin/pip install -e './apps/api[dev]'`
4. `cd apps/api && DATABASE_URL=postgresql+psycopg://nomos:change-me-local-only@localhost:5432/nomos ../../.venv/bin/alembic upgrade head`
5. `cd apps/web && npm ci`
6. Run API with `DATABASE_URL=... ../../.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000`.
7. Run Web with `npm run dev`.

## Verification gates
API: Ruff, mypy, pytest, Alembic empty-database upgrade.
Web: ESLint, TypeScript, Node test runner, Next production build.
CI also runs a repository secret scan.
