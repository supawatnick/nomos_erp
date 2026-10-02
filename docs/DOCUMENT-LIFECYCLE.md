# Document Lifecycle

## Principle
Status is a domain state machine, not a cosmetic UI label. Every document declares allowed transitions, permissions, validation, version/concurrency behavior and side effects. State transitions use application commands; clients do not arbitrarily PATCH status.

## Common concepts
DRAFT -> SUBMITTED/PENDING_APPROVAL -> APPROVED/CONFIRMED -> POSTED/COMPLETED.
Exception/terminal states may include REJECTED, EXPIRED, ON_HOLD, CANCELLED, CLOSED and REVERSED. Not every document uses every state.

A document that has produced a posted physical or financial effect is not silently edited/deleted. Corrections use explicit reversal/return/credit/debit/adjustment flows.

## Inventory
Inventory transaction: DRAFT/command validation -> POSTED -> REVERSED where eligible.
Only POSTED transactions affect on-hand. Posted rows are immutable.
Reservation is separate from on-hand: ACTIVE/ALLOCATED/PARTIALLY_FULFILLED/FULFILLED/RELEASED/EXPIRED according to Sales policy.

## Procurement & Purchasing
Purchase Request: DRAFT -> PENDING_APPROVAL -> APPROVED / REJECTED -> SOURCING / CONVERTED / CANCELLED.
RFQ: DRAFT -> SENT -> RESPONSES_RECEIVED -> AWARDED / CLOSED / CANCELLED.
Purchase Order: DRAFT -> PENDING_APPROVAL -> APPROVED -> SENT -> PARTIALLY_RECEIVED -> RECEIVED -> CLOSED; ON_HOLD/CANCELLED are controlled exceptions.
PO approval/sending never changes stock.
Goods Receipt: DRAFT -> POSTED -> REVERSED when correction is required. POSTED invokes Inventory receive atomically/through the defined contract.
Purchase Return: DRAFT -> POSTED -> REVERSED where eligible. POSTED invokes Inventory decrease.
PO operational status derives from line-level ordered/received/returned progress; it is not manually overwritten to fake completion.

## Sales & CRM
Lead/Opportunity: OPEN -> QUALIFIED -> WON / LOST / CANCELLED as applicable.

Quotation (QT): DRAFT -> SENT -> ACCEPTED / REJECTED / EXPIRED / CANCELLED.
- QT has explicit revision/version.
- Material edit after SENT creates a new revision or explicit audited re-open transition.
- ACCEPTED records actor/time/version and preserves the accepted commercial snapshot.
- Expiry is based on explicit validity date/policy.
- QT acceptance may create/seed a Sales Order but does not post Inventory or Accounting.

Sales Order: DRAFT -> CONFIRMED -> RESERVED/PARTIALLY_RESERVED -> PROCESSING -> PARTIALLY_FULFILLED -> FULFILLED -> CLOSED, with controlled ON_HOLD/CANCELLED.
- Confirmation does not reduce on-hand.
- Reservation changes available quantity only.
- Delivery invokes Inventory issue.
- Cancellation releases eligible reservation.
- Operational progress reconciles ordered/reserved/delivered/returned and later invoiced/paid facts.

Delivery: DRAFT -> POSTED -> REVERSED/RETURNED according to correction policy.
Sales Return: DRAFT -> POSTED -> REVERSED where eligible.

## Finance & Accounting
Customer Invoice / Supplier Invoice: DRAFT -> POSTED -> PARTIALLY_SETTLED -> SETTLED, with VOID/CREDITED/DEBITED only through permitted correction policy.
Receipt/Payment: DRAFT -> POSTED -> ALLOCATED/PARTIALLY_ALLOCATED -> REVERSED where eligible.
Journal Entry: DRAFT -> POSTED -> REVERSED.
Fiscal Period: OPEN -> SOFT_CLOSED (optional policy) -> CLOSED; reopening is high-risk, permissioned and audited.

Rules:
- POSTED journals/invoices/payment effects are immutable.
- Posting requires an open eligible fiscal period.
- Every journal must balance before commit.
- Source posting is idempotent and retains source module/type/id/number.
- Credit/debit notes and reversals link to the original effect; no destructive rewrite.
- Settlement/allocation state is derived from exact allocations, not manually set.

## Cross-core transition rule
A source document advances to a state that claims a cross-core effect only when that effect succeeds or a durable explicitly-defined asynchronous state exists. Examples:
- Goods Receipt cannot claim POSTED if Inventory receive rolled back.
- Delivery cannot claim POSTED if Inventory issue rolled back.
- Finance cannot mark a source as financially posted merely because an outbox notification was attempted.
Cross-core retries use stable idempotency identities.

## Approval invalidation
Approval binds to a specific immutable version/fingerprint. Material edits invalidate prior approval and require revalidation/reapproval according to policy.

## Numbering
Human document numbers are tenant-scoped business identifiers separate from immutable IDs. Allocation is concurrency-safe and may scope by legal entity/branch/period. Statutory Finance numbering may require stricter no-reuse/gap/audit policy than operational documents.

## Cancellation vs reversal vs return
Cancel: no irreversible/posted effect exists or explicit cancellation rules permit it.
Reversal: opposite durable effect after posting.
Return: business movement of goods back through a dedicated source document.
Credit/debit note: financial correction/adjustment linked to an invoice.
UI/API must not use these interchangeably.

## Required lifecycle tests
For each implemented document: allowed/forbidden transition matrix, stale version, permission denial, cross-tenant source/reference, material edit after approval, idempotent retry, partial progress reconciliation and immutable posted-history behavior.
