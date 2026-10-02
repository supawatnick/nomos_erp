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

## Host 72 -> Host 73 control path
Host 72 remains control/orchestration only. The verified development target is host 73 at `10.10.110.73`, hostname `nomos-erp`, repository `/root/nomos_erp`.

Verified control command shape from host 72:
`ssh -i /root/.ssh/ntap_office_demo_ed25519 -o BatchMode=yes root@10.10.110.73 <command>`

On 2026-10-02, a control-plane SSH task running `hostname` completed with exit code 0 and returned `nomos-erp`. If the shell task observation path is safety-gated, use the durable task status/result interface to inspect the already-started task rather than treating this as an SSH/network/key failure. Do not move NOMOS workloads to host 72 as a workaround.
