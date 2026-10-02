# API Guidelines

Base path: `/api/v1`.

Initial resources:
- /auth
- /tenants
- /users
- /products
- /warehouses
- /locations
- /inventory/balances
- /inventory/transactions
- /inventory/receive
- /inventory/issue
- /inventory/transfer
- /inventory/adjust
- /approvals
- /line
- /audit-logs

## Requirements
- OpenAPI generated from FastAPI
- tenant context resolved securely, never trusted from arbitrary client input
- RBAC on protected endpoints
- consistent error envelope
- pagination/filter/sort conventions
- idempotency keys for retriable mutations
- correlation/request IDs
- UTC timestamps in APIs; presentation converts to tenant/user timezone

API schemas are contracts. Breaking changes require a new version or migration strategy.
