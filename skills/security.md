# Security Skill

Threat-model every feature for tenant leakage, broken object authorization, privilege escalation, replay/duplicate mutation, race conditions, injection and sensitive-data exposure.

Rules:
- deny by default
- authorize server-side
- validate tenant/ownership for referenced IDs
- verify external webhook authenticity
- use secure session/token handling
- apply CSRF controls when cookies authenticate state changes
- rate-limit exposed authentication/webhook surfaces
- redact secrets from logs
- use least-privilege service/database credentials
- scan dependencies and secrets in CI
- audit critical mutations/security changes
- never expose arbitrary SQL/file/system tools to LINE/AI
- AI output is untrusted input until deterministic validation
- production data is not casually copied into development