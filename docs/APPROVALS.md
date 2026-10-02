# Confirmation and Approval

Confirmation and approval solve different problems.

- Confirmation: the requester verifies the normalized action before execution.
- Approval: another eligible authority authorizes execution according to policy.

## Policy examples

Approval may be required for:
- inventory adjustment above a quantity/value threshold
- issue/transfer above threshold
- negative-stock override if ever enabled
- backdated transaction beyond a configured window
- high-value purchasing
- role/security changes in future

## Approval request

Store:
- tenant
- request type
- requester
- structured immutable request snapshot or versioned reference
- policy/rule that triggered approval
- status
- created/expires timestamps
- decisions
- execution result/reference

Statuses:
- PENDING
- APPROVED
- REJECTED
- CANCELLED
- EXPIRED
- EXECUTED

## Rules

- Approval decisions are permission-checked.
- Eligibility is evaluated at decision time.
- Self-approval can be prohibited by policy and should be prohibited for sensitive defaults.
- A decision is idempotent.
- Changing a material request after approval invalidates approval and requires a new approval.
- Execution after approval revalidates relevant stock/domain state because conditions may have changed.
- Approved does not mean successfully executed; execution can still fail safely.
- Every decision and execution attempt is audited.

## LINE/Web consistency

Web and LINE expose the same approval objects and invoke the same application use cases. Channel-specific buttons must not bypass policy.