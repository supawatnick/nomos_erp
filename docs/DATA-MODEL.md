# Data Model Direction

This is the architectural ERD direction, not permission to create all tables in the first migration. Phase-specific schema contracts decide when tables are introduced.

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

Future commercial/accounting extensions are typed relations/configuration, not Phase 3 columns by default: product sales/purchase defaults, tax classifications and accounting mappings.

## Warehouse and inventory
warehouses
warehouse_locations
inventory_transactions
inventory_transaction_lines
inventory_balances
reorder_rules
stock_counts
stock_count_lines
inventory_reservations

Future: lots, serials and inventory-status dimensions.

## Partners & CRM
business_partners
partner_roles
partner_addresses
partner_contacts
crm_leads
crm_opportunities
crm_activities

A partner may be customer, supplier or both. CRM lead/opportunity may exist before conversion/linkage to a business partner.

## Procurement & Purchasing
purchase_requests / purchase_request_lines
requests_for_quotation / request_for_quotation_lines
supplier_quotation_responses / supplier_quotation_response_lines
purchase_orders / purchase_order_lines
goods_receipts / goods_receipt_lines
purchase_returns / purchase_return_lines

Commercial documents retain source linkage and line-level ordered/received/returned/invoiced progress.

## Sales & CRM
quotations / quotation_lines
quotation_revisions (or immutable versioned quotation headers/lines)
sales_orders / sales_order_lines
inventory_reservations
deliveries / delivery_lines
sales_returns / sales_return_lines

Quotation model must preserve revision/version, validity/expiry, acceptance evidence and accepted-version snapshot. Sales order read models track ordered/reserved/delivered/returned and later invoiced/paid progress without duplicating Finance authority.

## Finance & Accounting
chart_of_accounts
accounts
fiscal_periods
tax_codes
tax_rates
accounting_posting_rules
journal_entries / journal_lines
customer_invoices / customer_invoice_lines
supplier_invoices / supplier_invoice_lines
credit_debit_notes
receipts
payments
payment_allocations
ar_open_items
ap_open_items
source_posting_registry
exchange_rates
inventory_valuation_layers_or_cost_state

Exact physical design is Phase 12 work. Architectural requirements are locked now: tenant + legal-entity scope, balanced immutable journals, explicit currency/rate provenance, fiscal-period controls, source idempotency and subledger-to-GL reconciliation.

## Workflow
approval_policies
approval_requests
approval_steps
approval_decisions

## LINE
line_channels or tenant_line_config
line_user_links
line_webhook_events

## Cross-core source/provenance
Every durable cross-core effect preserves tenant_id, legal_entity_id where applicable, immutable source_type/source_id/source_number, effective date, request/correlation identity and idempotency identity. Money carries currency/rate context; quantity carries unit/base quantity. Polymorphic source references are application-validated for ownership and backed by unique posting/processing registries where duplicate effects are dangerous.

## Common design rules
- UUID identifiers unless a module documents a stronger reason otherwise.
- Tenant-owned tables carry tenant_id and tenant-local uniqueness includes tenant_id.
- Legal-entity financial/stock documents carry legal_entity_id and validate branch scope when present.
- created_at/updated_at are timezone-aware; persisted instants are UTC.
- Business dates are DATE and are not silently inferred from UTC timestamps.
- mutable master data prefers status/archived_at to destructive deletion when historically referenced.
- Posted inventory and accounting history is immutable; corrections are linked durable documents/effects.
- NUMERIC/DECIMAL is used for quantity, cost, price, tax, exchange rate and money. Never binary float.
- Money stores explicit ISO currency context; never assume THB globally.
- Foreign references among tenant-owned records preserve same-tenant ownership; legal-entity-owned records preserve organization ownership.
- JSONB is for non-core extensibility, not a substitute for constrained relational business columns.
- Files live in object storage; PostgreSQL stores metadata, object key, tenant, hash, size and MIME type.
- Schema migrations are versioned and controlled.
- Cross-core modules integrate through application contracts/outbox/posting facts, not direct table mutation.

## Scale direction
Start shared database/shared schema with strong tenant scoping. Add indexes and partition high-volume append tables only from measured need. Read/reporting replicas may be introduced later. Architecture must permit selected enterprise tenants to move to dedicated deployment/database without changing domain semantics.

## High-volume candidates
inventory transactions/lines, reservations, audit logs, outbox events, webhook events, journal entries/lines, AR/AP allocations and reporting facts require deliberate indexing, retention/archival and possible partitioning based on measured volume.
