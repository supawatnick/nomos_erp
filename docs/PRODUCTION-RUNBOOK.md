# Production Upgrade and Recovery Runbook

## Release
1. Confirm CI, dependency audit, secret scan and reconciliation are green.
2. Take/verify a fresh database backup and record its timestamp/checksum.
3. Deploy immutable application artifact compatible with both pre/post migration schema.
4. Run Alembic once from a controlled release job, never independently on replicas.
5. Run readiness, smoke and reconciliation checks.
6. If application-only regression occurs, roll back the application artifact while schema remains backward compatible.
7. For migration regression, prefer forward-fix. Destructive schema rollback requires explicit reviewed recovery plan and restored backup validation.

## PostgreSQL backup/restore
Baseline logical drill:
`pg_dump --format=custom --no-owner --no-acl "$DATABASE_URL" > nomos.dump`
Restore into an empty validation database:
`pg_restore --clean --if-exists --no-owner --no-acl --dbname "$RESTORE_DATABASE_URL" nomos.dump`
Then run Alembic current, full acceptance and reconciliation against the restored database.

Production deployments that sell <=15 minute RPO must additionally enable continuous WAL archiving/PITR in the managed PostgreSQL layer and test recovery to a timestamp between base backups.

## Pilot targets
Daily verified backup gives baseline RPO <=24h. PITR deployments target <=15m RPO. Controlled-pilot restore RTO target <=60m. Never claim these targets from configuration alone: record each drill's measured result in Phase 15 evidence.

## Rollback / forward fix
Never delete posted ERP history to repair a release. Prefer application rollback for compatible changes, forward migration for schema defects, and restore only for disaster recovery with explicit incident command.
