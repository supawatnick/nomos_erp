# Development Guide

## Local prerequisites

- Docker / Docker Compose
- Python toolchain required by apps/api
- Node.js package manager required by apps/web
- Git

Exact runtime versions should be pinned in the application manifests once source scaffolding is created.

## Local services

docker-compose.yml provides PostgreSQL and Redis dependencies. Application services can initially run on the host or be added to Compose when their Dockerfiles exist.

Copy .env.example to a local ignored env file and replace development-only values. Never commit real credentials.

## Suggested API structure

~~~
apps/api/
  app/
    api/
    application/
    domain/
    infrastructure/
    integrations/line/
    observability/
  migrations/
  tests/
~~~

## Suggested Web structure

~~~
apps/web/
  src/
    app/
    components/
    features/
    lib/api/
    lib/auth/
    i18n/
  tests/
~~~

## Testing layers

1. Domain unit tests
2. Application use-case tests
3. PostgreSQL repository integration tests
4. API contract/integration tests
5. LINE webhook/adapter tests
6. Selected end-to-end Web workflows
7. Cross-tenant and concurrency tests

## Required critical scenarios

- tenant isolation
- RBAC denial/allow matrix
- duplicate idempotency key
- duplicate LINE webhook
- two concurrent stock issues
- insufficient stock
- atomic transfer
- reversal/correction
- approval self/unauthorized denial
- approval state change before execution
- webhook signature failure
- audit creation

## Definition of Done

See AGENTS.md. No inventory mutation feature is complete with only happy-path API tests.