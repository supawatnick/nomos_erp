# Multi-Tenancy Skill

- Tenant is SaaS isolation/commercial boundary; do not conflate it with legal entity, branch, warehouse or location.
- Every tenant-owned repository operation is explicitly tenant scoped.
- Tenant-local uniqueness includes tenant_id.
- Cache keys, jobs, files, imports, audit and integrations carry tenant context.
- Cross-tenant references are invalid even if IDs exist.
- Shared DB/shared schema is initial; preserve domain semantics so selected enterprise tenants can move to dedicated infrastructure later.
