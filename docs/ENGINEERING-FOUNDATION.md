# Phase 1 Engineering Foundation

Verified on host 73 only: Ubuntu 24.04, Node.js 18.19.1, npm 9.2.0, Python 3.12.3, Docker 29.1.3, Docker Compose 2.40.3, PostgreSQL 17 container, Git 2.43.0.

Host 72 is control/orchestration only.

## Clean boot
1. Copy `.env.example` to `.env` with development-only values.
2. `docker compose up -d postgres`.
3. `python3 -m venv .venv && .venv/bin/pip install -r apps/api/requirements.txt`.
4. From `apps/api`, run Alembic upgrade head and uvicorn on port 8000.
5. From `apps/web`, run `npm ci` then `npm run dev`.

Liveness is `/health`; readiness is `/ready` and returns 503 when PostgreSQL is unavailable. Ports: PostgreSQL 5432, API 8000, Web 3000. Redis 6379 is reserved but not required in Phase 1.
