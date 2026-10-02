# Backend Skill

When working on NOMOS API/backend:
- Use FastAPI with router/application/domain/infrastructure separation.
- Route handlers parse transport input, resolve trusted context and call a use case.
- Business rules, authorization policy and stock calculations do not live in route handlers.
- Use typed request/response models.
- Use explicit DB transactions for business operations.
- Enforce tenant and permission context in services/repositories.
- Validate referenced entity ownership in the same tenant.
- Make retriable mutations idempotent.
- Use exact decimal types for quantities/money.
- Map domain/application errors to stable API error codes.
- Create audit/outbox events within the business transaction where appropriate.
- Add unit tests for domain rules and integration tests for persistence/API.
- Keep OpenAPI current.
- LINE or AI adapters never bypass application services.