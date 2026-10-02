# Product Requirements

## Vision

NOMOS ERP helps small and growing businesses control stock accurately from Web or LINE without creating separate business logic for each channel.

## Primary personas

- Owner/Admin: configures company, users, roles, warehouses and policies.
- Inventory Manager: receives, issues, transfers, adjusts and reviews stock.
- Operator: performs permitted warehouse tasks.
- Approver/Manager: approves sensitive or high-value operations.
- Viewer: read-only access to permitted reports and inventory.
- LINE User: one of the above ERP identities linked to a LINE account.

## MVP user outcomes

A company can:
- create a tenant and invite/manage users
- define products, units, warehouses and locations
- receive goods and see stock increase
- issue goods and prevent unauthorized/insufficient stock
- transfer stock between locations without duplication
- adjust stock with reason and audit evidence
- search balances/history
- configure low-stock thresholds
- use LINE to query stock and submit safe operational requests
- approve/reject permitted requests
- trace who did what, when, from which channel

## MVP exclusions

Not required for first production MVP:
- general ledger/full accounting
- payroll/HR
- manufacturing/MRP
- advanced WMS wave/route optimization
- advanced tax engine
- offline-first mobile application
- autonomous AI execution without deterministic policy checks

## Product principles

- Accuracy before convenience
- Explicit state transitions
- Human-readable audit history
- Mobile-friendly operational flows
- Safe defaults: no negative stock by default, deny authorization by default
- Thai and English presentation
- Configuration over customer-specific forks

## Core acceptance criteria

### Receive
Given a permitted user and valid destination location, posting a receive creates an immutable ledger transaction and increases derived stock exactly once.

### Issue
Given insufficient available stock and the default policy, posting an issue is rejected without partial ledger writes.

### Transfer
A transfer decreases the source and increases the destination atomically under one business transaction.

### Retry
Retrying a mutation with the same idempotency key returns the prior result and does not duplicate stock movement.

### Tenant isolation
A user in tenant A cannot read, reference or mutate tenant B data even if tenant B identifiers are guessed.

### LINE
A LINE mutation requires a linked ERP identity, valid permission, explicit confirmation and approval when policy requires it.

### Audit
Every critical mutation records actor, tenant, action, target, channel, request ID, result and relevant structured changes.

## Success metrics for pilot

- No unexplained stock balance changes
- No cross-tenant data access in automated security tests
- Duplicate LINE/API delivery does not duplicate mutations
- Common stock lookup can be completed quickly on Web and LINE
- Restore procedure is tested before production pilot