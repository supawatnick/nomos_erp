# RBAC Skill

Before authorization work read docs/AUTHORIZATION.md and docs/MULTI-TENANCY.md.
- Authorize permissions, not role-name conditionals.
- Deny by default.
- Tenant membership is trusted server context, never arbitrary payload data.
- Validate same-tenant ownership for every referenced business ID.
- UI authorization is UX only; server remains authoritative.
- Design trusted scope so branch/warehouse restrictions can be added later.
- Maintain automated permission allow/deny and cross-tenant tests.
