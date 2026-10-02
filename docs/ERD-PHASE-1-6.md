# Phase 1–6 Detailed Database Schema Contract

Status: APPROVED FOR PHASE 1–6 MIGRATION DESIGN

This contract refines DATA-MODEL.md. PostgreSQL is authoritative. Names may receive mechanical ORM naming adjustments, but ownership, keys, constraints and semantics require architecture review before change.

## Global conventions

- Primary business IDs: UUID, generated server-side.
- Tenant-owned tables include tenant_id UUID NOT NULL.
- Time instants: TIMESTAMPTZ, stored/compared as UTC.
- Business dates without time: DATE.
- Quantity: NUMERIC(24,8). Unit precision is additionally validated by domain rules.
- Money/rates: NUMERIC(24,8) internally unless a narrower presentation scale is configured.
- Currency: CHAR(3), ISO-4217 code.
- Codes: VARCHAR with explicit limits; normalized/case-insensitive uniqueness is implemented with normalized columns or functional indexes.
- Metadata JSONB is allowed only for non-core extensibility.
- Mutable masters use status/archived_at; referenced history is not physically deleted.
- Posted/append-oriented business history is not cascade-deleted.
- Tenant-owned parent tables expose UNIQUE(tenant_id,id) so composite foreign keys can enforce same-tenant references.
- Application tenant scoping is mandatory; PostgreSQL RLS may be added as defense-in-depth.
- FK delete default is RESTRICT/NO ACTION unless explicitly stated.
- created_at is NOT NULL; updated_at is NOT NULL on mutable rows.
- Actor FKs may be nullable where system/bootstrap actions are valid, while audit actor metadata remains explicit.

## 1. Tenancy and organization

### tenants
Global SaaS boundary.
- id UUID PK
- slug VARCHAR(80) NOT NULL
- name VARCHAR(200) NOT NULL
- status VARCHAR(24) NOT NULL: TRIAL|ACTIVE|SUSPENDED|CANCELLED
- default_locale VARCHAR(16) NOT NULL
- default_timezone VARCHAR(64) NOT NULL
- base_currency CHAR(3) NOT NULL
- created_at TIMESTAMPTZ NOT NULL
- updated_at TIMESTAMPTZ NOT NULL
Constraints/indexes:
- UNIQUE(lower(slug))
Deletion: never hard-delete after business data exists.

### tenant_settings
- tenant_id UUID PK FK tenants(id)
- settings_version INTEGER NOT NULL
- settings JSONB NOT NULL DEFAULT '{}'
- updated_at TIMESTAMPTZ NOT NULL
Use only for non-relational settings; security/domain-critical configuration gets typed tables/columns.

### legal_entities
- id UUID PK
- tenant_id UUID NOT NULL
- code VARCHAR(40) NOT NULL
- legal_name VARCHAR(240) NOT NULL
- display_name VARCHAR(240)
- tax_id VARCHAR(64)
- registration_number VARCHAR(80)
- country_code CHAR(2) NOT NULL
- base_currency CHAR(3) NOT NULL
- timezone VARCHAR(64) NOT NULL
- status VARCHAR(24) NOT NULL
- archived_at TIMESTAMPTZ
- created_at/updated_at TIMESTAMPTZ NOT NULL
Constraints:
- UNIQUE(tenant_id,id)
- UNIQUE(tenant_id,code)
- FK tenant_id -> tenants
Indexes: tenant_id,status
Deletion: archive.

### branches
- id UUID PK
- tenant_id UUID NOT NULL
- legal_entity_id UUID NOT NULL
- code VARCHAR(40) NOT NULL
- name VARCHAR(200) NOT NULL
- timezone VARCHAR(64)
- status VARCHAR(24) NOT NULL
- archived_at TIMESTAMPTZ
- created_at/updated_at TIMESTAMPTZ NOT NULL
Constraints:
- UNIQUE(tenant_id,id)
- UNIQUE(tenant_id,legal_entity_id,code)
- UNIQUE(tenant_id,legal_entity_id,id) to support composite organization references
- composite FK (tenant_id,legal_entity_id) -> legal_entities(tenant_id,id)
Indexes: tenant_id,legal_entity_id,status
Deletion: archive.

## 2. Identity and RBAC

