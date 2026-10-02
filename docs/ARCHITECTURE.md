# Architecture

## Context

NOMOS ERP is a multi-tenant SaaS ERP with Web and LINE as primary interaction channels.

~~~
Browser / Next.js -----\
                        -> FastAPI -> Application Use Cases -> Domain
LINE Messaging API ----/                 |                 |
                                          |                 -> Policies/invariants
                                          v
                                      Repositories
                                          |
                                     PostgreSQL
                                          |
                           Outbox / Queue / Workers -> LINE notifications
~~~

## Layers

### Presentation/adapters
- Next.js pages/components
- FastAPI routers and schemas
- LINE webhook parsing, reply formatting and postbacks
- worker entrypoints

Responsibilities: validate transport shape, authenticate/resolve context, invoke a use case, map result/error.

### Application
- use-case orchestration
- authorization policy invocation
- database transaction boundary
- idempotency
- approval/confirmation orchestration
- domain event/outbox creation

### Domain
- inventory rules and invariants
- transaction state rules
- value objects for quantity/money
- approval policy concepts
- business validation independent of HTTP/LINE

### Infrastructure
- PostgreSQL repositories
- Redis/queue adapters
- LINE client
- email/notification adapters if added
- telemetry, object storage and secret manager adapters

## Key architectural rules

- No business rule is duplicated by channel.
- No external identifier is trusted without tenant/ownership validation.
- Database transactions wrap stock-changing use cases.
- Asynchronous side effects happen after durable business commit, preferably through an outbox pattern.
- Workers must be idempotent.
- Derived/cached inventory balance is never more authoritative than the ledger.

## Request flow: stock mutation

1. Authenticate actor.
2. Resolve tenant membership and trusted context.
3. Validate request schema.
4. Claim/check idempotency key.
5. Authorize permission and referenced resources.
6. Determine whether confirmation/approval is required.
7. Start database transaction.
8. Lock/read required stock state using the documented concurrency strategy.
9. Validate domain invariants.
10. Write transaction header and lines.
11. Write audit/outbox records.
12. Commit.
13. Return result; process notifications asynchronously.

## Failure model

- Validation: 4xx structured error, no mutation.
- Authorization: deny without revealing cross-tenant resource details.
- Concurrency conflict: retryable conflict response when safe.
- External LINE/notification failure: business transaction remains committed; retry outbox delivery.
- Database failure: transaction rolls back atomically.

## Deployment evolution

Phase 1 can run Web, API, worker, PostgreSQL and Redis with Docker Compose. Production services should remain stateless where practical so Kubernetes adoption does not require rewriting business logic.