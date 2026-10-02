# Deployment and Operations

## Environments

At minimum:
- local
- staging
- production

Production credentials/data are isolated from staging.

## Services

Initial deployable units:
- web
- api
- worker when async jobs exist
- PostgreSQL
- Redis when queue/cache exists

Managed PostgreSQL is preferred for production when available. Application containers should be stateless except for explicitly managed storage.

## Configuration

Use environment variables/config files for non-secret configuration and a secret store for credentials. Validate required configuration at startup and fail fast on missing critical values.

## Database migration

Deployment order should make schema and application versions compatible. Prefer backward-compatible migrations.

Risky change pattern:
1. expand schema
2. deploy compatible code
3. backfill
4. switch reads/writes
5. verify
6. contract old schema later

Never run destructive migration automatically from every API replica.

## Health

- /health: process alive
- /ready: dependencies/migration compatibility sufficient to serve traffic

Readiness should not create heavy database load.

## Backups

Production baseline:
- automated database backups
- defined retention
- encrypted backup storage
- restoration procedure
- scheduled restore test
- documented RPO/RTO target before production pilot

A backup is not considered reliable until restore has been tested.

## Rollback

Application rollout must support reverting to the previous compatible version. If a data migration is not reversible, the deployment plan must specify forward recovery.

## Kubernetes evolution

When needed, add:
- Deployments for web/api/worker
- Services/Ingress
- ConfigMaps/Secrets integration
- readiness/liveness probes
- resource requests/limits
- HPA where justified
- migration Job
- NetworkPolicy
- PodDisruptionBudget for critical services

Keep business logic independent from the orchestrator.