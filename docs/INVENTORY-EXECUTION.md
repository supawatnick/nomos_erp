# Inventory Execution and Concurrency Contract

Status: PASS — Phase 0 execution contract.

This document is normative for Phase 4 inventory implementation and refines INVENTORY.md and ERD-PHASE-1-6.md.

## States and transitions
DRAFT may transition to PENDING_CONFIRMATION, PENDING_APPROVAL, POSTED or CANCELLED according to channel/policy. PENDING_CONFIRMATION -> PENDING_APPROVAL|POSTED|CANCELLED. PENDING_APPROVAL -> POSTED|REJECTED|CANCELLED. POSTED is immutable and may only be economically/physically corrected by a separate REVERSAL transaction. REJECTED/CANCELLED are terminal and never affect stock.

Posting is a command, not a mutable status patch.

## Preconditions for every posting
Within the same database transaction:
1. authenticate trusted actor/context and active tenant membership;
2. authorize the transaction-specific permission;
3. acquire/validate idempotency record;
4. load transaction/command and verify allowed state;
5. validate same-tenant product/unit/location/organization ownership;
6. validate product is inventory-capable and active for the operation;
7. validate positive quantity, unit conversion and precision;
8. resolve every line to base_quantity;
9. derive balance effects;
10. acquire balance locks deterministically;
11. validate stock/policy against locked balances;
12. write immutable ledger header/lines as POSTED or transition prepared header to POSTED;
13. apply balance projection effects;
14. write audit and outbox records;
15. finalize idempotency result;
16. commit once.

Any failure rolls back ledger, balance, audit/outbox business records and idempotency completion together.

## Balance effect rules
RECEIVE: destination +base_quantity.
ISSUE: source -base_quantity.
TRANSFER: source -base_quantity AND destination +base_quantity in one transaction.
ADJUST_IN: destination +base_quantity.
ADJUST_OUT: source -base_quantity.
OPENING: destination +base_quantity; permitted only through controlled opening/import workflow.
REVERSAL: exact opposite location/product/base-quantity effects of the referenced original transaction. A reversal never invents new line quantities.

Command quantities remain positive. Direction comes from transaction semantics.

## Deterministic locking
Balance lock key is (tenant_id, product_id, location_id), extended later by documented stock dimensions.
1. Aggregate duplicate effects for the same balance key before locking.
2. Ensure missing balance rows exist using conflict-safe INSERT ... ON CONFLICT DO NOTHING under the same transaction.
3. Sort all affected keys lexicographically by stable UUID byte/text representation in the same implementation everywhere.
4. SELECT affected balance rows FOR UPDATE in that order.
5. Re-read/use locked on_hand values only; never validate from an earlier unlocked read.
6. Apply aggregated deltas and increment balance version.

Transfers lock both source and destination keys together. Multi-line commands lock the complete sorted set, not line-by-line.

## Negative stock
Default policy: resulting on_hand for every affected key MUST be >= 0.
If any result is negative, fail with INSUFFICIENT_STOCK and write no stock effect.
Future negative-stock support requires an explicit tenant policy and schema migration compatible with the balance CHECK; it must never be enabled by bypassing the constraint.

## Idempotency
Required for receive/issue/transfer/adjust/opening/reversal API commands.
Scope is the stable use-case name plus tenant.
- First key use stores request fingerprint and IN_PROGRESS ownership.
- Same key + same canonical fingerprint after success returns the original business result without reposting.
- Same key + different fingerprint -> IDEMPOTENCY_CONFLICT.
- Concurrent same-key execution must have one owner; contenders wait/read completed result or receive a retriable in-progress conflict according to implementation timeout.
- Failed transaction must not leave a false SUCCESS record.
Canonical fingerprint excludes transport noise/request_id but includes every field that changes business meaning.

## Reversal
Eligibility:
- original exists in same tenant and is POSTED;
- original is not itself cancelled/deleted;
- no canonical reversal already exists;
- actor has permission for reversal policy (Phase 0 maps this to inventory.adjust);
- any future closed-period/accounting restrictions pass.

Reversal stores reversal_of_id and copies the original physical effect with opposite direction. Reference/reason is mandatory. Original remains POSTED; UI may derive/display REVERSED when a linked posted reversal exists. The unique reversal link prevents double reversal.

A reversal can fail with INSUFFICIENT_STOCK if reversing an inbound movement would make current stock negative. No historical rewrite is allowed to force it through; authorized compensating adjustment is a separate decision.

## Posting algorithms
Receive/Adjust In/Opening: validate destination stock location -> lock destination keys -> add -> post.
Issue/Adjust Out: validate source -> lock -> ensure sufficient locked on_hand -> subtract -> post.
Transfer: validate distinct source/destination and valid stock locations -> lock all source+destination keys -> validate all sources -> apply all deltas atomically -> post.
Reversal: load immutable original lines -> derive opposite effects -> lock all affected keys -> validate resulting balances -> create linked reversal -> apply -> post.

## Reconciliation
A reconciliation job/query derives signed SUM(base_quantity) per current stock key from POSTED ledger effects and compares with inventory_balances.on_hand using exact NUMERIC arithmetic.
Results: MATCH or MISMATCH with tenant/product/location, ledger_qty, balance_qty, delta.
Reconciliation is read-only by default. It never silently repairs balances. Repair requires an explicit controlled rebuild/repair operation, audit evidence and operational approval.
A full rebuild creates projection values from ledger in a controlled maintenance process; ledger is never rebuilt from balances.

## Required tests
- receive increments exactly once;
- issue rejects insufficient stock with no partial writes;
- two concurrent issues against 10 where each requests 8: at most one succeeds;
- multi-line issue failure rolls back every line;
- transfer commits both sides or neither;
- opposing concurrent transfers do not deadlock under deterministic ordering (or retry safely on DB deadlock);
- missing balance-row creation is race safe;
- duplicate idempotency request returns same transaction;
- conflicting payload under same key rejects;
- concurrent same-key requests create one stock movement;
- adjustment permission/reason enforced;
- opening stock only through authorized workflow;
- reversal produces exact opposite effects;
- second reversal rejects;
- reversal that would create negative stock rejects;
- cross-tenant product/location/reversal IDs do not disclose/mutate;
- ledger reconciliation matches after every successful scenario;
- audit and outbox exist only for committed effects.

## Implementation note
Serializable isolation is not required globally. Correctness comes from explicit DB transaction boundaries, deterministic row locking, uniqueness/constraints and retry handling for transient database conflicts.
