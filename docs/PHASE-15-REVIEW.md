# Phase 15 Review — Commercial Hardening

Status: **IN PROGRESS**

## Contract
Phase 15 must demonstrate, not merely describe:
- security review and dependency/secret gates;
- performance/load/concurrency acceptance;
- backup plus restore/PITR procedure and measured drill evidence;
- observability and alert targets;
- controlled upgrade/migration and rollback/forward-fix runbooks;
- incident readiness;
- end-to-end four-core reconciliation;
- explicit pilot SLA/SLO, RPO and RTO targets with evidence.

Phase 13 LINE remains DEFERRED / NOT PASS and is not a Phase 15 dependency.

## Pilot targets
- API availability target: 99.5% monthly for controlled pilot, excluding announced maintenance.
- Interactive API p95 target: <= 750 ms under the documented pilot smoke load for representative bounded reads.
- Server error-rate alert: >= 2% 5xx over 5 minutes.
- Database readiness: /ready must fail closed when DB is unavailable.
- Backup RPO target: <= 24 hours for baseline daily backup; PITR target <= 15 minutes where WAL archival is enabled by deployment.
- Restore RTO target: <= 60 minutes for the controlled pilot dataset/runbook.
- Reconciliation target: zero unexplained variance for inventory ledger/balance, AR/AP control and balanced GL; zero duplicate source financial postings.

## Evidence checklist
- [ ] security/dependency/secret gates green
- [ ] load/concurrency evidence
- [ ] backup/restore drill with measured RTO
- [ ] observability/alert contract
- [ ] upgrade/migration runbook
- [ ] incident runbook
- [ ] four-core reconciliation command/test
- [ ] final CI
- [ ] host 73 runtime sync and clean Git state
