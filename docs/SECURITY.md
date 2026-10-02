# Security Baseline

## Core controls

- Deny-by-default authorization
- Strong tenant isolation
- Modern password hashing
- Secure session/token rotation and revocation
- Secrets through environment/secret management; never source control
- LINE webhook signature verification
- Rate limits for authentication and public webhook surfaces
- Strict request/schema validation
- Parameterized queries/ORM
- CSRF protection for cookie-authenticated state changes
- Secure headers and TLS in production
- Append-oriented audit for critical operations
- Dependency/container scanning in CI
- Backups with tested restores
- Least-privilege database/service accounts

## Threats to review for every feature

- cross-tenant data leakage
- broken object-level authorization
- privilege escalation
- duplicate/replay mutation
- race condition on stock
- injection
- SSRF/file/path misuse for integrations
- sensitive data in logs
- secret leakage
- unsafe deserialization
- mass assignment
- AI prompt/tool abuse when AI features exist

## Secrets

Examples:
- DATABASE_URL
- session/JWT signing secret
- LINE channel secret
- LINE channel access token
- Redis credentials
- cloud/storage credentials

Production secrets belong in a secret manager or platform secret store. Rotate compromised secrets and document ownership.

## Audit events

Record:
- tenant
- actor
- effective roles/permission context when useful
- action
- target
- structured before/after or change metadata where appropriate
- request/correlation ID
- channel
- timestamp
- result/failure code
- originating IP/user-agent only when justified and handled under privacy policy

Never log passwords, raw tokens, LINE channel secrets, session secrets or unnecessary personal data.

## Data protection

- TLS in transit
- encrypted storage/backups at infrastructure layer
- retention policy for audit/operational data
- export/deletion process designed before broad SaaS release
- production data must not be copied casually into development

## Security testing

CI and pre-release checks include:
- dependency scanning
- secret scanning
- static analysis where practical
- tenant-isolation integration tests
- webhook signature/replay tests
- authorization matrix tests
- input fuzz/negative cases for critical endpoints

## Incident readiness

Define owners for credential compromise, tenant data exposure, destructive stock bug and backup restore. Logs must support timeline reconstruction without storing secrets.