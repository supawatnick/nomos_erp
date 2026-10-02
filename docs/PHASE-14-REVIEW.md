# Phase 14 Review — Commercial SaaS Layer

Status: **PASS — PHASE 14 COMPLETE**

## Sequencing decision
Phase 13 LINE was explicitly deferred by product decision on 2026-10-02. It remains **DEFERRED / NOT PASS**. Phase 14 has no dependency on LINE.

## Contract basis
- docs/MASTER-PLAN.md Phase 14
- docs/AUTHORIZATION-MATRIX.md
- docs/API-AUDIT-CONTRACT.md
- docs/WEB-DESIGN-CONTRACT.md
- Phase 2 tenant/RBAC platform contracts

## Delivered
- SaaS plan catalog with trial and retention policy.
- Per-plan feature entitlements and optional exact integer limits.
- One tenant subscription with TRIAL/ACTIVE/SUSPENDED/CANCELLED lifecycle.
- Tenant usage counters with locked server-side limit enforcement.
- Repeatable/idempotent tenant commercial provisioning.
- Explicit entitlement guard independent from RequestContext RBAC.
- Subscription lifecycle audit evidence.
- Cancellation records retention deadline instead of destructive tenant deletion.
- Tenant export request lifecycle with tenant-scoped requester identity and audit.
- Commercial API for subscription visibility, lifecycle transitions and entitlement-gated export.
- Plan & Subscription Web surface.
- API version advanced from Core ERP 0.12.0 to 0.14.0; 0.13.0 is intentionally not claimed because Phase 13 is deferred.

## Security boundary
Entitlement and RBAC are independent gates:
- entitlement answers whether the tenant's commercial plan enables a feature/limit;
- RBAC answers whether this authenticated tenant user may perform the operation;
- neither grants or substitutes for the other.

Suspended/cancelled/expired-trial tenants fail entitlement checks even if a user retains an ERP permission.

## Acceptance
`apps/api/tests/test_phase14_commercial.py` proves:
- repeatable provisioning returns the same tenant subscription;
- bounded entitlement usage rejects an increment over the commercial limit;
- a tenant with RBAC permission can still be denied by suspended commercial state;
- commercial entitlement does not give a user `tenant.export` RBAC permission;
- cancellation creates retention metadata;
- export request is tenant scoped.

## Persistence
Migration `0019_phase14_commercial_saas`:
- saas_plans
- saas_plan_entitlements
- saas_subscriptions
- saas_usage_counters
- saas_exports
- subscription.read / subscription.manage / tenant.export permissions.

## CI evidence
Phase 14 implementation gate: GitHub Actions run `37013634604` — **SUCCESS**.
- Ruff: PASS.
- mypy: PASS.
- Alembic through 0019: PASS.
- PostgreSQL/API pytest: **78 passed**.
- pip-audit: PASS.
- npm audit high: PASS.
- Web lint/typecheck/tests/build: PASS.
- full-history Gitleaks: PASS.

## Exit gate
**PASS.** Entitlement is demonstrably separate from RBAC and tenant commercial provisioning is repeatable. Trial/suspend/cancel, limits, export request and retention metadata are enforced/persisted server-side.

## Handoff
Run final documentation CI and host 73 synchronization. Then Phase 15 Commercial Hardening may start while Phase 13 remains DEFERRED / NOT PASS.
