# Multi-Tenancy

NOMOS serves independent companies from a shared application.

## MVP model

Shared application + shared PostgreSQL database with tenant-scoped rows.

## Tenant context

Trusted tenant context is resolved from authenticated user membership. Users belonging to multiple tenants explicitly select an allowed tenant.

Every protected request/use case carries tenant_id in trusted execution context.

## Isolation requirements

- Every tenant-owned repository/query is scoped.
- Foreign entity references are validated in the same tenant.
- Unique constraints include tenant_id when uniqueness is tenant-local.
- Background jobs carry tenant context.
- Queue payloads include stable tenant and object identifiers, not implicit global context.
- Cache keys include tenant identity.
- Files/object storage paths are tenant-namespaced.
- Audit logs always identify tenant.
- LINE links are tenant-specific.
- Search/report/export functions preserve tenant scope.

## Defense in depth

PostgreSQL Row Level Security may be added as a second isolation layer. If used, application authorization remains mandatory.

## Administrative boundaries

There is no hidden cross-tenant application role in ordinary tenant APIs. Any future platform/support access must be separately designed with just-in-time access, strong audit and minimal scope.

## Testing

Automated tests must attempt:
- read tenant B resource using tenant A actor
- mutate tenant B resource
- reference tenant B product/location in tenant A transaction
- use guessed identifiers
- consume tenant B approval
- use tenant B LINE link/session
- cache key collision

Expected result is denial without leaking sensitive existence/details.