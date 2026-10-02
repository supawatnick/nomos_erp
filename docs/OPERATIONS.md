# Operations Baseline

## Environments
Development executes on host 73 only. Staging and production are separate environments with separate credentials and data.

## Configuration
Configuration is environment-driven. Secrets are never committed. Production uses a secret-management mechanism and least-privilege service/database credentials.

## Database
Migrations are explicit controlled steps. Production replicas do not each auto-run migrations. Use expand/backfill/switch/contract for risky changes.

## Backup and recovery
Commercial readiness requires automated backups, point-in-time recovery where supported, off-site retention and recurring restore drills. RPO/RTO are defined for the sold service tier and demonstrated before commitments are made.

## Observability
Structured logs include request/correlation ID and safe tenant/actor/channel context. Monitor API latency/error rate, DB connections/slow queries/deadlocks, workers/outbox failures, inventory reconciliation, backup freshness and infrastructure capacity.

## Release
Build immutable application artifacts. Run migration compatibility checks and tests before deploy. Maintain rollback/forward-fix procedures and release notes for schema/behavior changes.

## Data
Production customer data is not copied casually into development. Imports are validated, previewable and auditable. Export/retention/deletion lifecycle is designed before broad commercial release.
