# Accounting and Costing Boundary

Accounting is not required for the first Inventory Web MVP, but the architecture must preserve a clean path to it.

## Separation
Inventory owns physical quantity and movement history.
Purchasing owns procurement documents and receipt intent.
Sales owns order, reservation and delivery intent.
Accounting owns journals, ledger accounts, receivables/payables, fiscal periods, invoices/payments and financial posting rules.
Costing owns or collaborates on valuation policy without changing physical quantity semantics.

## Business effects
Purchase Order: no physical or accounting stock posting by itself.
Goods Receipt: physical inventory increase; may later create valuation/accrual effects through accounting policy.
Purchase Return: physical decrease and corresponding financial effect when accounting is enabled.
Sales Order: no physical decrease; may reserve availability.
Delivery: physical decrease; may later recognize COGS/related entries according to accounting policy.
Invoice/Payment: financial documents; must not directly rewrite physical stock.
Inventory Adjustment: physical effect; accounting mapping is policy-driven.

## Integration contract
Business modules emit durable, idempotent domain/outbox events or invoke explicit accounting posting contracts after the business transaction reaches the appropriate state. Accounting must not infer critical postings by scraping mutable UI data.

## Money
Store exact decimal amounts with currency context. Tenant base currency is configuration, not a global assumption. Future foreign-currency documents require document currency, exchange-rate provenance/date and base-currency derived amounts.

## Tax
Tax codes/rates are effective-dated configuration. Do not hardcode a VAT percentage into business logic.

## Costing future
Prepare for weighted-average, FIFO and standard cost without embedding one method into the physical inventory ledger. Costing records must be reproducible/auditable and corrections must preserve history.

## Fiscal controls
Future accounting adds fiscal periods and posting locks. Module APIs should be able to reject postings into closed periods without redesigning document identity or audit history.
