# NOMOS Skills Index

These files are implementation instructions for contributors and coding agents. The docs/ directory is the product/domain source of truth; skills describe how to implement it.

Always read:
- product.md before changing scope/workflows
- architecture.md before adding a service/boundary
- security.md for every feature
- testing.md before calling a feature complete

By core:
- inventory.md for Inventory & Warehouse
- procurement.md for Procurement & Purchasing
- sales-crm.md for Sales & CRM, QT and order tracking
- finance.md for Finance & Accounting
- documents.md for business-document lifecycle/numbering

By technical surface:
- backend.md + api.md for FastAPI/application work
- frontend.md for Next.js work
- database.md for schema/query work
- multi-tenancy.md for tenant boundaries
- rbac.md for permissions
- approvals.md for approval/confirmation
- line.md for LINE
- devops.md for runtime/CI/deployment
- ai.md for model/assistant features

## Four-core rule
A feature touching more than one ERP core must read every affected core skill and use explicit application contracts. Never implement cross-core behavior by directly mutating another module's tables.
