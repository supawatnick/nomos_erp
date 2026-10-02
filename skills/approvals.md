# Approval Skill

- Confirmation is not approval; keep them separate.
- Approval policy evaluation is deterministic.
- Store a stable request snapshot/version with the approval.
- Permission plus policy eligibility is required to decide.
- Enforce self-approval/separation-of-duties rules.
- Decisions are idempotent and audited.
- Material request changes invalidate prior approval.
- Before execution, revalidate stock/domain conditions.
- APPROVED and EXECUTED are different states.
- Web and LINE call the same approval use cases.
- Expiry/cancellation must be explicit and tested.