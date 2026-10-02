# Document Lifecycle

## Principle
Status is a domain state machine, not a cosmetic UI label. Each document type declares allowed transitions, permissions, validation and side effects.

## Common conceptual states
DRAFT -> SUBMITTED/PENDING_APPROVAL -> APPROVED/CONFIRMED -> POSTED/COMPLETED
Terminal/exception states may include REJECTED, CANCELLED and REVERSED.

Not every document uses every state.

## Inventory
Draft/pending records do not affect stock. Only POSTED inventory transactions affect stock. A posted inventory transaction is not edited or deleted in ordinary operation. Correction creates a linked reversal or compensating transaction.

## Purchasing
Purchase Request: draft -> submitted -> approved/rejected/cancelled.
Purchase Order: draft -> submitted/approved -> issued -> partially_received -> received/closed/cancelled.
PO state alone never changes physical stock.
Goods Receipt: draft -> posted -> reversed where correction is needed. Posting invokes Inventory receive effects.
Purchase Return: posting invokes Inventory issue/decrease effects.

## Sales
Quotation: draft -> sent -> accepted/rejected/expired/cancelled.
Sales Order: draft -> confirmed -> partially_fulfilled -> fulfilled/closed/cancelled.
Sales Order does not directly reduce on-hand. Reservation, when enabled, changes available quantity.
Delivery: draft -> posted -> reversed/returned as defined. Posting invokes Inventory issue effects.
Sales Return: posting invokes Inventory receive effects.

## Approval invalidation
An approval binds to a specific version/fingerprint of the business request. Material edits invalidate prior approval and require revalidation/reapproval according to policy.

## Numbering
Human document numbers are tenant-scoped business identifiers, separate from immutable database IDs. Sequence allocation must be concurrency-safe. Number policy may include document type, branch/legal entity and fiscal period.

## Cancellation versus reversal
Cancel means the document has not produced an irreversible/posted business effect, or cancellation rules explicitly permit it. Reversal creates an opposite durable effect after posting. UI and APIs must not use these terms interchangeably.
