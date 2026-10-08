# NOMOS ERP

**A modern, audit-first ERP platform for connected business operations.**

NOMOS ERP brings inventory, procurement, sales, CRM, finance, approvals, reporting, and master data into one coherent workspace. The project is designed around a simple principle: business rules belong to the domain, not to the screen that happens to call them.

The result is an API-first ERP architecture where Web, integrations, messaging channels, automation, and future AI experiences can share the same governed application services.

## What NOMOS covers

| Area | Highlights |
| --- | --- |
| Inventory | Stock balances, movements, receive, issue, transfer, adjustment, counts, reorder and reversals |
| Procurement | Purchase requests, RFQs, supplier comparison, purchase orders, receipts and returns |
| Sales | Quotations, revisions, sales orders, reservations, delivery and returns |
| CRM | Partners, contacts, addresses, leads, opportunities and activities |
| Finance | Chart of accounts, fiscal periods, journals, AR/AP invoices, payments and allocations |
| Master Data | Products, categories, units, warehouses, locations and organization structure |
| Approvals | Policy-driven approval requests, decisions and controlled execution |
| Reporting | Operational reports and export workflows |
| Administration | Tenant users, roles, permissions and immutable audit evidence |
| Imports | Staged validation and controlled commit of business data |

## Design philosophy

NOMOS favors explicit business lifecycles over generic CRUD.

Master data can be created, maintained and archived. Posted transactions are not silently rewritten or deleted: they move through domain-specific actions such as submit, approve, cancel, reverse, receive, deliver, return or allocate. This keeps operational history understandable and makes auditability a first-class property of the system.

Other core principles include:

- **Tenant isolation by design** — business data is scoped to its owning tenant.
- **Ledger-based inventory** — stock truth is derived from posted movements rather than a casually mutable quantity field.
- **Audit-first operations** — meaningful mutations carry actor, request and business context.
- **Idempotent posting** — retriable commands are designed to avoid accidental duplicate effects.
- **Server-authoritative permissions** — the API remains the security boundary regardless of client.
- **Exact business arithmetic** — quantities and monetary values use decimal semantics.
- **Shared application services** — channels reuse domain logic instead of reimplementing it.

## Architecture

```text
┌──────────────────────────────────────────────────────────┐
│                     Experience Layer                     │
│        Web · Integrations · Messaging · Automation       │
└───────────────────────────┬──────────────────────────────┘
                            │
                    FastAPI / OpenAPI
                            │
┌───────────────────────────▼──────────────────────────────┐
│                    Application Layer                     │
│  Inventory · Procurement · Sales · CRM · Finance · RBAC │
│               Approvals · Reporting · Audit              │
└───────────────────────────┬──────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────┐
│                      Data Layer                          │
│                  PostgreSQL · Redis                      │
└──────────────────────────────────────────────────────────┘
```

The browser application is built with **Next.js and TypeScript**. Business APIs are implemented with **FastAPI and Python**, backed by **PostgreSQL**. Schema evolution is managed with **Alembic**, while container-based development is supported through **Docker Compose**.

## Repository structure

```text
apps/
  api/          FastAPI application and domain services
  web/          Next.js ERP workspace
  worker/       Background worker entry points

docs/           Product, architecture and domain documentation
infra/          Infrastructure and deployment assets
skills/         Contributor and coding-agent guidance
tests/          Cross-service test assets

AGENTS.md
CONTRIBUTING.md
docker-compose.yml
.env.example
```

## Business flows

### Procure to stock
Purchase Request → RFQ → Supplier Response → Award → Purchase Order → Approval → Goods Receipt → Supplier Return

### Quote to cash
Lead / Opportunity → Quotation → Revision → Acceptance → Sales Order → Reservation → Delivery → Sales Return

### Inventory control
Receive → Balance → Transfer / Issue / Adjustment → Movement History → Reversal

### Financial control
Fiscal Period → Journal / Invoice / Payment → Allocation → Reversal and audit evidence

## Security & governance

NOMOS treats authorization and traceability as domain concerns rather than UI features. Tenant membership, role-based permissions, approval policies, idempotency keys, audit records and transaction state checks are enforced server-side.

Sensitive configuration is expected to be supplied through environment-specific secret management. Repository documentation intentionally avoids publishing environment addresses, credentials or private deployment identifiers.

## Documentation

The `docs/` directory contains the deeper design material behind the project:

- `PRODUCT.md` — product scope and user journeys
- `ARCHITECTURE.md` — boundaries, components and data flow
- `DATABASE.md` — persistence model and invariants
- `AUTH-RBAC.md` — authentication and authorization model
- `INVENTORY.md` — stock and movement rules
- `PURCHASING.md` — procurement domain
- `SALES.md` — sales lifecycle
- `APPROVALS.md` — controlled decision workflows
- `API.md` — API conventions
- `SECURITY.md` — security baseline
- `OBSERVABILITY.md` — operational telemetry
- `DEVELOPMENT.md` — development workflow
- `DEPLOYMENT.md` — deployment concepts

## Technology

**Frontend:** Next.js · React · TypeScript  
**Backend:** Python · FastAPI · SQLAlchemy · Alembic  
**Data:** PostgreSQL · Redis  
**Quality:** Ruff · mypy · pytest · Node test runner · runtime acceptance checks  
**Infrastructure:** Docker Compose · reverse proxy · container-ready services

---

NOMOS ERP is an exploration of how a modern ERP can remain operationally practical while keeping domain boundaries, auditability and data integrity explicit in the architecture.
