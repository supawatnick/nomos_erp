# Frontend Skill

When working on the Web ERP:
- Use Next.js + TypeScript.
- Treat API as the source of business truth.
- Do not duplicate server authorization/domain rules as security controls.
- Build reusable tables, forms, dialogs, status badges and confirmation components.
- Always make tenant, warehouse, SKU, quantity, unit and transaction state clear.
- Stock-changing actions require an explicit normalized review/confirmation step.
- Approval state must be visible and refreshable.
- Provide loading, empty, error and retry states.
- Avoid optimistic UI that claims a stock mutation succeeded before server confirmation.
- Use stable API error codes for friendly localized messages.
- Design for Thai and English.
- Support keyboard/accessibility basics and responsive operator workflows.