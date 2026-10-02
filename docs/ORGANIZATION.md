# Organization Model Contract

Status: PASS — Phase 0.

## Hierarchy and ownership
Tenant is the SaaS/security/commercial boundary. Legal Entity is a juridical/accounting company inside one tenant. Branch is an operating/tax/organizational subdivision of exactly one Legal Entity. Warehouse is a physical/logical inventory facility owned by exactly one Legal Entity and optionally assigned to one Branch. Location belongs to exactly one Warehouse.

Tenant != Legal Entity != Branch != Warehouse != Location.

## Required relationships
Tenant 1..N LegalEntity.
LegalEntity 1..N Branch.
LegalEntity 1..N Warehouse.
Branch 0..N Warehouse.
Warehouse 1..N Location.

If warehouse.branch_id is present, the Branch MUST belong to the same legal_entity_id and tenant as the Warehouse. Database migrations must enforce this with an appropriate composite candidate key/FK rather than application validation alone.

## Defaults
Tenant defaults: locale, timezone, base currency; these are onboarding conveniences, not replacements for legal-entity configuration.
Legal Entity: base currency, country, timezone are authoritative defaults for its business documents unless a document explicitly records an allowed override.
Tenant User may have default_branch_id for UX. It grants no authorization by itself.
Warehouse has no implicit default stock location. A workflow must select/derive an explicit stock-enabled Location.
No global "current warehouse" is trusted as authorization context.

## Lifecycle
Legal Entity/Branch/Warehouse/Location referenced by business history is archived/deactivated, not deleted.
Archiving a parent does not rewrite historical documents and must prevent new operations that require an active parent.
A Warehouse/Location with on-hand stock cannot be archived until policy-controlled transfer/zeroing conditions pass.
Location hierarchy cannot cross warehouse boundaries and must reject cycles.

## Transaction organization
Every inventory transaction records legal_entity_id. branch_id is optional only where the operation legitimately has no branch assignment. Locations determine warehouse; warehouse ownership must match transaction legal entity. Cross-legal-entity physical movement is NOT a simple TRANSFER: future intercompany/inter-entity workflow must use explicit paired business documents/accounting treatment.

## Multi-company future
A Tenant may contain multiple Legal Entities from the start. Shared product master is tenant-scoped in Phase 1–6. Entity-specific price/tax/accounting policies may be added later without duplicating Product identity.

## Required tests
- cross-tenant entity/branch/warehouse/location reference denied;
- branch cannot attach to foreign legal entity;
- warehouse branch/legal-entity mismatch rejected at DB boundary;
- location cannot attach/cross-parent another warehouse;
- archived hierarchy cannot accept new stock transaction;
- tenant-user default branch gives no extra permission;
- stock-bearing location cannot be silently archived;
- cross-legal-entity location transfer rejects as ordinary TRANSFER.
