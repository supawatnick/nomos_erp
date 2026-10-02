# Phase 12 Review — Finance & Accounting

Status: **IN PROGRESS**

## Contract basis
- docs/MASTER-PLAN.md Phase 12
- docs/ACCOUNTING-BOUNDARY.md
- docs/AUTHORIZATION-MATRIX.md
- docs/DOCUMENT-LIFECYCLE.md
- docs/NUMBERING.md
- docs/API-AUDIT-CONTRACT.md
- docs/MODULES.md
- docs/WEB-DESIGN-CONTRACT.md
- skills/finance.md

## Required delivery
- Legal-entity-scoped Chart of Accounts and posting configuration.
- Fiscal periods with open/closed posting enforcement.
- Immutable balanced journal/GL with exact decimals, source provenance, idempotent posting and reversal.
- Customer/Supplier invoices, AR/AP open items, receipts/payments and exact allocations.
- Effective-dated tax configuration and explicit exchange-rate provenance.
- Inventory valuation/costing integration and explicit posting rules for eligible Inventory/Procurement/Sales source facts.
- Trial balance/financial statement foundation and AR/AP/inventory subledger-to-GL reconciliation.
- Tenant/legal-entity isolation, permission denial, closed-period, unbalanced, duplicate-source and immutable-posted acceptance.
- Finance Web surfaces following the ERP design contract.

## Exit gate
Phase 12 is not PASS until eligible Inventory/Purchasing/Sales documents create balanced, idempotent and auditable financial effects; subledgers reconcile to GL; closed periods reject posting; and all API/Web/security/dependency/CI/runtime gates are green.

## Work log
- 2026-10-02: Phase 11 baseline verified and Phase 12 contracts read before implementation.
