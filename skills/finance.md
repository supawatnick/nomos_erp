# Finance & Accounting Skill

Before Finance work read docs/ACCOUNTING-BOUNDARY.md, docs/DOCUMENT-LIFECYCLE.md, docs/NUMBERING.md and docs/MODULES.md.

- Finance is a first-class ERP core, not a reporting add-on.
- Own GL, AR/AP, invoices, receipts/payments, fiscal periods and posting rules in Finance.
- Never let Finance rewrite Inventory quantity or Sales/Procurement source documents.
- Posted journals are immutable; correction uses reversal/credit/debit/adjustment.
- Enforce debit == credit before commit.
- Use exact Decimal values and explicit currency/exchange-rate provenance.
- Reject posting into closed/locked fiscal periods.
- Make source posting idempotent with a unique source/posting identity.
- Preserve tenant + legal entity + source document provenance on every journal.
- Tax codes/rates are effective-dated configuration; never hardcode VAT.
- Test AR/AP/Inventory subledger reconciliation to GL control accounts.
- Every financial mutation needs authorization, audit and negative tests.
