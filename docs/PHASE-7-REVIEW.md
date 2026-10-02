# Phase 7 Review — Business Partners & CRM Foundation

Date: 2026-10-02
Status: **PASS**

## Outcome
Phase 7 adds the shared commercial identity and CRM foundation required by later Procurement and Sales phases without prematurely introducing PR/RFQ/PO/QT/SO documents.

## Business partners
business_partners is tenant scoped and may be:
- customer only
- supplier only
- both customer and supplier

A partner must have at least one role. Partner code is unique per tenant. Contacts and addresses are child records using composite tenant references. Primary contact/address handling is explicit.

## CRM
Phase 7 adds:
- leads
- opportunities
- activities/notes
- owner tenant-user references

Lead lifecycle is explicit:
OPEN -> QUALIFIED -> WON / LOST / CANCELLED.

Opportunities reference a tenant-owned lead and/or customer partner, use exact Decimal estimated amount and explicit currency.

Activities support NOTE, CALL, EMAIL, MEETING and TASK and must target a partner, lead or opportunity.

## Boundaries
Phase 7 does not create:
- Quotation
- Sales Order
- Purchase Request
- RFQ
- Purchase Order
- inventory movement
- accounting posting

Phase 8 owns Procurement documents.
Phase 9 owns QT/SO and fulfillment orchestration.

## Security and audit
Permissions:
- partner.read
- partner.manage
- crm.read
- crm.manage

Partner/CRM queries and references are tenant scoped.
Cross-tenant child/reference attempts are rejected without trusting client tenant IDs.
Partner, lead, opportunity and activity mutations write audit evidence; activities emit outbox facts.

## Web
Added:
- /partners
- /crm

The workspace now exposes Business Partners and CRM alongside the completed Inventory ERP MVP.

## Acceptance
PostgreSQL acceptance covers:
- customer + supplier dual role
- mandatory partner role
- contacts and addresses
- cross-tenant partner child rejection
- lead lifecycle
- opportunity exact amount
- activity history
- explicit absence of QT/SO/PO tables in Phase 7

Web acceptance covers:
- partner dual-role controls
- lead/opportunity routes
- lead qualification workflow
- no Sales Order coupling
- workspace navigation

## Verification
Implementation gate PASS:
- Ruff
- mypy
- Alembic upgrade through 0007_phase7_crm
- PostgreSQL pytest suite
- pip-audit
- npm ci
- npm audit high
- Web lint/typecheck/tests/build
- gitleaks

Final documentation commit must pass the same CI before terminal closure.

## Next
Phase 8 — Procurement & Purchasing.
