# Incident Readiness Runbook

## Severity
SEV-1: tenant isolation/security breach, financial/inventory integrity risk, broad outage or unrecoverable write path.
SEV-2: material degraded service, delayed outbox/integration, partial module outage.
SEV-3: localized defect with safe workaround.

## Response
1. Assign incident commander and timestamp.
2. Preserve request/correlation IDs, affected tenant IDs and safe logs; never copy secrets into incident notes.
3. Contain: disable unsafe write path or suspend affected tenant/service when integrity is at risk.
4. Diagnose using API 5xx/latency, DB connections/slow queries/deadlocks, outbox backlog, backup freshness and reconciliation.
5. Recover via known-good artifact/forward-fix/restore runbook.
6. Run inventory + finance + AR/AP reconciliation before declaring data-integrity recovery.
7. Communicate impact and recovery facts; do not guess.
8. Produce post-incident actions with owner and deadline.

## Alerts
Page for sustained >=2% 5xx over 5 minutes, readiness failure, backup freshness beyond sold RPO, reconciliation variance, material outbox backlog, or database capacity/deadlock thresholds defined by deployment.
