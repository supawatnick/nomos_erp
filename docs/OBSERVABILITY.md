# Observability

NOMOS must make business failures diagnosable without exposing secrets.

## Structured logs

Include where relevant:
- timestamp
- service
- environment
- request_id/correlation_id
- tenant_id (safe internal identifier)
- actor_id
- channel
- route/use_case
- outcome/error_code
- latency

Do not log raw passwords, tokens, LINE secrets or full sensitive payloads.

## Metrics

API:
- request count/latency/error rate
- auth failures/rate limits
- DB pool saturation

Inventory:
- posted transaction count by type
- business validation failures
- insufficient-stock conflicts
- idempotency replays/conflicts
- approval pending/executed/expired

LINE:
- webhook received/verified/rejected
- duplicate webhook count
- processing latency
- reply/push delivery failures
- queue retry/dead-letter count

Workers:
- queue depth
- job latency
- retry/failure/dead-letter

## Tracing

Propagate correlation context from Web/API/LINE through application, DB calls and background events where supported.

## Alerts

Start with actionable alerts:
- elevated API 5xx
- database unavailable/saturated
- webhook signature failure spike
- queue backlog/dead-letter growth
- backup failure
- scheduled restore-test failure
- unusual authorization denial spike if meaningful

Avoid alerting on every expected business validation error.

## Audit vs logs

Audit log is business/security evidence and has stronger retention/integrity requirements.
Operational logs are diagnostic telemetry.
Do not rely on ephemeral application logs as the only audit trail.

## Phase 15 controlled-pilot targets
- Availability target: 99.5% monthly excluding announced maintenance.
- Representative bounded-read p95 target: <=750 ms under the documented pilot smoke load.
- Page on sustained >=2% HTTP 5xx over 5 minutes.
- Integrity alert on any unexplained inventory ledger/balance variance, unbalanced GL or duplicate financial source posting.
- Monitor AR/AP control reconciliation, outbox age/failures and backup freshness.
- Backup freshness alert threshold follows the sold RPO; baseline daily-backup RPO is <=24h, and deployments selling <=15m RPO require tested WAL/PITR.

These are controlled-pilot acceptance thresholds, not a public SLA until production telemetry demonstrates them.
