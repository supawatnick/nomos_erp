# Module Boundaries

## Rule
NOMOS is a modular monolith. A module owns its domain rules and persistence. Other modules use explicit application contracts; they do not update its tables directly.

## Four ERP cores
1. **finance** — GL, AR/AP, invoice, receipt/payment, fiscal periods, tax posting, financial statements and costing/valuation integration.
2. **inventory** — warehouse/location, immutable physical ledger, balances, stock count, reservations and availability.
3. **procurement** — supplier sourcing, PR, RFQ, PO, receipt/return orchestration and procurement tracking.
4. **sales_crm** — lead/opportunity/customer workflow, QT, SO, reservation/delivery/return orchestration and sales/order tracking.

## Supporting modules
identity: users, authentication, sessions.
tenancy: tenants, membership context and tenant settings.
organization: legal entities and branches.
catalog: products, categories, units, conversions and barcodes.
partners: shared business-partner identity, roles, contacts and addresses.
approval: policy and decision lifecycle.
audit: append-oriented security/business audit.
reporting: controlled read models/queries and exports.
line: external LINE transport/identity adapter only.

## Ownership examples
- Procurement posts Goods Receipt by invoking Inventory receive; it never inserts inventory ledger rows.
- Sales posts Delivery by invoking Inventory issue.
- QT acceptance creates commercial intent/order state, not stock or journal rows.
- Finance consumes explicit posting facts/contracts from Inventory/Procurement/Sales; it does not scrape their UI or mutate their source documents.
- Customer Invoice and Supplier Invoice are Finance-owned financial documents linked to source commercial documents.
- LINE invokes the same application use cases as Web.

## Dependency direction
Presentation/adapters -> application -> domain -> ports/interfaces -> infrastructure adapters.
Domain code does not import FastAPI, Next.js, LINE SDK, SQLAlchemy models or Redis clients.

## Cross-core integration contract
Every cross-core command/event carries tenant_id, immutable source ID, source type/number, effective date, actor/request correlation and idempotency identity where retriable. Money carries currency; quantity carries unit/precision. Receivers validate tenant ownership and current source state.

## Transactions
A use case defines the consistency boundary. Where one PostgreSQL transaction must cover multiple module-owned effects in the modular monolith, orchestration is explicit and ownership remains clear. Asynchronous side effects use transactional outbox. No distributed transaction is introduced without a measured need.
