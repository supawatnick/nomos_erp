# Database Design

PostgreSQL is the system of record.

## Core entities
- tenants
- users
- tenant_users
- roles / permissions
- products
- categories
- units
- warehouses
- warehouse_locations
- inventory_transactions
- inventory_transaction_lines
- suppliers
- customers
- approvals
- audit_logs
- line_accounts / line_user_links

## Tenant isolation
All tenant-owned tables carry `tenant_id`. Every repository/query must scope by tenant. Cross-tenant access is forbidden.

## Inventory
Stock movements are append-oriented ledger transactions. Types initially include RECEIVE, ISSUE, TRANSFER, ADJUST_IN, ADJUST_OUT.

A transfer must be represented consistently as source decrease + destination increase under one business transaction.

## Numeric rules
Use PostgreSQL NUMERIC/DECIMAL for quantities/costs where fractional units are supported. Define unit precision explicitly.

## Concurrency
Stock-changing operations execute in DB transactions with an explicit concurrency strategy. Never rely on a read-then-write sequence without protection.
