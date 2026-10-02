# Security Skill

For every feature, threat-model tenant leakage, privilege escalation, replay/duplicate requests, injection and sensitive-data exposure.

Rules:
- deny by default
- authorize server-side
- validate ownership and tenant on referenced IDs
- verify external webhook authenticity
- redact secrets from logs
- use secure dependencies and pinned/managed versions
- audit critical mutations
- never expose arbitrary SQL execution to LINE/AI
- AI output is untrusted input until validated by deterministic application logic
