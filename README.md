# NOMOS ERP

NOMOS ERP is an inventory-first, multi-tenant ERP for small and growing businesses.

> Product idea: **ERP you can operate without opening the ERP.**

The same business services power the responsive Web application, API and LINE Messaging API experience. Channel-specific code may format input/output, but it must not own business rules.

## Product goals

- Fast inventory operations with a clear audit trail
- Multi-company SaaS architecture with strong tenant isolation
- Multi-warehouse and location/bin inventory
- Safe operational commands through LINE
- Configurable RBAC, confirmations and approvals
- Thai/English ready UX
- API-first design so mobile, integrations and AI can be added safely
- Deploy locally with Docker Compose and scale to Kubernetes later

## MVP scope

1. Authentication, tenant membership and RBAC
2. Product/SKU, category and unit masters
3. Warehouses and locations
4. Receive, issue, transfer and adjustment
5. Ledger-based inventory balances and movement history
6. Low-stock rules and dashboard
7. LINE account linking and inventory queries
8. LINE mutation requests with confirmation and approval when required
9. Audit log and operational observability
10. Backup/restore and production deployment baseline

Purchasing and sales are documented as the next business modules. Full accounting/GL, payroll and manufacturing are not MVP requirements.

## Target stack

- Web: Next.js + TypeScript
- API: Python + FastAPI
- Database: PostgreSQL
- Cache/queue: Redis when asynchronous work is required
- Local runtime: Docker Compose
- Production target: containers; Kubernetes when scale requires it
- LINE: LINE Messaging API webhook
- API contract: OpenAPI generated from FastAPI

## Repository layout

~~~
apps/
  api/              # FastAPI application
  web/              # Next.js application
docs/               # Product and engineering source of truth
skills/             # Instructions for coding agents/contributors
infra/              # Local/production infrastructure assets
tests/              # Cross-service and end-to-end tests
AGENTS.md
CONTRIBUTING.md
docker-compose.yml
.env.example
~~~

## Documentation map

Start with:
- docs/PRODUCT.md — product scope, personas and acceptance criteria
- docs/ARCHITECTURE.md — system boundaries and data flow
- docs/DATABASE.md — persistence model and invariants
- docs/AUTH-RBAC.md — authentication and permissions
- docs/INVENTORY.md — inventory domain rules
- docs/API.md — API conventions and resources
- docs/LINE-INTEGRATION.md — LINE identity and command safety
- docs/APPROVALS.md — confirmation/approval workflow
- docs/SECURITY.md — security baseline
- docs/DEVELOPMENT.md — local development and Definition of Done
- docs/DEPLOYMENT.md — environments, migration and backup strategy
- docs/OBSERVABILITY.md — logs, metrics, traces and alerts
- docs/ROADMAP.md — delivery phases
- docs/PURCHASING.md and docs/SALES.md — post-MVP business modules
- docs/AI-ASSISTANT.md — controlled future AI assistant

## Core engineering rules

- Inventory is ledger-based; never treat a mutable stock field as the system of record.
- Every tenant-owned record is tenant-scoped.
- Web, LINE and future AI call the same application services.
- Stock-changing operations are transactional, idempotent when retriable and audited.
- Posted business transactions are corrected by reversal/correction flows, not silent edits.
- Exact decimal types are used for quantities and money.
- Cross-tenant access is denied and covered by automated tests.
- Secrets never enter source control.

Read AGENTS.md before implementation.