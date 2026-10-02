# Inventory Skill

Before editing inventory code, read docs/INVENTORY.md and docs/DATABASE.md.

Rules:
- Only POSTED ledger transactions affect stock.
- Never silently update stock as the authoritative history.
- Receive increases destination.
- Issue decreases source and rejects insufficient stock by default.
- Transfer decreases source and increases destination atomically.
- Adjustment requires reason and permission; policy may require approval.
- Posted transaction correction uses reversal/compensating entry.
- Validate tenant ownership of product/unit/location.
- Validate quantity precision.
- Use idempotency for retriable commands.
- Use a concurrency-safe balance check and write transaction.
- Create audit evidence.
- Tests must include duplicates, concurrency, insufficient stock and reversal.