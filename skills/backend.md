# Backend Skill

When working on NOMOS backend:
- Use FastAPI with clear router/application/domain/infrastructure separation.
- Keep business rules out of route handlers.
- Use typed request/response models.
- Use DB transactions for business operations.
- Enforce tenant and permission context in services/repositories.
- Make retriable mutations idempotent.
- Add unit tests for domain rules and integration tests for persistence/API.
- Generate/maintain OpenAPI contracts.
- Do not allow LINE or AI adapters to bypass application services.
