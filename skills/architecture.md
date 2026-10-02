# Architecture Skill

- Preserve adapter -> application -> domain -> infrastructure boundaries.
- Web, LINE and AI must invoke shared application use cases.
- Keep external SDK types out of domain code.
- Define transaction boundaries in the application layer.
- Use an outbox/worker for non-transactional side effects that must follow committed business changes.
- Workers are idempotent and tenant-aware.
- Prefer a modular monolith for MVP; split services only for a measured operational/domain reason.
- Do not introduce a distributed system merely to match a diagram.
- Record important irreversible architecture choices in docs when introduced.