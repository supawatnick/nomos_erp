# Document Numbering

Human-readable document numbers are separate from immutable database IDs.

## Requirements
- tenant scoped
- concurrency safe
- configurable by document type
- optionally segmented by legal entity/branch and fiscal/calendar period
- unique under the configured scope
- allocated server-side
- never used as the only foreign key

## Example patterns
PO-BKK-2026-000001
SO-BKK-2026-000001
GR-BKK-2026-000001
TR-2026-000001

Examples are not hardcoded defaults.

## Allocation
Use a transactional sequence/allocation record such as document_sequences keyed by tenant + document type + configured scope + period. Lock/update allocation atomically. Do not calculate next number with SELECT MAX(number)+1.

## Gaps
Number-gap policy is document/jurisdiction dependent. Technical IDs and business numbers remain distinct so stricter statutory numbering can be introduced for tax/accounting documents later.
