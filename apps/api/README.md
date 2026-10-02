# NOMOS API

Target: FastAPI modular monolith.

Suggested package structure:

~~~
app/
  api/                 # HTTP routers/schemas
  application/         # use cases, policies, transaction orchestration
  domain/              # entities/value objects/invariants
  infrastructure/      # DB repositories, queue, telemetry
  integrations/line/   # LINE adapter/client
migrations/
tests/
~~~

Implementation must follow AGENTS.md, docs/API.md, docs/DATABASE.md and relevant domain docs.

First implementation milestone:
1. settings/config validation
2. /health and /ready
3. PostgreSQL connection + migrations
4. auth/tenant context
5. RBAC
6. product/warehouse masters
7. inventory ledger use cases
8. audit/idempotency
9. LINE adapter
