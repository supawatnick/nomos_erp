# Database Skill

- PostgreSQL is authoritative.
- All tenant-owned rows are tenant-scoped.
- Use migrations for every schema change.
- Use foreign keys, checks and unique constraints to reinforce invariants.
- Use DECIMAL/NUMERIC for exact business quantities/currency.
- Inventory history is ledger-based.
- Index tenant_id plus common lookup/filter columns.
- Review query plans for high-volume reports.
- Include concurrency and idempotency tests for stock mutations.
