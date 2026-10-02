# Domain Model and Vocabulary

## Hierarchy
Tenant is the SaaS isolation and commercial boundary. A tenant may contain one or more legal entities/companies. A legal entity may contain branches. Warehouses belong to the tenant and are associated with the appropriate organizational scope; stock is held at warehouse locations.

Do not equate Tenant, Legal Entity, Branch, Warehouse or Location.

## Identity
A global User authenticates to NOMOS. Tenant membership grants access to a tenant. Roles/permissions are assigned in tenant context. No business payload may assert trusted tenant identity.

## Catalog
Product is the commercial/master identity. Initial product types: STOCKABLE, CONSUMABLE, SERVICE. Inventory behavior applies only where defined by product policy. Category classifies products. Unit defines quantity semantics. ProductUnit defines allowed conversions. Barcode is an alternate identifier.

## Inventory
Physical stock is represented by posted inventory ledger effects at Location level. The authoritative history is the ledger. InventoryBalance is a projection for fast reads and must be rebuildable/reconcilable.

Initial implemented stock key: tenant + product + location.
Future dimensions must remain possible: lot/batch, serial, inventory status, owner/consignment.

OnHand = posted physical quantity.
Reserved = quantity committed by reservation rules when Sales is introduced.
Available initially equals OnHand; after reservations it is derived according to documented reservation policy.

## Business partner
BusinessPartner represents a legal/person counterparty. Partner roles classify CUSTOMER and/or SUPPLIER. UI may expose separate Customers and Suppliers without duplicating identity/address/contact data.

## Business documents
Each domain owns its concrete documents and lines. Shared concepts include document number, status, dates, organization, partner, references, notes, attachments, audit and approvals. Do not create one generic mega-table for all ERP documents.

## Posting
Posting is a domain transition that makes an approved business effect durable. Posted inventory transactions are immutable in normal operation. Correction is a reversal/compensating transaction with explicit linkage and reason.

## Accounting boundary
Physical inventory quantity and financial valuation are related but separate concerns. Inventory must not hardcode a single costing or GL policy. Business events/document postings provide explicit inputs to Accounting.

## Cross-module invariants
- Tenant ownership is never crossed.
- Posted history is not silently rewritten.
- External channels and UI never mutate persistence directly.
- Purchase orders do not increase physical stock; goods receipt does.
- Sales orders do not decrease on-hand; delivery/issue does.
- Reservation changes availability, not physical on-hand.
- Monetary and quantity values are exact decimals.
- Critical mutations are auditable and retry-safe.
