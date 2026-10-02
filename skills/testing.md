# Testing Skill

Testing pyramid:
1. Domain unit tests
2. Application/service tests
3. DB/repository integration tests
4. API tests
5. LINE webhook/adapter tests
6. Selected Web end-to-end flows
7. Security/concurrency tests

Critical scenarios:
- tenant isolation by guessed IDs
- RBAC allow/deny matrix
- duplicate idempotency request
- conflicting idempotency payload
- duplicate LINE webhook
- concurrent stock issue
- insufficient stock
- atomic transfer
- reversal/adjustment
- approval authorization and self-approval rule
- approved request with changed stock before execution
- webhook signature failure
- audit/outbox creation

Tests must assert no partial writes after failure. Business-critical inventory code is not complete without these tests.