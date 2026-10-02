# Phase 1–6 Authorization Matrix

Status: PASS — baseline permissions and test matrix.

Roles below are templates/examples only. Server code authorizes permissions, never role names.

## Risk levels
LOW: read-only operational access.
MEDIUM: mutable master/normal stock operations.
HIGH: stock correction, identity/security administration, tenant configuration, audit/export-sensitive actions.

## Permissions and operations

| Operation | Permission | Risk | Notes |
|---|---|---:|---|
| View tenant/company/branch | tenant.read / organization.read | LOW | Same tenant only |
| Edit tenant settings | tenant.manage | HIGH | Audit required |
| Create/edit/archive legal entity/branch | organization.manage | HIGH | Audit required |
| View users | user.read | LOW | Tenant membership only |
| Invite/edit/disable tenant user | user.manage | HIGH | Cannot grant beyond authorized administration policy |
| View roles | role.read | LOW | |
| Create/edit role and assignments | role.manage | HIGH | Audit before/after permission set |
| View products/categories/units | product.read | LOW | |
| Create/edit/archive products/categories/units/barcodes | product.manage | MEDIUM | Audit master changes |
| View warehouse/location | warehouse.read | LOW | |
| Create/edit/archive warehouse/location | warehouse.manage | HIGH | Referenced stock locations cannot be destructively removed |
| View stock/balances/movements | inventory.read | LOW | |
| Receive stock | inventory.receive | MEDIUM | Idempotency + audit |
| Issue stock | inventory.issue | MEDIUM | Sufficient stock + idempotency |
| Transfer stock | inventory.transfer | MEDIUM | Atomic + idempotency |
| Adjustment in/out | inventory.adjust | HIGH | Reason required; approval hook |
| Reverse posted inventory | inventory.adjust | HIGH | Reason + original eligibility; future dedicated permission may be split |
| Opening stock/import commit | inventory.adjust | HIGH | Controlled import/opening workflow |
| Create/perform stock count | inventory.count | MEDIUM | Posting variance also requires inventory.adjust unless policy grants combined workflow |
| View reorder/low stock | inventory.read | LOW | |
| Manage reorder rules | inventory.adjust | HIGH | Temporary Phase 1–6 mapping; may split inventory.policy.manage later |
| View audit | audit.read | HIGH | Metadata may be sensitive |
| Export operational reports | report.export | MEDIUM | report.read also required when report module enabled |

## Example role templates
Owner/Admin: broad tenant administration; still subject to invariant/approval rules.
Warehouse Manager: product.read, warehouse.read, inventory.read/receive/issue/transfer/adjust/count; optional warehouse.manage.
Warehouse Staff: product.read, warehouse.read, inventory.read/receive/issue/transfer; no adjustment by default.
Auditor/Viewer: read permissions and audit.read only where explicitly assigned.

Templates are seeded convenience, not authorization branches.

## Scope
Phase 1–6 permission grants are tenant-wide. API/application context MUST be shaped so later grants can include legal_entity_ids, branch_ids and warehouse_ids. Client-supplied scope is never trusted. When scoped grants arrive, effective scope is the intersection of membership/grant and requested object ownership.

## Separation and escalation
- A user may not use user.manage/role.manage to escape tenant membership boundaries.
- Assigning high-risk permissions is audited.
- Future approval policies can require a second actor for inventory.adjust/opening/reversal without changing permission codes.
- Stock-count variance posting requires inventory.count plus inventory.adjust unless an explicit approved workflow delegates the posting step.
- Disabled user or membership invalidates protected access even if an old session exists.

## Denial semantics
Unauthenticated -> AUTHENTICATION_REQUIRED.
Authenticated but inactive/expired membership -> PERMISSION_DENIED or session invalidation according to auth flow.
Missing permission -> PERMISSION_DENIED.
Guessed/cross-tenant business ID -> RESOURCE_NOT_FOUND when existence disclosure would leak tenant data.
Invalid same-tenant state -> appropriate domain error, never disguised as permission success.

## Required authorization tests
For every protected Phase 1–6 operation:
1. allowed permission succeeds on owned object;
2. missing permission denies;
3. disabled user/membership denies;
4. guessed other-tenant ID cannot read/mutate;
5. same-tenant child cannot reference foreign-tenant parent;
6. UI omission is not relied on—direct API call still denies;
7. role change takes effect according to session/permission refresh policy;
8. high-risk operation emits audit evidence;
9. stock-count posting checks both required permissions;
10. role/user administration cannot assign resources across tenants.