### users
Global login identity.
- id UUID PK
- email VARCHAR(320) NOT NULL
- password_hash TEXT NOT NULL
- display_name VARCHAR(200) NOT NULL
- status VARCHAR(24) NOT NULL
- locale VARCHAR(16)
- last_login_at TIMESTAMPTZ
- created_at/updated_at TIMESTAMPTZ NOT NULL
Constraints: UNIQUE(lower(email))
Deletion: disable/anonymize according to retention policy; never delete business history.

### tenant_users
- id UUID PK
- tenant_id UUID NOT NULL
- user_id UUID NOT NULL
- employee_code VARCHAR(64)
- default_branch_id UUID
- status VARCHAR(24) NOT NULL
- joined_at TIMESTAMPTZ NOT NULL
- created_at/updated_at TIMESTAMPTZ NOT NULL
Constraints:
- UNIQUE(tenant_id,id)
- UNIQUE(tenant_id,user_id)
- composite FK default branch belongs to tenant
Indexes: user_id; tenant_id,status

### permissions
Global catalog.
- id UUID PK
- code VARCHAR(120) NOT NULL UNIQUE
- description VARCHAR(300) NOT NULL
- risk_level VARCHAR(16) NOT NULL
- created_at TIMESTAMPTZ NOT NULL

### roles
Tenant-owned configurable role.
- id UUID PK
- tenant_id UUID NOT NULL
- code VARCHAR(80) NOT NULL
- name VARCHAR(120) NOT NULL
- description VARCHAR(300)
- is_system BOOLEAN NOT NULL DEFAULT false
- status VARCHAR(24) NOT NULL
- created_at/updated_at TIMESTAMPTZ NOT NULL
Constraints: UNIQUE(tenant_id,id), UNIQUE(tenant_id,code)

### role_permissions
- tenant_id UUID NOT NULL
- role_id UUID NOT NULL
- permission_id UUID NOT NULL
- created_at TIMESTAMPTZ NOT NULL
PK: (tenant_id,role_id,permission_id)
Composite FK role; FK permission.

### tenant_user_roles
- tenant_id UUID NOT NULL
- tenant_user_id UUID NOT NULL
- role_id UUID NOT NULL
- created_at TIMESTAMPTZ NOT NULL
PK: (tenant_id,tenant_user_id,role_id)
Composite FKs ensure both membership and role belong to tenant.

### sessions
- id UUID PK
- user_id UUID NOT NULL
- token_hash TEXT NOT NULL
- expires_at TIMESTAMPTZ NOT NULL
- revoked_at TIMESTAMPTZ
- created_at TIMESTAMPTZ NOT NULL
- last_seen_at TIMESTAMPTZ
- ip_hash TEXT
- user_agent_summary VARCHAR(300)
Constraints: UNIQUE(token_hash)
Indexes: user_id,expires_at; active-session partial index where revoked_at IS NULL.
Raw session tokens are never stored.

## 3. Catalog

### categories
- id UUID PK
- tenant_id UUID NOT NULL
- parent_id UUID
- code VARCHAR(64) NOT NULL
- name VARCHAR(200) NOT NULL
- status VARCHAR(24) NOT NULL
- archived_at TIMESTAMPTZ
- created_at/updated_at TIMESTAMPTZ NOT NULL
Constraints: UNIQUE(tenant_id,id), UNIQUE(tenant_id,code), same-tenant parent FK.
Cycle prevention is application/domain validated.

### units
- id UUID PK
- tenant_id UUID NOT NULL
- code VARCHAR(32) NOT NULL
- name VARCHAR(100) NOT NULL
- symbol VARCHAR(24)
- precision SMALLINT NOT NULL DEFAULT 0
- status VARCHAR(24) NOT NULL
- created_at/updated_at TIMESTAMPTZ NOT NULL
Constraints: UNIQUE(tenant_id,id), UNIQUE(tenant_id,code), CHECK precision BETWEEN 0 AND 8.

