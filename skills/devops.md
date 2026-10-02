# DevOps Skill

- Local development via Docker Compose.
- Production services should be containerized and stateless where practical.
- Configuration through environment variables; secrets through secret management.
- CI: lint, type check, unit/integration tests, dependency scan, container build.
- Database migrations run as controlled deployment steps.
- Health/readiness endpoints are required.
- Structured logs with request/correlation IDs.
- Metrics and tracing should cover API latency/errors, DB, workers, LINE webhook processing and business failures.
- Backups require periodic restore tests.
- Kubernetes manifests/Helm can be introduced when operational scale justifies it.
