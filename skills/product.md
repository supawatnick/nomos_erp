# Product Skill

- Start from docs/PRODUCT.md and docs/MASTER-PLAN.md.
- NOMOS has four first-class ERP cores: Finance & Accounting, Inventory & Warehouse, Procurement & Purchasing, Sales & CRM.
- Do not call the product a complete ERP release until all four core release gates are operational.
- Write acceptance criteria before ambiguous business behavior.
- Prefer configuration over customer-specific forks.
- Keep phase boundaries explicit while preserving cross-core integration contracts early.
- Sales/CRM includes QT and order tracking as mandatory scope.
- Procurement includes sourcing/RFQ/PO/receipt tracking as core scope.
- Finance/Accounting is required for Core ERP V1; it is not an optional future add-on.
- Optimize operator workflows for speed without weakening audit, confirmation or authorization.
- Thai and English UX must use stable business terms.
- A workflow is incomplete when error/recovery and partial-progress states are undefined.
- When product behavior changes, update the relevant domain document, roadmap/status and tests.
