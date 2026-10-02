# Roadmap

## Phase 0 — Foundation

Deliverables:
- repository standards and CI
- API/Web skeleton
- Docker Compose local dependencies
- PostgreSQL migrations
- auth, tenant membership and RBAC
- audit and request correlation
- production configuration baseline

Exit: a user can authenticate into an isolated tenant and protected API tests prove cross-tenant denial.

## Phase 1 — Inventory MVP

Deliverables:
- products/categories/units
- warehouses/locations
- ledger + balance projection
- receive/issue/transfer/adjust/reversal
- history and low-stock dashboard
- concurrency/idempotency tests

Exit: inventory operations are atomic, auditable, retry-safe and concurrency-tested.

## Phase 2 — LINE MVP

Deliverables:
- LINE tenant configuration
- secure account linking
- signed/deduplicated webhook
- stock/product queries
- confirmation flow
- receive/issue/transfer requests

Exit: duplicate webhook/reply does not duplicate stock movement and permissions match Web.

## Phase 3 — Approval

Deliverables:
- policy engine baseline
- approval request/decision
- Web and LINE approval UX
- expiry/cancel/revalidation
- separation-of-duties option

Exit: sensitive mutation cannot execute without valid current approval.

## Phase 4 — Production hardening

Deliverables:
- staging/production deployment
- CI security scans
- logs/metrics/alerts
- backup + successful restore test
- load/concurrency test
- incident/runbook baseline

Exit: ready for controlled pilot customers.

## Phase 5 — Purchasing

Suppliers, purchase requests, purchase orders, partial goods receipt and approval.

## Phase 6 — Sales

Customers, sales orders, reservation, picking/issue, delivery and partial fulfillment.

## Phase 7 — AI Assistant

Natural-language tool calling and reporting through constrained deterministic ERP tools.

## Phase 8 — SaaS scale

Billing/subscriptions, automated provisioning, quotas, support tooling, retention/privacy workflows, advanced observability, Kubernetes/HA where justified.

## Later candidates

Lot/serial/expiry, barcode, cycle counting, costing/valuation, returns, accounting integration, mobile/PWA enhancements and external integration marketplace.