### products
- id UUID PK
- tenant_id UUID NOT NULL
- sku VARCHAR(100) NOT NULL
- name VARCHAR(240) NOT NULL
- description TEXT
- category_id UUID
- product_type VARCHAR(24) NOT NULL: STOCKABLE|CONSUMABLE|SERVICE
- base_unit_id UUID NOT NULL
- tracking_type VARCHAR(16) NOT NULL DEFAULT 'NONE': NONE|LOT|SERIAL
- status VARCHAR(24) NOT NULL
- archived_at TIMESTAMPTZ
- created_at/updated_at TIMESTAMPTZ NOT NULL
Constraints:
- UNIQUE(tenant_id,id)
- UNIQUE(tenant_id,sku)
- same-tenant category and base-unit composite FKs
Indexes: tenant_id,status; tenant_id,category_id
Deletion: archive after reference.

### product_units
Allowed conversion to base unit.
- id UUID PK
- tenant_id UUID NOT NULL
- product_id UUID NOT NULL
- unit_id UUID NOT NULL
- factor_to_base NUMERIC(24,8) NOT NULL
- is_purchase_unit BOOLEAN NOT NULL DEFAULT false
- is_sales_unit BOOLEAN NOT NULL DEFAULT false
- created_at/updated_at TIMESTAMPTZ NOT NULL
Constraints: UNIQUE(tenant_id,id), UNIQUE(tenant_id,product_id,unit_id), CHECK factor_to_base > 0; same-tenant product/unit FKs.

### product_barcodes
- id UUID PK
- tenant_id UUID NOT NULL
- product_id UUID NOT NULL
- product_unit_id UUID
- barcode VARCHAR(128) NOT NULL
- created_at TIMESTAMPTZ NOT NULL
Constraints: UNIQUE(tenant_id,id), UNIQUE(tenant_id,barcode); same-tenant product/unit FKs.

## 4. Warehouse

### warehouses
- id UUID PK
- tenant_id UUID NOT NULL
- legal_entity_id UUID NOT NULL
- branch_id UUID
- code VARCHAR(64) NOT NULL
- name VARCHAR(200) NOT NULL
- status VARCHAR(24) NOT NULL
- archived_at TIMESTAMPTZ
- created_at/updated_at TIMESTAMPTZ NOT NULL
Constraints:
- UNIQUE(tenant_id,id)
- UNIQUE(tenant_id,code)
- composite FK (tenant_id,legal_entity_id) -> legal_entities(tenant_id,id)
- when branch_id is present, composite FK (tenant_id,legal_entity_id,branch_id) -> branches(tenant_id,legal_entity_id,id), guaranteeing branch and warehouse share the same legal entity
- branch_id NULL means legal-entity-level warehouse, not an unknown branch.
Indexes: tenant_id,branch_id,status.

### warehouse_locations
- id UUID PK
- tenant_id UUID NOT NULL
- warehouse_id UUID NOT NULL
- parent_id UUID
- code VARCHAR(64) NOT NULL
- name VARCHAR(160) NOT NULL
- location_type VARCHAR(24) NOT NULL DEFAULT 'STORAGE'
- allow_stock BOOLEAN NOT NULL DEFAULT true
- status VARCHAR(24) NOT NULL
- archived_at TIMESTAMPTZ
- created_at/updated_at TIMESTAMPTZ NOT NULL
Constraints: UNIQUE(tenant_id,id), UNIQUE(tenant_id,warehouse_id,code); same-tenant warehouse and parent FKs. Parent must be in same warehouse.
Indexes: tenant_id,warehouse_id,status.

## 5. Inventory ledger

### inventory_transactions
- id UUID PK
- tenant_id UUID NOT NULL
- transaction_number VARCHAR(80) NOT NULL
- transaction_type VARCHAR(24) NOT NULL: RECEIVE|ISSUE|TRANSFER|ADJUST_IN|ADJUST_OUT|REVERSAL|OPENING
- status VARCHAR(32) NOT NULL
- legal_entity_id UUID NOT NULL
- branch_id UUID
- reference_type VARCHAR(64)
- reference_id UUID
- reason_code VARCHAR(64)
- reason_text TEXT
- occurred_at TIMESTAMPTZ NOT NULL
- posted_at TIMESTAMPTZ
- posted_by UUID
- reversal_of_id UUID
- channel VARCHAR(16) NOT NULL
- request_id UUID NOT NULL
- created_by UUID
- created_at/updated_at TIMESTAMPTZ NOT NULL
Constraints:
- UNIQUE(tenant_id,id)
- UNIQUE(tenant_id,transaction_number)
- UNIQUE(tenant_id,reversal_of_id) WHERE reversal_of_id IS NOT NULL (one canonical reversal per original; further correction uses a new business flow)
- same-tenant organization and reversal FKs
- POSTED requires posted_at and posted_by/system actor policy
Indexes:
- (tenant_id,occurred_at DESC)
- (tenant_id,transaction_type,status,occurred_at DESC)
- (tenant_id,reference_type,reference_id)
- (tenant_id,reversal_of_id)
Deletion: posted rows never deleted.

