# Authorization Model

## Model
NOMOS uses tenant-scoped RBAC with explicit permissions. Roles are permission bundles; business logic checks permissions, not role names.

## Initial permission namespaces
tenant.read, tenant.manage
organization.read, organization.manage
user.read, user.manage
role.read, role.manage
product.read, product.manage
warehouse.read, warehouse.manage
inventory.read, inventory.receive, inventory.issue, inventory.transfer, inventory.adjust, inventory.count
partner.read, partner.manage
purchase.read, purchase.create, purchase.approve
sales.read, sales.create, sales.approve
approval.read, approval.decide
report.read, report.export
audit.read
line.manage

## Enforcement
- Authentication establishes user identity.
- Membership establishes allowed tenant context.
- Server resolves effective permissions.
- Use case authorizes action.
- Repository validates tenant ownership/scoping.
- Referenced resources are verified in the same tenant.
- UI permission checks improve UX only and are never security boundaries.

## Object and scope rules
Future policy may restrict a permission to legal entity, branch, warehouse or department. Design APIs/use cases so trusted scope can be added without accepting arbitrary client claims.

## Denial behavior
Deny by default. Cross-tenant lookups should avoid leaking whether a guessed object exists.

## High-risk operations
Inventory adjustment, user/role changes, approval decisions, sensitive settings and future financial posting may require stronger permission and configurable approval.

## Testing
Maintain an authorization matrix and automated allow/deny tests. Include cross-tenant guessed IDs, foreign references, stale membership, disabled users and attempts to consume another tenant's approval/action token.
