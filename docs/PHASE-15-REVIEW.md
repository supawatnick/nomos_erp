# Phase 15 Review — Commercial Hardening

Status: **FAILED / CLEAN-ROOM REMEDIATION — BACKEND HARDENING VERIFIED, WEB ACCEPTANCE INVALIDATED**

## Sequencing
Phase 13 LINE remains **DEFERRED / NOT PASS** by product decision. Phase 15 does not claim Integrated Channel ERP V1 and does not depend on LINE.

## Delivered and demonstrated
- Security gates: Ruff, mypy, pip dependency audit, npm high-severity audit and full-history Gitleaks.
- PostgreSQL/Alembic full-suite regression.
- Phase 15 cross-core reconciliation snapshot:
  - Inventory posted ledger vs on-hand projection variance.
  - GL debit/credit balance.
  - Duplicate non-reversal financial source effects.
  - AR/AP open subledger amounts exposed for reconciliation evidence.
- Representative reconciliation bounded-read smoke p95 acceptance target <=750 ms.
- Concurrent inventory no-oversell hardening acceptance.
- Existing Finance balance invariants revalidated under hardening suite.
- Production upgrade/recovery runbook with controlled Alembic, compatibility, rollback/forward-fix and restore procedure.
- Incident severity/containment/recovery/reconciliation runbook.
- Observability signals and controlled-pilot alert/SLO thresholds.
- Real host 73 PostgreSQL logical backup/restore drill.

## Controlled pilot targets
- Availability: 99.5% monthly excluding announced maintenance.
- Representative bounded-read p95: <=750 ms under documented smoke acceptance.
- HTTP 5xx alert: sustained >=2% over 5 minutes.
- Baseline daily-backup RPO target: <=24h.
- Deployments selling <=15m RPO require continuous WAL/PITR and a timestamp recovery drill.
- Controlled-pilot restore RTO target: <=60m.
- Integrity target: zero unexplained Inventory variance, zero unbalanced journals and zero duplicate source financial postings.

These are controlled-pilot acceptance targets, not a public production SLA until production telemetry supports them.

## Backup/restore drill — host 73
Executed 2026-10-02 against the host 73 PostgreSQL 17 container:
- `pg_dump -Fc` of `nomos` produced an 829K custom-format backup.
- Restored into isolated validation database `nomos_phase15_restore`.
- Restored Alembic version verified: `0019_phase14_commercial_saas`.
- Measured dump + create + restore + version verification: **2 seconds**.
- Result: **PASS**, comfortably inside the <=60 minute controlled-pilot RTO target for the current development/pilot dataset.

This logical drill proves the current dataset restore procedure. It does not claim a <=15 minute PITR RPO; that requires deployment-level WAL archival and timestamp recovery evidence.

## CI evidence
Phase 15 implementation gate: GitHub Actions run `37017699870` — **SUCCESS**.
- Ruff: PASS.
- mypy: PASS.
- Alembic through 0019: PASS.
- PostgreSQL/API pytest: **82 passed**.
- pip-audit: PASS.
- npm audit high: PASS.
- Web lint/typecheck/tests/build: PASS.
- full-history Gitleaks: PASS.

## Host 73 evidence
- Repository synchronized to implementation baseline.
- PostgreSQL/API suite: **82 passed**.
- Git working tree clean.
- Git divergence: **0 ahead / 0 behind**.
- Historical three stashes preserved and untouched.

## Exit gate
**CODE/HARDENING PASS; DEPLOYMENT ACCEPTANCE OPEN.** Security, concurrency, restore, observability/alerts, migration/recovery, incident readiness and cross-core integrity checks are demonstrated at the current pilot dataset scale. A later runtime inspection found that no Next.js Web service was listening on host 73 and API processes were bound to localhost only; therefore browser-accessible commercial-pilot readiness was previously overstated.

Commercial pilot scope excluding LINE can proceed. The repository must continue to state Phase 13 as DEFERRED / NOT PASS; Integrated Channel ERP V1 and full 0–15 sequential completion cannot be claimed until Phase 13 is completed.

## Deployment acceptance correction — 2026-10-02
Runtime inspection after the original closure found PostgreSQL/Redis running, API uvicorn listeners only on 127.0.0.1:8000 and 127.0.0.1:8010, and **no Next.js Web listener**. CI production-build success is not deployment evidence.

The gate is reopened until all are proven:
- production Web service running and restartable;
- one canonical API service running and restartable;
- browser entry URL reachable on the host network;
- same-origin proxy routes Web API requests correctly;
- /health and /ready succeed through the deployed entry point;
- login and representative ERP pages are exercised against the deployed runtime;
- runtime URL/configuration is recorded in HOST-73-RUNBOOK.md.

Deployment correction gate is now closed by docs/WEB-RUNTIME-ACCEPTANCE.md. Verified private-network entry URL: **http://10.10.110.73/**. Web/API services are restartable, same-origin routing is active, health/readiness pass through the browser entry point, and representative ERP routes return HTTP 200.


## Clean-room invalidation — 2026-10-02
The prior Phase 15 PASS is withdrawn. Backend hardening evidence remains valid where rerun against PostgreSQL (82 passed, 0 skipped), but Web/browser acceptance was materially overstated.

The specific errors, root cause and mandatory prevention gates are recorded in `docs/WEB-RUNTIME-ACCEPTANCE.md`. In particular, `npm test` had no NOMOS-owned tests to discover, HTTP 200 route checks were mistaken for workflow acceptance, and runtime defects reached the deployed environment despite prior PASS language.

Phase 15 MUST remain FAILED / REMEDIATION until a non-zero browser/Web suite and deployed Host 73 critical-flow E2E pass. Historical CI/build success cannot override this gate.