### inventory_transaction_lines
- id UUID PK
- tenant_id UUID NOT NULL
- transaction_id UUID NOT NULL
- line_no INTEGER NOT NULL
- product_id UUID NOT NULL
- unit_id UUID NOT NULL
- quantity NUMERIC(24,8) NOT NULL
- base_quantity NUMERIC(24,8) NOT NULL
- from_location_id UUID
- to_location_id UUID
- unit_cost NUMERIC(24,8)
- currency_code CHAR(3)
- created_at TIMESTAMPTZ NOT NULL
Constraints:
- UNIQUE(tenant_id,id)
- UNIQUE(tenant_id,transaction_id,line_no)
- CHECK quantity > 0
- CHECK base_quantity > 0
- CHECK unit_cost IS NULL OR unit_cost >= 0
- same-tenant transaction/product/unit/location FKs
- transaction-type location shape is domain validated and backed by CHECKs where practical.
Indexes: tenant_id,product_id; tenant_id,from_location_id; tenant_id,to_location_id.

Ledger direction is derived from transaction type and from/to location semantics; persisted command quantity remains positive.

### inventory_balances
Transactional read projection; not source of truth.
- id UUID PK
- tenant_id UUID NOT NULL
- product_id UUID NOT NULL
- location_id UUID NOT NULL
- on_hand NUMERIC(24,8) NOT NULL DEFAULT 0
- version BIGINT NOT NULL DEFAULT 0
- updated_at TIMESTAMPTZ NOT NULL
Constraints:
- UNIQUE(tenant_id,id)
- UNIQUE(tenant_id,product_id,location_id)
- same-tenant product/location FKs
- CHECK on_hand >= 0 for default no-negative-stock policy; if tenant policy later allows negative stock this constraint must become policy-compatible rather than silently removed.
Indexes: tenant_id,location_id,product_id; tenant_id,product_id.

Balance rows are locked in deterministic key order during posting. Missing rows are safely created/upserted before/within the posting strategy defined by INVENTORY-EXECUTION.md.

## 6. Stock operations

### reorder_rules
- id UUID PK
- tenant_id UUID NOT NULL
- product_id UUID NOT NULL
- warehouse_id UUID NOT NULL
- minimum_qty NUMERIC(24,8) NOT NULL DEFAULT 0
- reorder_point NUMERIC(24,8) NOT NULL
- target_qty NUMERIC(24,8)
- status VARCHAR(24) NOT NULL
- created_at/updated_at TIMESTAMPTZ NOT NULL
Constraints: UNIQUE(tenant_id,id), UNIQUE(tenant_id,product_id,warehouse_id), nonnegative quantities, target >= reorder_point when present.

### stock_counts
- id UUID PK
- tenant_id UUID NOT NULL
- count_number VARCHAR(80) NOT NULL
- warehouse_id UUID NOT NULL
- status VARCHAR(32) NOT NULL
- snapshot_at TIMESTAMPTZ NOT NULL
- started_by UUID
- reviewed_by UUID
- posted_adjustment_transaction_id UUID
- created_at/updated_at TIMESTAMPTZ NOT NULL
Constraints: UNIQUE(tenant_id,id), UNIQUE(tenant_id,count_number); same-tenant warehouse/posted-adjustment FK.
Deletion: no deletion after count starts.

### stock_count_lines
- id UUID PK
- tenant_id UUID NOT NULL
- stock_count_id UUID NOT NULL
- line_no INTEGER NOT NULL
- product_id UUID NOT NULL
- location_id UUID NOT NULL
- system_qty NUMERIC(24,8) NOT NULL
- counted_qty NUMERIC(24,8)
- variance_qty NUMERIC(24,8)
- counted_by UUID
- counted_at TIMESTAMPTZ
Constraints: UNIQUE(tenant_id,id), UNIQUE(tenant_id,stock_count_id,line_no), UNIQUE(tenant_id,stock_count_id,product_id,location_id); same-tenant FKs.
Variance is validated/derived from counted - snapshot/system quantity; posting creates Inventory adjustment rather than updating balance directly.

