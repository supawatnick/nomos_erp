# Testing Skill

Testing pyramid:
1. Domain unit tests
2. Application/service tests
3. DB/repository integration tests
4. API tests
5. LINE webhook/adapter tests
6. Selected end-to-end Web flows

Critical scenarios:
- tenant isolation
- RBAC
- duplicate requests/webhooks
- concurrent stock issue
- insufficient stock
- transfers
- reversals/adjustments
- approval authorization
- webhook signature failure
- audit creation

Business-critical inventory code is not complete without tests.
