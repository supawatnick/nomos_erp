# Database Design

PostgreSQL is the system of record.

## Core tables

Identity/configuration:
- tenants
- users
- tenant_users
- roles
- permissions
- role_permissions
- tenant_user_roles
- sessions / refresh_tokens as needed

Master data:
- products
- categories
- units
- product_units if conversions are supported
- warehouses
- warehouse_locations
- suppliers
- customers

Inventory:
- inventory_transactions
- inventory_transaction_lines
- inventory_balances (derived/materialized optimization, not source-of-truth ledger)
- reorder_rules

Control/audit:
- idempotency_keys
- approvals
- approval_steps or approval_decisions
- audit_logs
- outbox_events

LINE:
- line_channels / tenant_line_config
- line_user_links
- line_webhook_events

## Common columns

Tenant-owned tables generally include:
- id: UUID/ULID or documented stable identifier
- tenant_id
- created_at
- updated_at where mutable
- created_by / updated_by when operationally useful

Business rows that can be deactivated should prefer explicit status/archived_at over destructive deletion when history matters.

## Tenant isolation

- Every tenant-owned query includes tenant scope.
- Foreign references between tenant-owned entities must be validated to the same tenant.
- Unique constraints include tenant_id when uniqueness is tenant-local.
- Cache keys, object paths and background jobs include tenant identity.
- Consider PostgreSQL Row Level Security as defense-in-depth, not a substitute for application authorization.

## Inventory ledger

Inventory transaction header:
- tenant_id
- transaction_number
- type: RECEIVE, ISSUE, TRANSFER, ADJUST_IN, ADJUST_OUT, REVERSAL
- status: DRAFT/PENDING_APPROVAL/POSTED/REJECTED/CANCELLED as applicable
- reference_type/reference_id
- reason
- occurred_at
- posted_at
- actor/channel/request_id/idempotency metadata

Line:
- product_id
- unit_id
- quantity
- from_location_id when decreasing
- to_location_id when increasing
- unit_cost when applicable

A transfer is one business transaction containing a source decrease and destination increase that commit atomically.

## Balance model

The ledger is authoritative. inventory_balances may be maintained transactionally as a projection for fast reads. It must be reproducible/reconcilable from posted ledger lines.

Suggested unique key:
tenant_id + product_id + location_id + unit/stock dimension.

## Numeric rules

- NUMERIC/DECIMAL for quantities and money.
- Currency includes explicit currency code and scale policy.
- Unit precision is defined and validated.
- Never use floating point for persisted business amounts.

## Concurrency

Stock-changing operations use a documented strategy such as row locks on balance projection rows in a deterministic order. The operation validates available quantity and writes ledger/projection inside one transaction.

Concurrency tests must cover two simultaneous issues/transfers for the same stock.

## Idempotency

Store:
- tenant_id
- actor/client scope
- idempotency key
- request fingerprint
- resulting resource/response
- status and expiry policy

A replay with the same fingerprint returns the original result. A conflicting fingerprint is rejected.

## Index baseline

Index:
- tenant_id + common lookup columns
- tenant_id + SKU/product code
- tenant_id + warehouse/location
- tenant_id + transaction date/type/status
- tenant_id + approval status
- webhook/event unique delivery identifiers
- audit tenant + timestamp + actor/action as needed

## Migrations

All schema changes are versioned. Prefer expand/backfill/switch/contract for risky changes. Production migrations are controlled deployment steps and are not run implicitly by every application replica.