# Phase 11 Review — Operational Reporting

Status: **IN PROGRESS**

## Contract basis
- docs/MASTER-PLAN.md Phase 11
- docs/API-AUDIT-CONTRACT.md
- docs/AUTHORIZATION-MATRIX.md
- docs/WEB-DESIGN-CONTRACT.md
- Phase 4–10 domain/review contracts

## Required delivery
- Tenant-scoped operational reports for Inventory, Procurement, Sales/CRM and management.
- Explicit allowlisted report catalog; no arbitrary SQL endpoint or client-provided SQL fragments.
- Bounded date range, row limit and deterministic ordering.
- Server-side CSV and XLSX export from the same bounded report definitions.
- report.read for report data and report.export in addition for export.
- Safe spreadsheet output, including formula-injection protection.
- Web reporting workspace with loading/empty/error/export states.
- Acceptance proving tenant isolation, permission denial, bounds and export safety.

## Existing baseline
Phase 6 already provides an Inventory operational summary and client-side CSV. Phase 11 generalizes reporting across implemented operational modules and moves export generation to the server.

## Exit gate
Phase 11 is not PASS until common operational/pipeline/order-tracking reports are available without arbitrary SQL, exports are bounded and safe, and full API/Web/security/dependency CI is green.
