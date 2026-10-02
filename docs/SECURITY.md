# Security Baseline

- Least privilege RBAC
- Strong tenant isolation
- Password hashing using an approved modern password hashing scheme
- Secure session/token handling
- Secrets only via environment/secret manager; never commit them
- LINE webhook signature verification
- Rate limiting for authentication and public webhook surfaces
- Input/schema validation
- Parameterized DB access/ORM
- CSRF protection where cookie-based flows require it
- Secure headers and TLS in production
- Immutable/append-oriented audit records for critical operations
- Dependency and container scanning in CI
- Backups with tested restore procedures

## Audit events
Record actor, tenant, action, target, before/after or structured change metadata where appropriate, request/correlation ID, channel (WEB/LINE/API), timestamp and result.

Never log passwords, tokens, LINE channel secrets, session secrets or unnecessary personal data.
