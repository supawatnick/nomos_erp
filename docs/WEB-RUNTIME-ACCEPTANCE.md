# Web Runtime Acceptance — Clean-Room Correction

Status: **FAILED / REMEDIATION IN PROGRESS**

> 2026-10-02 correction: the previous PASS was invalid. HTTP 200 route checks, service liveness, and a successful Next.js build were incorrectly treated as browser/product acceptance.

## What went wrong
1. The Web package had **zero NOMOS-owned test files** outside dependencies.
2. `npm test` was `node --test`, which exits successfully when no project tests exist. A green command was incorrectly recorded as Web regression evidence.
3. Runtime acceptance checked route HTTP status but did not prove login/session persistence or operator workflows.
4. The deployed UI exposed only a thin subset of the 90-path API surface; several phase reviews therefore overstated browser completeness.
5. A temporary authentication edit introduced a Python syntax error and reached Host 73 before a compile/runtime gate caught it.
6. Warehouse/Product optional PostgreSQL filters could fail at runtime with `AmbiguousParameter`; route/build checks did not exercise the query.
7. Documentation continued to say PASS after these contradictions existed.

## Root cause
The acceptance model conflated four different signals: source exists, build succeeds, route responds, and workflow works. Only the last one demonstrates a usable ERP browser surface. Test commands were also accepted without proving that they discovered any NOMOS tests.

## Prevention gates
Web acceptance MUST fail unless all are true:
- NOMOS-owned browser/Web tests are discovered and count is non-zero.
- login creates a session and `/api/v1/auth/context` resolves it.
- critical module navigation and data reads execute through the deployed origin.
- critical create/transition/post/reverse workflows are browser-tested where applicable.
- error, 401/403, loading and empty states are exercised.
- lint, typecheck and production build pass.
- PostgreSQL-backed API acceptance passes with zero acceptance-test skips.
- deployed Host 73 smoke/E2E passes through port 80.
- review documents cite the actual evidence; HTTP 200 alone is never called browser acceptance.

## Current verified runtime baseline
- Caddy: port 80.
- Next.js: 127.0.0.1:3000.
- FastAPI canonical service: 127.0.0.1:8020.
- Same-origin `/api/*`, `/health`, `/ready` proxy to API.
- Host 73 PostgreSQL-backed API suite: **82 passed, 0 skipped** during clean-room remediation.
- Web lint/typecheck/production build: PASS after remediation.
- Web service: active; root returned HTTP 200 after restart.
- Product/Warehouse optional-filter PostgreSQL typing defect: fixed.

## Current URL
**http://10.10.110.73/**

## Open acceptance work
- Add a real Web/browser test harness.
- Prove non-zero NOMOS test discovery.
- Automate demo login + session context.
- Automate critical Inventory, Procurement, Sales, Finance, Approvals and Reports flows.
- Re-run against deployed Host 73 origin.
- Only then may this document return to PASS.
