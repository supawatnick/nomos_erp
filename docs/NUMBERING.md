# Document Numbering

Human-readable document numbers are separate from immutable database IDs.

## Requirements
- tenant scoped
- concurrency safe
- configurable by document type
- optionally segmented by legal entity/branch and fiscal/calendar period
- unique under configured scope
- allocated server-side
- never the only foreign key
- source linkage uses immutable ID plus human number for traceability

## Reserved document-type families
Operational examples:
QT quotation
SO sales order
DLV delivery
SRT sales return
PR purchase request
RFQ request for quotation
PO purchase order
GR goods receipt
PRT purchase return
TR inventory transfer
ADJ inventory adjustment

Finance examples:
CINV customer invoice
SINV supplier invoice
CRN credit note
DBN debit note
RCT receipt
PAY payment
JV journal voucher

Codes/prefixes are policy/configuration contracts, not hardcoded UI strings.

## Example patterns
QT-BKK-2026-000001
PO-BKK-2026-000001
GR-BKK-2026-000001
CINV-TH01-2026-000001
JV-TH01-2026-000001

## Allocation
Use document_sequences keyed by tenant + document type + configured legal-entity/branch/period scope. Lock/update atomically. Never SELECT MAX(number)+1. Allocation and persistence rules must define whether a number is reserved at draft, submit or posting time for each document class.

## Revisions
QT revision is not a new identity by accident. Preserve immutable quotation ID and explicit revision/version semantics. Display policy may render QT-... Rev.2 or allocate separate revision numbers, but accepted-version traceability must be unambiguous.

## Gaps and statutory documents
Gap policy is document/jurisdiction dependent. Operational documents may tolerate committed allocation gaps according to policy. Tax/accounting documents may require stricter legal-entity/fiscal-series rules, void tracking, no number reuse and explicit cancellation evidence. Phase 12 must implement jurisdiction/configuration policy rather than assuming one global no-gap rule.

## Tests
Concurrent allocation uniqueness, nullable scope uniqueness, legal-entity/branch ownership, period rollover, retry/idempotency and statutory no-reuse policy when enabled.
