# DevOps Skill

- Local dependencies run through Docker Compose.
- Production application services are containerized/stateless where practical.
- Configuration uses environment variables; secrets use secret management.
- CI gates: lint, type check, unit/integration tests, migration check, secret/dependency scan and container build when containers exist.
- Database migrations are controlled deployment steps.
- Health/readiness endpoints are required.
- Structured logs carry request/correlation IDs.
- Metrics/tracing cover API, DB, workers, LINE and critical business failures.
- Backups require periodic restore tests.
- Prefer managed PostgreSQL in production where appropriate.
- Use backward-compatible deployment/migration patterns.
- Introduce Kubernetes only when operational needs justify it; business logic must not depend on Kubernetes.