# Module Boundaries

## Rule
NOMOS is a modular monolith. A module owns its domain rules and persistence. Other modules use its application contracts; they do not update its tables directly.

## Modules
identity: users, authentication, sessions.
tenancy: tenants, membership context and tenant settings.
organization: legal entities and branches.
catalog: products, categories, units, conversions and barcodes.
inventory: warehouses/locations, physical ledger, balances, stock count and future reservations.
partners: business partner identity, roles, contacts and addresses.
purchasing: PR, PO, goods receipt/return orchestration.
sales: quotation, sales order, reservation/delivery/return orchestration.
approval: policy and decision lifecycle.
audit: append-oriented security/business audit.
reporting: controlled read models/queries and exports.
accounting: future financial posting, GL, AR/AP and fiscal controls.
line: external LINE transport/identity adapter only.

## Cross-module examples
Purchasing posts Goods Receipt by invoking an Inventory receive application contract; it does not insert inventory ledger rows itself.
Sales posts Delivery by invoking an Inventory issue contract.
LINE invokes the same application use cases as Web.
Accounting consumes explicit posting contracts/events rather than reaching into UI/controller code.

## Dependency direction
Presentation/adapters -> application -> domain -> ports/interfaces -> infrastructure adapters.
Domain code does not import FastAPI, Next.js, LINE SDK, SQLAlchemy models or Redis clients.

## Transactions
A use case defines the consistency boundary. Where one database transaction must cover multiple module-owned effects in the modular monolith, orchestration is explicit and ownership remains clear. Asynchronous side effects use transactional outbox.