## 7. Control, audit and reliable side effects

### idempotency_keys
- id UUID PK
- tenant_id UUID NOT NULL
- scope VARCHAR(120) NOT NULL
- idempotency_key VARCHAR(200) NOT NULL
- request_fingerprint CHAR(64) NOT NULL
- status VARCHAR(24) NOT NULL
- resource_type VARCHAR(80)
- resource_id UUID
- response_code INTEGER
- response_body JSONB
- expires_at TIMESTAMPTZ NOT NULL
- created_at/updated_at TIMESTAMPTZ NOT NULL
Constraints: UNIQUE(tenant_id,scope,idempotency_key)
Indexes: expires_at.
Same key + same fingerprint replays result; same key + different fingerprint is conflict.

### audit_logs
Append-oriented.
- id UUID PK
- tenant_id UUID NOT NULL
- occurred_at TIMESTAMPTZ NOT NULL
- actor_user_id UUID
- actor_tenant_user_id UUID
- action VARCHAR(160) NOT NULL
- target_type VARCHAR(100)
- target_id UUID
- channel VARCHAR(16) NOT NULL
- request_id UUID NOT NULL
- result VARCHAR(24) NOT NULL
- metadata JSONB NOT NULL DEFAULT '{}'
Indexes: tenant_id,occurred_at DESC; tenant_id,actor_user_id,occurred_at DESC; tenant_id,action,occurred_at DESC.
No normal update/delete API.

### outbox_events
- id UUID PK
- tenant_id UUID NOT NULL
- aggregate_type VARCHAR(100) NOT NULL
- aggregate_id UUID NOT NULL
- event_type VARCHAR(160) NOT NULL
- payload JSONB NOT NULL
- occurred_at TIMESTAMPTZ NOT NULL
- available_at TIMESTAMPTZ NOT NULL
- published_at TIMESTAMPTZ
- attempt_count INTEGER NOT NULL DEFAULT 0
- last_error TEXT
Indexes: unpublished (published_at IS NULL,available_at); tenant_id,aggregate_type,aggregate_id.
Created in same DB transaction as business effect.

## 8. Numbering, files and imports

### document_sequences
- id UUID PK
- tenant_id UUID NOT NULL
- document_type VARCHAR(64) NOT NULL
- legal_entity_id UUID
- branch_id UUID
- period_key VARCHAR(32) NOT NULL
- prefix VARCHAR(40) NOT NULL
- next_value BIGINT NOT NULL
- padding SMALLINT NOT NULL DEFAULT 6
- updated_at TIMESTAMPTZ NOT NULL
Constraints: scoped UNIQUE across tenant + document_type + nullable scope + period; CHECK next_value > 0; CHECK padding BETWEEN 1 AND 12.
Implementation must account for PostgreSQL NULL uniqueness semantics using NULLS NOT DISTINCT or normalized scope keys.

### attachments
- id UUID PK
- tenant_id UUID NOT NULL
- owner_type VARCHAR(80) NOT NULL
- owner_id UUID NOT NULL
- object_key TEXT NOT NULL
- original_filename VARCHAR(255) NOT NULL
- mime_type VARCHAR(160) NOT NULL
- size_bytes BIGINT NOT NULL
- sha256 CHAR(64) NOT NULL
- uploaded_by UUID
- created_at TIMESTAMPTZ NOT NULL
Constraints: UNIQUE(tenant_id,id), UNIQUE(object_key), CHECK size_bytes >= 0.
Object storage authorization must derive tenant context; polymorphic owner existence is application validated.

### import_batches
- id UUID PK
- tenant_id UUID NOT NULL
- import_type VARCHAR(64) NOT NULL
- status VARCHAR(24) NOT NULL
- source_attachment_id UUID
- total_rows INTEGER NOT NULL DEFAULT 0
- valid_rows INTEGER NOT NULL DEFAULT 0
- error_rows INTEGER NOT NULL DEFAULT 0
- requested_by UUID
- committed_at TIMESTAMPTZ
- created_at/updated_at TIMESTAMPTZ NOT NULL
Constraints: counters >= 0 and valid_rows + error_rows <= total_rows; same-tenant attachment reference.

