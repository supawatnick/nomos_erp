# Multi-Tenancy

NOMOS is designed to serve multiple independent companies.

## MVP model
Shared application + shared PostgreSQL database with tenant-scoped rows.

## Requirements
- tenant membership determines accessible tenant(s)
- tenant context is established from authenticated membership
- every tenant-owned query is scoped
- unique constraints generally include tenant_id when uniqueness is tenant-local
- background jobs carry tenant context
- caches include tenant identity in keys
- files/object paths are tenant-namespaced
- audit logs identify tenant

Automated tests must attempt cross-tenant reads and writes and verify denial.
