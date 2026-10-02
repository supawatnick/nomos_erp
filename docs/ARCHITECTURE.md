# Architecture

## Context
NOMOS ERP is a multi-tenant SaaS ERP with four first-class business cores: Finance & Accounting, Inventory & Warehouse, Procurement & Purchasing, and Sales & CRM.

~~~
Browser / Next.js ---------LINE adapter (later) -------+-> FastAPI -> Application Use Cases -> Domain Modules
                             |                |
                             |                +-> Sales/CRM
                             |                +-> Procurement
                             |                +-> Inventory
                             |                +-> Finance
                             |                |
                             |             PostgreSQL
                             |                |
                             ---------- Outbox / Workers
~~~

## Layers
### Presentation/adapters
Next.js, FastAPI routers/schemas, LINE adapter and worker entrypoints validate transport, resolve trusted context, invoke a use case and map result/error.

### Application
Use-case orchestration, authorization, transaction boundary, idempotency, approvals, cross-module contracts and outbox creation.

### Domain
Module-owned state machines, quantity/money rules, inventory invariants, commercial rules, accounting posting rules and value objects independent of transport/infrastructure.

### Infrastructure
PostgreSQL repositories, queue/Redis adapters, external clients, telemetry, object storage and secrets.

## Core module ownership
- Sales/CRM owns lead -> QT -> SO -> fulfillment intent/status.
- Procurement owns sourcing -> PR/RFQ -> PO -> receipt intent/status.
- Inventory owns physical stock ledger/balances/reservations.
- Finance owns invoices, AR/AP, payment, journals/GL, fiscal controls and financial posting.
- Modules never directly update another module's tables.

## Cross-module flows
Sales: QT -> SO -> Inventory reservation -> Delivery/Inventory issue -> Finance customer invoice/AR -> receipt.
Procurement: PR/RFQ -> PO -> Goods Receipt/Inventory receive -> Finance supplier invoice/AP -> payment.
Inventory movements may emit valuation facts; Finance owns accounting mapping/journals.

## Key architectural rules
- No business rule is duplicated by channel.
- No external identifier is trusted without tenant/ownership validation.
- Database transactions wrap stock-changing and financial-posting use cases.
- Asynchronous effects follow durable commit through transactional outbox.
- Workers are idempotent and tenant-aware.
- Inventory balance is a projection; immutable posted ledger is quantity authority.
- Posted journal is financial authority; source modules cannot edit it.
- Exact decimals only for money/quantity; currency/unit context is explicit.
- Cross-module references preserve immutable source IDs and document numbers.
- No critical business integration is implemented by UI scraping or shared-table mutation.

## Request flow: business mutation
1. Authenticate actor.
2. Resolve membership/trusted tenant/legal-entity context.
3. Validate schema and idempotency.
4. Authorize permission and referenced resources.
5. Validate state transition/approval.
6. Start database transaction.
7. Lock/read authoritative state using module concurrency strategy.
8. Apply module invariants.
9. Invoke explicit same-transaction module contract when atomicity requires it, or persist durable outbox/posting fact for post-commit work.
10. Write source state + audit/outbox.
11. Commit.
12. Return result; retry asynchronous delivery idempotently.

## Failure model
Validation -> structured 4xx/no mutation.
Authorization -> deny without leaking cross-tenant existence.
Concurrency -> retryable conflict where safe.
Inventory/Finance contract failure inside an atomic use case -> rollback source transition.
External notification failure -> committed business transaction remains; retry outbox.
Database failure -> atomic rollback.

## Evolution
Remain a modular monolith until measured scale/team/domain boundaries justify extraction. If a core is later separated, existing application contracts/outbox identities become the seam; business rules must not be rewritten merely to distribute deployment.
