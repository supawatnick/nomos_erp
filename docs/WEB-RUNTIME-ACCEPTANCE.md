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


## Remediation evidence — 2026-10-02
A mandatory NOMOS-owned runtime suite now exists at `apps/web/tests/runtime.test.mjs`; `npm test` explicitly targets `tests/*.test.mjs`, so absence of project tests can no longer silently pass.

The new gate immediately found defects that prior acceptance missed:
- Finance workspace called `GET /api/v1/finance/periods` although only POST existed: **405**.
- After adding finance read APIs, the journal query referenced non-existent `finance_journals` instead of schema table `journal_entries`: **500**.
- Invoice/payment UI read models assumed stored `open_amount`/`unallocated_amount`; the schema stores settled/allocated amounts, so read endpoints now derive the open values.
These were corrected before accepting the gate.

Deployed-origin run against **http://10.10.110.73**:
- critical ERP route rendering: PASS;
- `/health` + `/ready`: PASS;
- demo login + session context: PASS;
- authenticated reads for master data, Inventory, Procurement PR/RFQ/PO, Sales quotation/order, Finance accounts/periods/journals/invoices/payments, Approvals and Reports: PASS;
- runtime suite: **3 passed, 0 failed, 0 skipped**;
- Web lint: PASS;
- Web typecheck: PASS;
- production build command completed successfully in the same gate (build output intentionally redirected on Host 73).

### Remaining limitation
This runtime suite is an automated deployed-origin integration/smoke suite, not yet a full DOM-driving browser suite. It proves routing, login/session and critical authenticated API reads through the deployed origin. Destructive/financial posting browser workflows still require dedicated E2E coverage before Phase 15 can return to PASS.


## DOM-driving browser gate — 2026-10-02
Playwright Chromium acceptance is now installed and executed on Host 73 against the deployed private-network origin.

Initial execution correctly FAILED because Host 73 lacked Chromium runtime libraries (`libatk-1.0.so.0`). Playwright system dependencies were installed; this infrastructure failure was not waived.

The first real browser run then exposed a client lifecycle defect that HTTP/API smoke could not detect: navigating or refreshing while the home page `/api/v1/auth/context` request was in flight aborted `fetch`; the generic catch handler interpreted the abort as authentication failure and deleted `nomos_session` / `nomos_tenant`. This manifested as successful login followed by apparently random logout / Inventory auth errors. The workspace now uses `AbortController`, ignores navigation AbortError, and clears credentials only on explicit 401/403.

A test-authoring defect was also corrected: Next.js route announcer uses an empty `role=alert`; browser assertions now target NOMOS error surfaces rather than treating framework accessibility infrastructure as an ERP error.

Final Host 73 gate:
- deterministic Web contract tests: **3 passed**;
- deployed-origin runtime integration tests: **3 passed**;
- Chromium DOM E2E: **3 passed**;
- browser flows cover demo sign-in, critical module navigation, session persistence across refresh, interactive Finance tabs, and Inventory operational navigation/client-error detection;
- Web lint: PASS;
- Web typecheck: PASS.

This closes the previous “no DOM-driving browser test” gap for navigation/session/read surfaces. Phase 15 remains in remediation until mutation workflows that change business state (create/submit/approve/post/reverse/return where applicable) receive browser E2E coverage.
