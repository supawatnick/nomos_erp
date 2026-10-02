# Phase 0–3 Four-Core Alignment Review

Date: 2026-10-02
Status: **PASS — ALIGNMENT PATCH COMPLETE**

## Purpose
Backport the approved four-core ERP direction into Phase 0–3 contracts before Phase 4 begins, without pretending future modules are already implemented and without invalidating completed acceptance gates.

## Result by completed phase

### Phase 0 — specification/architecture
PASS remains valid. Contracts were strengthened:
- DATA-MODEL now reserves CRM leads/opportunities/activities, QT revision, RFQ/supplier responses and Finance GL/AR/AP/invoice/payment/fiscal/tax/FX/posting-registry entities.
- DOCUMENT-LIFECYCLE now defines QT revision/acceptance, Sales/Procurement progress, Finance posting/settlement and cross-core transition rules.
- AUTHORIZATION-MATRIX reserves stable permission namespaces for CRM, Sales, Procurement and Finance.
- API-AUDIT-CONTRACT reserves cross-core envelope, errors and audit taxonomy.
- NUMBERING reserves QT/SO/PR/RFQ/PO/GR and Finance document families with statutory-numbering caveat.

### Phase 1 — engineering foundation
No runtime redesign required.
Existing FastAPI/PostgreSQL/outbox/idempotency/CI layering remains valid.
Contract requirement added: exact decimal/currency handling and cross-core application/outbox contracts remain authoritative; future modules must not integrate by direct table mutation.

### Phase 2 — SaaS platform core
No auth/session/RBAC/audit migration is required by this alignment.
RequestContext remains server-derived. Future authorization scope must support legal_entity/branch/warehouse intersections; reserved permissions are not seeded until their implementation phases.
Finance is explicitly legal-entity scoped.

### Phase 3 — catalog/warehouse
No Phase 3 schema rollback/rework required.
Product/Unit/Warehouse/Location and document_sequences remain valid.
Commercial/accounting product defaults, tax classifications and account mappings are intentionally deferred to typed later-phase configuration instead of polluting Phase 3.
Existing document_sequences is the foundation for future QT/SO/PO/Finance numbering.

## Phase 4 guardrails added
- Inventory remains physical quantity authority.
- Stable source_type/source_id/source_number + correlation/idempotency must survive posting.
- Goods Receipt/Return and Delivery/Return later invoke Inventory contracts; they never mutate ledger tables.
- Inventory may emit valuation/posting facts, but Finance owns journals.
- Phase 4 cannot couple to future Sales/Procurement/Finance persistence.

## Files aligned
- docs/DATA-MODEL.md
- docs/ERD-PHASE-1-6.md
- docs/DOCUMENT-LIFECYCLE.md
- docs/AUTHORIZATION-MATRIX.md
- docs/API-AUDIT-CONTRACT.md
- docs/NUMBERING.md
- PROJECT-STATUS.md

This review complements docs/FOUR-CORE-ERP-REVISION.md.

## Acceptance
PASS requires documentation consistency, unchanged Phase 0–3 functional baseline, green repository CI and clean synchronized host 73. Phase 4 remains the next executable implementation phase.
