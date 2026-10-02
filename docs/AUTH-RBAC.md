# Authentication and RBAC

## Authentication

MVP supports local ERP users. Authentication implementation must provide:
- strong password hashing with a modern memory-hard password hashing scheme
- rate limiting and lockout/backoff controls against brute force
- secure session/token rotation and revocation
- secure password reset with short-lived one-time tokens
- optional MFA as an early hardening feature

Web credentials/tokens must use Secure, HttpOnly cookies when cookie-based flows are used. CSRF protections are required for state-changing cookie-authenticated requests.

## Tenant membership

A user can belong to one or more tenants through tenant_users. Tenant selection is valid only when the membership is active.

Do not infer authorization from email domain or a tenant ID supplied in a business payload.

## Suggested roles

Roles are configurable, but initial templates can be:
- OWNER
- ADMIN
- INVENTORY_MANAGER
- OPERATOR
- APPROVER
- VIEWER

## Permission catalogue

Initial permissions:
- tenant.manage
- user.read / user.manage
- role.read / role.manage
- product.read / product.manage
- warehouse.read / warehouse.manage
- inventory.read
- inventory.receive
- inventory.issue
- inventory.transfer
- inventory.adjust
- approval.read
- approval.decide
- audit.read
- line.link / line.manage

## Authorization rules

- Deny by default.
- Check permission server-side in application use cases.
- Check tenant ownership of every referenced entity.
- A record ID alone never grants access.
- Approval decision requires both approval.decide and eligibility under the approval policy.
- A requester cannot approve their own request when separation-of-duties policy says so.

## Role templates

OWNER: all tenant permissions.
ADMIN: tenant configuration/users/masters plus operational read; sensitive rights configurable.
INVENTORY_MANAGER: masters needed for inventory and all standard inventory operations.
OPERATOR: inventory read and selected receive/issue/transfer operations.
APPROVER: inventory read, approval read/decide for eligible policies.
VIEWER: read-only permissions.

Exact templates are defaults; the permission system remains authoritative.

## Audit

Log security-relevant events:
- login success/failure category
- logout/session revocation
- password reset
- role/permission changes
- tenant membership changes
- LINE account link/unlink
- sensitive authorization denial where useful

Do not log passwords, raw reset tokens, refresh tokens or LINE secrets.