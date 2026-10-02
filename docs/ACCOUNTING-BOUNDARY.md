# Finance & Accounting Core

Finance & Accounting is one of NOMOS ERP's four first-class core modules. It is not an optional future add-on. Delivery is sequenced after operational modules so their source facts are stable, but architecture and schemas must preserve accounting integration from the start.

## Ownership
Finance owns:
- chart of accounts and account configuration
- journal entries/lines and General Ledger
- Accounts Receivable and Accounts Payable
- customer/supplier invoices and credit/debit notes
- receipts, payments and allocations
- fiscal periods and posting locks
- tax/VAT posting configuration
- accounting posting rules
- financial dimensions required by policy
- trial balance and financial statement foundations
- reconciliation controls

Inventory owns physical quantity/movement. Procurement owns supplier purchase intent. Sales owns customer commercial intent. Finance never rewrites physical stock or source commercial documents.

## Core invariants
- Posted journal entries are immutable.
- Every posted journal balances debit == credit in document/base currency rules.
- Financial amounts use exact decimals with explicit currency.
- Posting into closed/locked periods is rejected.
- Posting is tenant/legal-entity scoped.
- Cross-tenant/legal-entity account/document references are rejected.
- Source posting is idempotent: one eligible source effect cannot create duplicate journals.
- Corrections use reversal, credit/debit note or explicit adjustment; no destructive history rewrite.
- Journal entries retain source module/type/id/number, request correlation and actor/system provenance.
- AR/AP subledgers reconcile to GL control accounts.

## Operational integration
Purchase Order: no financial posting by itself.
Goods Receipt: physical increase; may create inventory/accrual valuation facts according to configured policy.
Supplier Invoice: AP/tax/expense/inventory-clearing financial document.
Payment: settles AP without changing physical stock.

Quotation/Sales Order: no GL posting by themselves.
Delivery: physical decrease; may create inventory/COGS valuation facts.
Customer Invoice: AR/revenue/tax financial document.
Receipt: settles AR without changing physical stock.

Inventory Adjustment: physical effect; Finance maps valuation impact through configured posting rules.

## Posting contract
Source modules emit durable, idempotent posting facts or invoke explicit Finance posting contracts only after the source reaches an eligible state. Contract includes tenant, legal entity, source type/id/number, effective/posting date, currency, exact amounts, tax context, business dimensions and idempotency identity. Finance validates period/account/policy and owns resulting journal IDs.

## Money & currency
Tenant base currency is configuration, not a global assumption. Foreign-currency documents preserve document currency, transaction amount, exchange-rate value/source/date and calculated base-currency amount. Rounding policy is explicit and tested.

## Tax/VAT
Tax codes/rates are effective-dated configuration. Do not hardcode VAT percentages. Tax calculation and tax posting are separate concerns with auditable bases/amounts.

## Costing & valuation
Physical inventory ledger remains quantity-authoritative. Costing/valuation may use weighted average, FIFO or standard cost according to configured policy without changing physical movement history. Valuation must be reproducible and corrections preserve history.

## Reconciliation gates
- journal debit == credit
- AR customer balance == AR control reconciliation
- AP supplier balance == AP control reconciliation
- inventory valuation/subledger == configured GL inventory control reconciliation
- source posting facts == Finance posting registry without duplicates/missing eligible items

## Acceptance
Finance phase is not PASS until balanced journal, closed-period, idempotency, reversal, tax/currency precision, AR/AP allocation and subledger-to-GL reconciliation tests pass.
