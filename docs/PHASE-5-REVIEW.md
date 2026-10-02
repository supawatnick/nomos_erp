# Phase 5 Review — Inventory Web ERP

Date: 2026-10-02
Status: **PASS**

## Scope completed
Phase 5 turns the Phase 4 Inventory Engine into an operational Web ERP surface while preserving server authority for tenant isolation, permissions, stock validation, concurrency and idempotency.

### Inventory workspace
Routes:
- /inventory — operational control dashboard
- /inventory/stock — stock on hand
- /inventory/movements — immutable movement history
- /inventory/receive — receive workflow
- /inventory/issue — issue workflow
- /inventory/transfer — transfer workflow
- /inventory/adjust — adjustment workflow

The main ERP landing page now promotes Inventory Control alongside Master Data.

### Dashboard and stock
Inventory dashboard reads Phase 4 balances and movements.
Stock rows display product SKU/name and warehouse/location labels rather than forcing operators to work from UUIDs.
The balance API was enriched for presentation only; inventory quantity remains the Phase 4 projection and is not recalculated in Web code.

### Movement history
Movement history reads immutable POSTED transactions from Phase 4 and exposes transaction type, reference, source, posted time, status and reversal linkage.

### Posting workflows
Receive, Issue, Transfer and Adjustment share one Web posting component.
The form resolves active stock products, stock-enabled locations and warehouse organization context from authenticated APIs.
It sends:
- transaction_type
- legal_entity_id / branch_id derived from selected warehouse
- product base unit
- source/destination location
- quantity
- explicit adjustment direction
- reference/reason
- source_type=WEB_MANUAL

The Web never updates inventory_balances directly and does not reproduce no-negative-stock or posting rules.

### Idempotent retry
Every new posting attempt generates an Idempotency-Key.
If transport fails, Retry reuses the same key to prevent duplicate stock effects.
A successful posting clears the retry key and links the operator to movement history.
Server idempotency conflicts are surfaced explicitly.

### UX and security states
Implemented:
- loading
- empty
- validation
- missing login/session
- permission denied
- insufficient stock
- invalid document state
- idempotency conflict
- network failure with safe retry
- posted success state

Authorization and X-Tenant-ID are supplied from the established authenticated Web session, but server-side trusted context remains authoritative.

## Acceptance
Web tests verify:
- all Phase 5 routes exist
- authenticated tenant headers are used
- Phase 4 posting endpoint is used
- Idempotency-Key and retryKey behavior are present
- insufficient-stock and permission states are mapped
- organization/base unit are derived from server master data
- Web does not mutate on-hand balances

## Verification
Final closure gate:
- API Ruff
- API mypy
- PostgreSQL Alembic
- PostgreSQL pytest
- pip-audit
- npm ci
- npm audit high
- Web lint
- Web typecheck
- Web tests
- Web production build including all Phase 5 routes
- gitleaks
- final GitHub Actions success
- synchronized clean host 73

## Phase 5 exit
Phase 5 is complete when the final documentation commit passes the full gate and host 73 is synchronized/clean.
Next: Phase 6 Stock Count, Reorder and Operational Reports, completing the planned Internal ERP MVP.


## Phase 0–7 remediation closure addendum
The 2026-10-02 Phase 0–7 contract audit found that the original Phase 5 acceptance document required Users/Roles/Audit Web surfaces that were not present in the repository despite the phase being marked PASS.

Closure implemented before Phase 8:
- `/api/v1/admin/users` guarded by `user.read`;
- `/api/v1/admin/roles` guarded by `role.read`;
- `/api/v1/admin/audit` guarded by `audit.read`;
- all queries are tenant scoped and derive tenant from the authenticated server context;
- `/admin` provides Users, Roles/Permissions and Audit Trail surfaces;
- the Web remains presentation-only for authorization; API permission checks are authoritative;
- remediation Web acceptance verifies the required admin surface.

The gap is tracked and closed by `docs/PHASE-0-7-REMEDIATION.md`.
