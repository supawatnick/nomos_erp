# Error Contract

API error codes are stable machine contracts; localized messages are presentation.

## Baseline categories
AUTHENTICATION_REQUIRED
SESSION_EXPIRED
PERMISSION_DENIED
RESOURCE_NOT_FOUND
VALIDATION_FAILED
CONFLICT
IDEMPOTENCY_CONFLICT
CONCURRENCY_CONFLICT
INSUFFICIENT_STOCK
INVALID_DOCUMENT_STATE
APPROVAL_REQUIRED
APPROVAL_STALE
DUPLICATE_RESOURCE
RATE_LIMITED
INTEGRATION_UNAVAILABLE
INTERNAL_ERROR

## Rules
- Never expose raw SQL, stack traces, secrets or cross-tenant existence details.
- details is structured and safe for clients.
- request_id is returned for support correlation.
- Validation details identify fields without exposing internals.
- New domain-specific codes are documented before clients depend on them.
