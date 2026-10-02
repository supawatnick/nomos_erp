# NOMOS ERP — Phase 2 Review

Status: **PASS — SaaS Platform Core**

## Scope completed

Phase 2 establishes the tenant/security/control-plane foundation required by later ERP modules.

### Persistence
- Tenant, tenant settings, legal entity and branch persistence.
- Global user identity plus tenant membership.
- Tenant-scoped roles, global permission catalog, role-permission and membership-role joins.
- Session persistence stores only token hashes.
- Idempotency, append-oriented audit and transactional outbox persistence.
- Same-tenant composite candidate keys/FKs protect tenant-owned relationships at the database boundary.
- Active-session index and Phase 2 permission seed catalog included in migrations.

### Authentication and authorization
- Passwords use PBKDF2-SHA256 with per-password salt.
- Session tokens are generated randomly and persisted only as SHA-256 hashes.
- Login requires an active user and active membership in the selected tenant.
- Session resolution derives tenant membership and effective permissions server-side.
- Revoked sessions, disabled users and disabled memberships cannot establish trusted context.
- Permission checks are deny-by-default and check permission codes rather than role names.
- Server owns the canonical request ID; client correlation is separate.
- /api/v1/auth/login, /api/v1/auth/logout, and /api/v1/auth/context provide the Phase 2 session/context transport surface.

### Tenant isolation and control
- Tenant-scoped repository reads and mutations always include tenant ID.
- Cross-tenant guessed IDs are hidden by tenant-scoped lookup semantics.
- Composite database FKs reject foreign-tenant organization references.
- Administration mutation service requires organization.manage.
- Successful critical administration mutations write correlated audit and outbox rows in the same database transaction.
- Idempotency claims distinguish first claim, same-fingerprint replay and conflicting payload.

## Automated acceptance coverage
- deny-by-default RBAC and explicit allow/deny permission matrix;
- password hashing and session-token hashing;
- cross-tenant composite-FK rejection;
- cross-tenant read/update/archive guessed-ID isolation;
- disabled membership rejection;
- revoked session rejection;
- deterministic idempotency fingerprinting and persisted replay/conflict semantics;
- audit metadata secret redaction;
- correlated administration audit + outbox persistence;
- server-owned canonical request IDs.

PostgreSQL-specific isolation tests run in CI after Alembic migration so they exercise the authoritative database rather than SQLite.

## Migrations
- 0002_phase2_saas_core.py — tenancy, organization, identity/RBAC/session, idempotency, audit and outbox baseline.
- 0003_phase2_completion.py — tenant settings, permission seeds and active-session index.

## Security decisions locked
- Tenant identity is never trusted from a business payload; authenticated membership resolves trusted context.
- Role names are not authorization primitives; effective permission codes are.
- Default branch is UX context only and grants no permission.
- Cross-tenant resource probing must not reveal object existence.
- Session tokens, passwords, credentials and authorization material must not enter audit metadata.
- Audit history is append-oriented; no normal update/delete API is provided.
- Outbox rows are created transactionally with critical business effects.

## Exit gate
Phase 2 is PASS only with Ruff, mypy, PostgreSQL Alembic upgrade, unit/integration tests, dependency audit, Web regression gates, gitleaks, final GitHub Actions PASS, updated PROJECT-STATUS.md and a clean host 73 working tree.

## Next phase
Phase 3 — Catalog and Warehouse: categories, units/conversions, products/barcodes, warehouses/locations, document sequence, archive lifecycle, list APIs and Web master-data flows.
