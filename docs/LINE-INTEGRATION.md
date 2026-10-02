# LINE Integration

LINE is a first-class client of NOMOS ERP, not a separate ERP implementation.

## Flow
LINE -> signed webhook -> identity mapping -> intent/command -> permission check -> application service -> DB -> response

## Initial commands/use cases
- Search product
- Check SKU stock
- Check stock by warehouse
- Show low-stock products
- Request receive/issue/transfer
- Check pending approvals
- Approve/reject permitted requests
- Daily inventory summary

Thai natural-language input may map to these deterministic tools.

## Security
- Verify LINE webhook signature.
- Link LINE user identity to an authenticated ERP user/tenant.
- Never infer tenant only from free-form message text.
- Check ERP permission on every action.
- Read-only questions can execute immediately after authorization.
- Mutations require clear confirmation; sensitive/high-impact mutations may require approval.
- Protect against duplicate webhook delivery.
- Never expose secrets or unrestricted DB/query tools to an AI model.

## AI boundary
AI can translate “ย้าย A001 10 ชิ้นจากกรุงเทพไปภูเก็ต” into structured intent. The ERP service validates SKU, warehouses, quantity, authorization and approval before execution.
