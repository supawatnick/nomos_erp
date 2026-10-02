# Contributing to NOMOS ERP

## Workflow

1. Create a focused branch from main.
2. Keep changes small enough to review.
3. Add or update tests with business behavior.
4. Run lint, type checks, tests and migration checks locally.
5. Update documentation when contracts, architecture or rules change.
6. Open a pull request describing behavior, risks and migration impact.

## Commit style

Prefer concise conventional-style subjects:
- feat: add inventory transfer use case
- fix: prevent duplicate LINE webhook processing
- docs: define approval policy
- test: add cross-tenant access coverage
- chore: update CI tooling

## Pull request checklist

- [ ] Tenant scope reviewed
- [ ] Authorization reviewed
- [ ] Validation and error behavior reviewed
- [ ] Idempotency/concurrency reviewed for mutations
- [ ] Audit/logging reviewed
- [ ] Migrations are safe and documented
- [ ] Tests cover success and failure paths
- [ ] Documentation/OpenAPI updated
- [ ] No secrets or credentials committed

## Database migrations

Use additive/backward-compatible migrations when possible. For destructive or large migrations, use an expand -> backfill -> switch -> contract sequence and document rollback/recovery.

## Review rule

Business-critical inventory, authorization, tenant isolation and approval changes require another reviewer before production deployment.