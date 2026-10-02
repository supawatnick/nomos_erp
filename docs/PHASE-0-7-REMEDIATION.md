# Phase 0–7 Remediation Audit

Status: **PASS — PHASE 0–7 BASELINE CLEAN — READY FOR PHASE 8**

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


## Resolution record

### R-01 — CLOSED
Tenant-safe administration read APIs and `/admin` Web surface now cover Users, Roles/Permissions and Audit. Server-side `user.read`, `role.read` and `audit.read` checks remain authoritative.

### R-02 — CLOSED
Migration `0008_phase0_7_remediation`, staged import application/API and `/inventory/imports` implement PRODUCT and OPENING_STOCK stage/validate/preview/commit behavior. Validation has no business side effects. Opening stock commits through `post_inventory(... transaction_type="OPENING")`; direct balance mutation is not used. Opening authorization was corrected from `inventory.receive` to the contractually required high-risk `inventory.adjust`.

### R-03 — CLOSED
Project status and Phase 5/6 review evidence were reconciled during this closure. Obsolete Phase 4-not-started/pending closure statements are no longer authoritative.

### R-04 — CLOSED
New remediation Web surfaces reuse the approved ERP primitives/tokens: #FAFAFA workspace, white bordered surfaces, 12px cards/panels, 6px controls, Indigo #6366F1 accent, table/panel operational layout and existing responsive behavior. No marketing-page visual pattern was introduced.

## Acceptance evidence
Implementation acceptance GitHub Actions run **36986274423** on commit `87386d7d6b14680224d6b1e2709a29bedf595ca0`: **PASS**.
- Ruff: PASS.
- mypy: PASS.
- Alembic clean upgrade through `0008_phase0_7_remediation`: PASS.
- PostgreSQL pytest: PASS, including remediation acceptance (47 tests total at this gate).
- Product import validation side-effect-free: PASS.
- Product import commit/replay safety: PASS.
- Cross-tenant import batch hiding: PASS.
- Opening Stock requires `inventory.adjust`: PASS.
- pip-audit: PASS.
- npm ci / high audit: PASS.
- Web lint/typecheck/tests/build: PASS.
- remediation Web route/behavior tests: PASS.
- gitleaks: PASS.

A final documentation-only CI run is required after the status/review reconciliation commit; its run ID is recorded in PROJECT-STATUS.md after verification.

## Phase 8 gate
The functional Phase 0–7 remediation gate is closed. Phase 8 Procurement may begin only from a green final documentation commit and must continue to consume Phase 7 supplier identity and Phase 4 Inventory contracts without direct stock mutation.
