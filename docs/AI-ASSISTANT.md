# AI Assistant Boundary

AI is a future interface to NOMOS, not an authority.

## Allowed responsibilities

AI may:
- interpret Thai/English natural language
- map text into a limited structured intent/tool call
- ask for missing/ambiguous information
- summarize inventory/audit/report data the user is authorized to read
- draft an operational request for confirmation

## Prohibited shortcuts

AI must not:
- run arbitrary SQL
- receive database credentials
- choose tenant from free-form text without trusted identity context
- bypass RBAC, confirmation or approval
- silently execute ambiguous/high-impact mutations
- expose another tenant's data
- invent identifiers/stock values and execute them
- treat model output as validated business data

## Tool design

Expose narrow tools such as:
- search_product
- get_inventory_balance
- create_receive_request
- create_issue_request
- create_transfer_request
- get_pending_approvals
- decide_approval

Each tool accepts a trusted actor/tenant context outside model-controlled arguments where possible. Deterministic application services validate all arguments.

## Mutation flow

natural language -> structured draft -> deterministic validation -> normalized summary -> explicit user confirmation -> approval if required -> deterministic execution -> auditable result

## Prompt injection posture

External/user text is untrusted. The model cannot grant itself new tools, permissions or data scope. Tool authorization is enforced outside the model.