### import_rows
Required for traceability.
- id UUID PK
- tenant_id UUID NOT NULL
- import_batch_id UUID NOT NULL
- row_number INTEGER NOT NULL
- status VARCHAR(24) NOT NULL
- source_data JSONB NOT NULL
- normalized_data JSONB
- errors JSONB
- target_type VARCHAR(80)
- target_id UUID
- created_at TIMESTAMPTZ NOT NULL
Constraints: UNIQUE(tenant_id,import_batch_id,row_number); same-tenant batch FK.
Retention may compact source rows after a documented period, but import audit summary remains.

## 9. Cross-tenant integrity strategy

For every tenant-owned referenced table, migrations create UNIQUE(tenant_id,id). Child relations use composite FKs such as:
(tenant_id, product_id) -> products(tenant_id,id)
rather than product_id -> products(id) alone.

Global user/permission references are exceptions because they are intentionally global. Authorization still validates tenant membership.

Polymorphic references such as reference_type/reference_id, audit target and attachment owner cannot use ordinary FKs; the owning application use case must validate target ownership and tests must cover guessed cross-tenant IDs.

## 10. Index principles

Every index is justified by an access path; avoid blindly indexing every FK. Phase 1–6 baseline prioritizes:
- tenant + human code/SKU
- tenant + active/status lists
- stock by product/location
- ledger by product/location/time and transaction time/type/status
- audit by tenant/time/actor/action
- outbox unpublished work
- idempotency uniqueness
- import batch/row lookup

Use EXPLAIN/production telemetry before adding speculative reporting indexes.

## 11. Four-core compatibility contract

Phase 1–6 does not implement Partners/CRM, Procurement, Sales/CRM or Finance, but the accepted foundation MUST remain compatible with them.

Preserved integration seams:
- organization/legal_entity IDs on business documents;
- product tracking and exact unit conversion;
- location-level physical stock authority;
- explicit currency/cost fields without making Inventory cost authoritative for Finance;
- source reference hooks plus request correlation;
- transactional outbox/idempotency for cross-core effects;
- document numbering scopes usable by QT/SO/PR/RFQ/PO/GR/invoices/payments/journals;
- composite tenant integrity and future legal-entity scope.

Future entity direction is defined in DATA-MODEL.md and FOUR-CORE-ERP-REVISION.md. In particular, later schema must support CRM lead/opportunity/activity, quotation revision/acceptance, RFQ/supplier responses, Sales/Procurement progress, Finance invoices/AR/AP/payments/journals/fiscal periods/tax/FX and a unique source-posting registry.

Phase 4 Inventory contracts must preserve stable source_type/source_id/source_number and idempotency/correlation so Goods Receipt, Delivery, Return and Finance valuation can integrate without direct cross-module table mutation.

Future stock dimensions require controlled expansion of ledger/balance keys. Do not encode lot/serial or future commercial/accounting core fields into JSON as a shortcut.

## 12. Migration-order dependency

1. tenants/users
2. legal_entities/branches
3. tenant membership/RBAC/session
4. categories/units/products/product_units/barcodes
5. warehouses/locations
6. document_sequences
7. inventory_transactions/lines/balances
8. reorder/stock_count
9. idempotency/audit/outbox
10. attachments/imports

Exact migration grouping may differ, but dependency order and constraints must remain valid.

## 13. ERD exit-gate checklist

PASS requires:
- [x] Tenant ownership identified for every Phase 1–6 table.
- [x] PK and tenant-local uniqueness strategy defined.
- [x] Same-tenant FK strategy defined.
- [x] Quantity/money/time types defined.
- [x] Archive/delete policy defined by category.
- [x] Inventory ledger and projection keys defined.
- [x] Idempotency/outbox/audit persistence defined.
- [x] Number allocation persistence defined.
- [x] Import traceability persistence defined.
- [x] Four-core Procurement/Sales-CRM/Finance compatibility reviewed and explicit integration seams reserved.

Open implementation detail intentionally deferred to migrations: exact PostgreSQL enum-vs-CHECK implementation, RLS policy DDL, and physical index tuning. These do not alter domain ownership or keys.
