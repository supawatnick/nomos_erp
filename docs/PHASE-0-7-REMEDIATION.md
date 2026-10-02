# Phase 0–7 Remediation Audit

Status: **OPEN — BLOCKS PHASE 8**

Purpose: reconcile implemented behavior against the authoritative Phase 0–7 contracts before Procurement begins. This remediation is corrective closure work and does not change the Phase 8 scope.

## Audit findings

### R-01 — Phase 5 administration Web gap
The Phase 5 acceptance contract requires Users/Roles/Audit Web surfaces. The repository has Phase 2 RBAC/audit persistence and permissions but no tenant-safe administration API/Web surfaces for these workflows.

Required closure:
- tenant-scoped Users read surface;
- tenant-scoped Roles/permission read surface;
- tenant-scoped Audit viewer;
- server-side permission enforcement (UI is never authority);
- Web routes and navigation using the approved Web Design Contract;
- API/Web acceptance tests including cross-tenant non-disclosure.

### R-02 — Phase 6 import lifecycle gap
The Phase 6 acceptance contract requires PRODUCT/master and OPENING_STOCK import lifecycle. Current Phase 6 implementation covers stock count, reorder and reports but not the import lifecycle defined by docs/IMPORT-OPENING-STOCK.md.

Required closure:
- staged import batch persistence and row-level normalized/error/result data;
- lifecycle validation with no business side effects;
- explicit atomic commit;
- PRODUCT and OPENING_STOCK minimum executable import types;
- opening stock commit only through Phase 4 Inventory posting (never direct balance writes);
- replay-safe committed batch behavior;
- permission, tenant-isolation, audit and outbox evidence;
- Web preview/commit workflow;
- required PostgreSQL and Web tests.

### R-03 — stale project status/evidence
PROJECT-STATUS.md contains obsolete Phase 4-not-started and terminal-CI-pending statements after later phases passed. Phase review/status evidence must be reconciled to completed CI evidence.

### R-04 — Web design conformance regression
Before closure, all added remediation surfaces and existing Phase 5–7 operational routes must be checked against docs/WEB-DESIGN-CONTRACT.md. Fix material contract deviations; do not turn ERP screens into marketing UI.

## Closure gate
Phase 8 remains blocked until:
1. R-01 through R-04 are resolved;
2. migrations upgrade from clean PostgreSQL;
3. full API PostgreSQL suite passes;
4. Ruff and mypy pass;
5. pip audit passes;
6. Web lint/typecheck/tests/build and npm high audit pass;
7. gitleaks passes;
8. final GitHub Actions run for the remediation documentation commit is green;
9. PROJECT-STATUS.md and Phase reviews contain no contradictory stale state.

After closure, mark this document **PASS — PHASE 0–7 BASELINE CLEAN — READY FOR PHASE 8** and record exact CI evidence.
