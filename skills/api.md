# API Skill

- Base path is /api/v1.
- Use stable resource/command names from docs/API.md.
- Protected calls require authenticated tenant context.
- Stock mutations require Idempotency-Key.
- Return a stable error envelope with machine code and request_id.
- Do not leak cross-tenant resource existence through error detail.
- Use cursor pagination for growing lists.
- Whitelist sort/filter fields.
- Serialize time in UTC ISO/RFC format.
- Preserve decimal precision in API schema/serialization.
- Breaking changes require a version or compatibility plan.
- Generate OpenAPI from FastAPI and treat it as a contract used by Web/LINE integrations/tests.