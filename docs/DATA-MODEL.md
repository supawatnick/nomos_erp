# Data Model Direction

This is the architectural ERD direction, not permission to create all tables in the first migration.

## Platform
tenants
tenant_settings
legal_entities
branches
users
tenant_users
roles
permissions
role_permissions
tenant_user_roles
sessions
idempotency_keys
audit_logs
outbox_events
attachments
import_batches
document_sequences

## Catalog
products
categories
units
product_units
product_barcodes

## Warehouse and inventory
warehouses
warehouse_locations
inventory_transactions
inventory_transaction_lines
inventory_balances
reorder_rules
stock_counts
stock_count_lines

Future: inventory_reservations, lots, serials, inventory_status dimensions.

## Partners
business_partners
partner_roles
partner_addresses
partner_contacts

## Purchasing
purchase_requests / lines
purchase_orders / lines
goods_receipts / lines
purchase_returns / lines

## Sales
quotations / lines
sales_orders / lines
inventory_reservations
deliveries / lines
sales_returns / lines

## Workflow
approval_policies
approval_requests
approval_steps
approval_decisions

## LINE
line_channels or tenant_line_config
line_user_links
line_webhook_events

## Common design rules
- UUID identifiers unless a module documents a stronger reason otherwise.
- Tenant-owned tables carry tenant_id and tenant-local uniqueness includes tenant_id.
- created_at and updated_at use timezone-aware timestamps; persisted instants are UTC.
- created_by/updated_by are included where operationally useful.
- mutable master data prefers status/archived_at to destructive deletion when referenced historically.
- NUMERIC/DECIMAL is used for quantity, cost, price, tax and money.
- Money stores explicit currency context; never assume THB globally.
- Foreign references among tenant-owned records must preserve same-tenant ownership.
- JSONB is for extensible metadata where relational constraints are not required; it is not a substitute for core relational columns.
- Files live in object storage; PostgreSQL stores metadata, object key, tenant, hash, size and MIME type.
- Schema migrations are versioned and controlled.

## Scale direction
Start shared database/shared schema with strong tenant scoping. Add indexes and partition high-volume append tables only from measured need. Read replicas/reporting replicas may be introduced later. Architecture must permit selected enterprise tenants to move to dedicated deployment/database without changing domain semantics.

## High-volume candidates
inventory_transactions/lines, audit_logs, outbox events, webhook events and future accounting journals require deliberate indexing, retention/archival and possible partitioning based on measured volume.
