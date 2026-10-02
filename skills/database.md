# Database Skill

- PostgreSQL is authoritative.
- All tenant-owned rows are tenant-scoped.
- Use migrations for every schema change.
- Use foreign keys, checks and unique constraints to reinforce invariants.
- Use NUMERIC/DECIMAL for exact business quantities/currency.
- Inventory history is ledger-based.
- A balance table is a projection and must reconcile to the ledger.
- Index tenant_id plus common lookup/filter columns.
- Use explicit row-lock/concurrency strategy for stock-changing operations.
- Acquire multiple locks in deterministic order.
- Idempotency records are tenant/actor scoped and request-fingerprinted.
- Prefer additive/backward-compatible migrations.
- Review query plans for high-volume reports.
- Include concurrency and idempotency tests for stock mutations.