# NOMOS ERP

NOMOS ERP is an inventory-first, multi-tenant ERP designed for small and growing businesses.

## Product vision
**ERP you can operate without opening the ERP.**

NOMOS provides:
- Responsive web application
- LINE Messaging API interface for queries and operational commands
- Inventory ledger and multi-warehouse stock
- Role-based access control and approvals
- Auditability for every stock-changing action
- SaaS-ready multi-tenancy
- Future AI assistant through controlled ERP tools/APIs

## MVP
1. Authentication, tenant and RBAC
2. Products/SKUs, categories and units
3. Warehouses and locations
4. Stock receive, issue, transfer and adjustment
5. Inventory ledger, balances and history
6. Low-stock alerts and dashboard
7. LINE account linking and stock queries
8. LINE operational requests with confirmation/approval
9. Audit logs

## Architecture
Web and LINE are clients of the same backend. Business rules must never be duplicated in channel-specific code.

See `AGENTS.md` and `docs/`.
