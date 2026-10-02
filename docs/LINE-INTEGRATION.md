# LINE Integration

LINE is a client/adapter of NOMOS ERP, not a separate business system.

## High-level flow

LINE -> signed webhook -> deduplication -> identity mapping -> command/intent -> permission/policy -> application use case -> database -> response/outbox

## Initial user actions

Read-only:
- search product
- check SKU stock
- check stock by warehouse/location
- show low-stock products
- show recent movements
- show pending approvals

Mutating:
- request receive
- request issue
- request transfer
- request adjustment when permitted
- approve/reject eligible requests

## Identity linking

A LINE user must be explicitly linked to an authenticated ERP user and tenant.

Recommended flow:
1. User initiates link from ERP Web.
2. Server creates a short-lived, single-use link token/code.
3. User completes link through LINE.
4. Server verifies token, membership and tenant.
5. Store LINE user identifier -> ERP user/tenant link.
6. Audit link/unlink.

Never infer tenant from free-form message content.

## Webhook security

- Verify LINE webhook signature before parsing business content.
- Enforce body size limits.
- Store/deduplicate delivery event identifiers.
- Return promptly; queue work if processing could exceed webhook response expectations.
- Webhook retry must not duplicate business mutation.

## Natural language

Thai/English natural language may map messages into a small deterministic command schema, for example:

~~~
{
  "intent": "inventory.transfer",
  "sku": "A001",
  "quantity": "10",
  "from_warehouse": "Bangkok",
  "to_warehouse": "Phuket"
}
~~~

The parser/AI is not trusted to authorize or execute. The ERP validates entity matches, tenant, quantity, permission, approval and concurrency.

## Ambiguity handling

If product, warehouse, unit, quantity or other required data is ambiguous:
- ask a concise follow-up
- present safe choices when possible
- do not guess operational data

## Mutation safety

LINE mutation lifecycle:
1. Interpret structured request.
2. Validate and authorize.
3. Show normalized confirmation summary.
4. User confirms.
5. If policy requires approval, create approval request.
6. Otherwise post through the same application service used by Web.
7. Reply with transaction number/result.

Confirmation tokens are short-lived, bound to actor/tenant/request and single-use.

## Approvals

Approvers can receive a concise summary with approve/reject actions. Decision postbacks are verified, permission-checked, duplicate-safe and tied to a specific approval version/state.

## Output rules

Replies should be compact and mobile-friendly. Never expose:
- credentials/secrets
- raw stack traces
- internal SQL
- unrestricted internal IDs when unnecessary
- data from another tenant