# Document Skill

Before business-document work read docs/DOCUMENT-LIFECYCLE.md and docs/NUMBERING.md.
- Status is a state machine with explicit transitions.
- Database ID and human document number are separate.
- Number allocation is tenant-scoped and concurrency-safe; never MAX()+1.
- Posted effects are immutable; cancellation and reversal are distinct.
- Material edits invalidate approvals bound to an earlier version/fingerprint.
- Each domain owns concrete document tables; do not build a universal document mega-table.
- Partial receipt/delivery is first-class and must reconcile line quantities.
