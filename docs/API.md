# API Contract

Base path: /api/v1

## Resource groups

- /auth
- /me
- /tenants
- /users
- /roles
- /products
- /categories
- /units
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
- /health
- /ready

Future modules:
- /suppliers
- /purchase-orders
- /customers
- /sales-orders

## Authentication

Web uses a secure server-managed session or short-lived access token plus rotating refresh token stored in secure HttpOnly cookies. Do not store long-lived credentials in browser localStorage. Machine-to-machine credentials, if added later, must be separately scoped and revocable.

## Tenant context

Tenant context comes from authenticated tenant membership. The client may select among tenants it belongs to, but the server validates membership and does not trust an arbitrary tenant_id in a business payload.

## Mutation conventions

- POST for commands that create business transactions.
- Require an Idempotency-Key for retriable stock mutations.
- Return the existing result for a replay of the same key and compatible request.
- Reject reuse of the same key with a materially different payload.
- Use optimistic or pessimistic concurrency explicitly; never unprotected read-then-write.

## Standard success envelope

~~~
{
  "data": {...},
  "meta": {
    "request_id": "..."
  }
}
~~~

## Standard error envelope

~~~
{
  "error": {
    "code": "INSUFFICIENT_STOCK",
    "message": "Insufficient available stock",
    "details": {...},
    "request_id": "..."
  }
}
~~~

Error codes are stable machine contracts; messages may be localized.

## Pagination

List endpoints use cursor pagination where practical:
- limit
- cursor
- sort
- approved filter fields

Responses return next_cursor when more data exists. Avoid arbitrary client-provided SQL-like sort/filter expressions.

## Time, quantity and money

- Persist timestamps in UTC.
- Return RFC 3339/ISO 8601 timestamps.
- Present using tenant/user timezone.
- Quantities and currency values are serialized as strings or exact decimal-safe values, never binary floating point assumptions.

## Authorization

Each protected endpoint maps to explicit permission(s), for example:
- inventory.read
- inventory.receive
- inventory.issue
- inventory.transfer
- inventory.adjust
- approval.read
- approval.decide
- product.manage
- warehouse.manage
- user.manage
- tenant.manage
- audit.read

## Versioning

Breaking contract changes require a new API version or a documented compatibility migration. OpenAPI generated from FastAPI is the authoritative machine-readable contract.