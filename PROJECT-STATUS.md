# NOMOS ERP — Clean-Room Verification Status

> Effective 2026-10-02. This document supersedes prior PASS claims until each gate below is independently reverified against the current repository and the deployment environment runtime.

## Current stage
**CLEAN-ROOM AUDIT / REMEDIATION — ALL PHASES 0–15 UNVERIFIED**

Reason: browser/runtime inspection exposed a material gap between prior phase documentation and the deployed Web product. No prior phase PASS is inherited automatically.

## Verified baseline facts
- the deployment environment is the runtime/build/test/database target; Host 72 remains orchestration only.
- the deployment environment repository matches origin/main at the audit baseline.
- Caddy listens on :80, Next.js on :3000, FastAPI on 127.0.0.1:8020.
- Web and API services are running at the baseline.
- Repository contains API migrations 0001–0019 and 18 API test modules.
- Default API pytest result: 18 passed, 64 skipped. The skipped PostgreSQL acceptance tests MUST be rerun with the PostgreSQL runtime configuration before backend phases can be verified.
- NOMOS-owned Web test files found outside node_modules: **0**.
- apps/web package test script is `node --test`; therefore a green `npm test` does not currently prove Web behavior.
- Web app contains roughly 30 route/page files but the primary route/layout/CSS implementation is extremely thin (roughly 300 lines in the first inventory), inconsistent with prior claims of complete commercial-pilot browser acceptance.
- Temporary demo provisioning exists, but login/browser acceptance is not yet an accepted gate.

## Status by phase
| Phase | Clean-room status | Primary reason |
|---|---|---|
| 0 | UNVERIFIED | contracts must be reconciled against actual implementation |
| 1 | UNVERIFIED | deterministic boot/migrate/CI must be rerun |
| 2 | UNVERIFIED | PostgreSQL tenant/RBAC/session acceptance must run without skips |
| 3 | UNVERIFIED | API + usable Web master-data flow must be demonstrated |
| 4 | UNVERIFIED | PostgreSQL concurrency/ledger acceptance must run without skips |
| 5 | FAILED / REMEDIATION | deployed Web is not a complete operator-grade ERP surface |
| 6 | UNVERIFIED | operational Web + PostgreSQL flows not clean-room accepted |
| 7 | UNVERIFIED | CRM/partner Web + DB flows not clean-room accepted |
| 8 | UNVERIFIED | procurement E2E Web/API/DB acceptance required |
| 9 | UNVERIFIED | sales E2E Web/API/DB acceptance required |
| 10 | UNVERIFIED | approval E2E acceptance required |
| 11 | UNVERIFIED | reports/export E2E acceptance required |
| 12 | UNVERIFIED | finance E2E and reconciliation acceptance required |
| 13 | DEFERRED / NOT PASS | intentionally deferred |
| 14 | UNVERIFIED | onboarding/subscription/entitlement browser acceptance required |
| 15 | FAILED / REMEDIATION | prior commercial hardening closure did not prove usable browser E2E |

## New acceptance rule
A phase is PASS only when its required source implementation, migrations, authorization/tenant isolation, automated tests, and relevant deployed the deployment environment runtime/browser workflows are all demonstrated. Route HTTP 200, build success, or documentation alone is not acceptance.

For Web-dependent phases, acceptance additionally requires:
1. real NOMOS-owned automated Web tests;
2. browser-operable navigation/forms/tables/states;
3. authentication/session persistence;
4. API errors surfaced usefully;
5. design-contract compliance;
6. deployed the deployment environment smoke/E2E evidence.

## Immediate remediation plan
1. Restore trustworthy authentication/login and remove temporary unsafe demo bypass after a proper demo credential path is available.
2. Build a real shared ERP Web shell/component system matching WEB-DESIGN-CONTRACT.
3. Add a Web test harness and tests for login, navigation, protected requests, error states and critical workflows.
4. Rebuild Phase 3–12/14 Web surfaces module by module against existing API contracts rather than placeholder/thin pages.
5. Run PostgreSQL-backed API acceptance with zero acceptance-test skips.
6. Execute deployed E2E smoke flows on the deployment environment across the four ERP cores.
7. Reconcile phase review documents only after evidence exists.

## Clean-room remediation evidence — 2026-10-02
- the deployment environment PostgreSQL-backed API acceptance: **82 passed, 0 skipped** after loading the runtime environment.
- Fixed PostgreSQL optional-filter typing in product/warehouse listing that produced runtime 500 errors.
- FastAPI readiness returned `{"status":"ready"}` after remediation restart.
- Reworked Demo login UX to prefill tenant/email, store session/tenant/permissions and redirect to workspace.
- Reworked home workspace to verify `/api/v1/auth/context` before presenting operational modules.
- Expanded Procurement Web visibility from PO-only to PR + RFQ + PO pipeline while preserving receipt/return workflow.
- Expanded Finance Web from COA-only to accounts, periods, journals, invoices and payments workspaces.
- Strengthened Sales workspace hierarchy and operational counts.
- Web lint/typecheck/build: PASS after remediation; production Web service restarted.
- NOMOS-owned deployed-origin runtime tests now exist and cannot silently pass with zero discovered tests. the deployment environment port-80 runtime gate: **3 passed, 0 failed, 0 skipped** covering critical routes, health/readiness, demo login/session context, and authenticated reads across master data + four cores + approvals/reports.\n- The new suite caught and forced fixes for Finance 405 method mismatch and 500 schema mismatch before acceptance.\n- Chromium DOM-driving E2E is now active on the deployment environment: **3 passed** covering login, session persistence/refresh, critical module navigation, Finance tab interaction and Inventory navigation/client errors. The suite exposed and forced a fix for a real session-loss-on-aborted-context-fetch defect.\n- **Remaining clean-room blocker:** browser E2E for business-state mutations (create/submit/approve/post/reverse/return as applicable) is still required before affected Web phases can return to PASS.


## Clean-room continuation — 2026-10-02 17:02 UTC
- Control-plane identity reconfirmed: Host 72 is orchestration; the deployment environment is the NOMOS runtime target.
- the deployment environment deployed Web through Caddy returns HTTP 200 on port 80.
- Temporary demo passwordless login returns HTTP 200 and authenticated session context resolves HTTP 200.
- Authenticated runtime reads return HTTP 200 for master-data summary, inventory balances, Procurement PR/RFQ/PO, Sales quotations/orders, Finance accounts/periods/journals/invoices/payments, approvals and reports.
- A prior ad-hoc probe used guessed endpoint names and produced 404/422; those results are not regressions. The canonical runtime-test endpoint list was then used and passed.
- Latest browser-mutation test work is at commit 631e83a9ad0d6923fa6cca967f99a45a03828649 (Inventory receive + explicit reversal flow).
- CI run 37036036854 exposed Ruff-only bootstrap/demo import defects; commits 3776e261b80bd112a1ca6da4646deb8ec8bdaa67 and 135855129a517ac74b03a4aef7dc0a1a1b0c6a4b corrected those import findings.
- CI run 37037624283 then passed Ruff and exposed two remaining mypy defects: bootstrap_admin return annotation mismatch and provision_demo permission-count annotation. Later gates did not run because mypy stopped the job.
- Direct SSH from the current Host 72 session to the deployment environment reaches sshd but is rejected by public-key authentication for both root and ntap. Runtime HTTP remains healthy; SSH authorization must be restored before the deployment environment service restart/deploy and on-host browser mutation E2E can be resumed safely.


## Clean-room continuation — 2026-10-02 18:50 UTC
- Host 72 SSH access to the deployment environment is confirmed using the dedicated demo operations identity; the deployment environment reports hostname nomos-erp.
- the deployment environment runtime layout: PostgreSQL and Redis run in Docker Compose; nomos-api.service and nomos-web.service run under systemd.
- Deployed runtime suite passed 3/3: critical ERP routes, health/readiness, and demo login + authenticated module reads.
- Browser acceptance originally passed 3/4 and failed only on Inventory RECEIVE because no POST was emitted after clicking the enabled button.
- Root cause: inventory idempotency generation called crypto.randomUUID() directly. The private HTTP origin is not a secure context, so the browser threw before fetch. Commit e6a0e8ce7b5c5190b8a794394c1f16519d226458 adds a getRandomValues fallback.
- Production Web rebuilt successfully and nomos-web.service restarted. API log then confirmed POST /api/v1/inventory/transactions returned 201 Created.
- Focused browser mutation acceptance now passes 1/1 end-to-end: RECEIVE is posted, movement is visible, explicit reversal is posted, and reversal is visible.
- CI is green for the production fix commit e6a0e8ce7b5c5190b8a794394c1f16519d226458 and preceding mypy fixes. The latest test-only synchronization commit is still running CI at the time of this note.


## Verification continuation — 2026-10-02 23:45 UTC
- GitHub Actions is green through commit 305da778eb852c16c523d957a7fd203b0bfab1c8, including the production private-HTTP idempotency fix and browser test synchronization.
- the deployment environment was fast-forwarded to 305da77; nomos-api.service and nomos-web.service both report active.
- Important runtime topology correction: nomos-api.service listens on 127.0.0.1:8020, not 127.0.0.1:8000. Probing :8000 produced an unrelated 500 and must not be used as NOMOS API health evidence.
- API health and reverse-proxy health checks returned healthy responses during verification.
- Runtime acceptance against the public origin passed 3/3 again: critical ERP routes, health/readiness, and demo login + authenticated reads.
- Inventory browser mutation acceptance remains verified end-to-end from the prior run: RECEIVE 201, movement visible, reversal 201, reversal visible.

## NEXT ACTIONS
- **NEXT 1:** repair and acceptance-test authentication/login end-to-end.
- **NEXT 2:** establish shared Web design system + shell and automated Web test harness.
- **NEXT 3:** reverify Phase 0–4 backend foundations using PostgreSQL acceptance.
- **NEXT 4:** rebuild/verify Web-dependent phases sequentially.
- **NEXT 5:** rerun commercial hardening only after four-core E2E is green.

## Handoff
Do not use historical PASS language as authorization to advance. The clean-room table above is the operational source of truth until superseded by new evidence.


## Login/API regression incident — 2026-10-03
- Production symptom: `/login` rendered HTTP 200 but authentication failed because public `/health` returned 502.
- Root cause: `apps/api/app/api_master.py` contained literal escaped `\\n` sequences introduced by the organization lookup patch. Python raised `SyntaxError` while importing `app.main`, causing `nomos-api.service` to restart-loop.
- Fix: commit `db78acea36e1ed91b3eb2cbb2dfbe782f20e3e51` removed the escaped newline corruption. On the deployment environment, `python -m py_compile apps/api/app/api_master.py` passes and the API was restarted.
- Production verification: public `/health` returns HTTP 200 with `{"status":"ok"}`; `/login` returns HTTP 200; deployed runtime acceptance passes 3/3 including demo login, tenant session creation, and authenticated context resolution.
- Prevention: commit `c47edeaa4f3e28f4089af57c59d785bdf4a2d17b` adds an explicit CI import/startup gate (`from app.main import app`) before migration/tests so import-time syntax failures are caught before deployment.
- CI note: the regression fix itself proceeds past Python checks; current CI is independently blocked by `npm audit --audit-level=high` on upstream `braces 3.0.3` (GHSA-vfj7-8cjw-p6xm). The registry currently reports 3.0.3 as latest and `npm audit fix --force` proposes a breaking eslint-config-next downgrade, so the security gate is not being bypassed or force-downgraded.


## CRUD lifecycle completion — 2026-10-03
- Master-data lifecycle policy is now explicit: mutable master records use Create + Edit + Archive rather than destructive hard-delete, preserving foreign keys and audit history. Posted transactional documents continue to use Cancel/Void/Reverse according to their domain lifecycle.
- Backend update/archive coverage added for Category, Unit, Warehouse, Location, Product, and Business Partner. Update operations remain tenant-scoped, permission-gated, and audit-recorded.
- Web actions now expose Edit/Cancel/Archive for Category, Unit, Warehouse, Location, Product, and Business Partner; CRM also exposes lead creation/transitions, opportunity creation, and targeted activity creation.
- A Unit archive patch initially inserted an archive SQL entry into the read-query map; Ruff caught the duplicate-key defect before deployment. Commit 2baa870e7afb5b2baaa8f5eb5db26223de07bbd3 corrected query placement. This is recorded as another reason to require lint/import gates before deployment.
- the deployment environment verification after the CRUD changes: Python compilation passed, API pytest passed 18/18 (64 environment-dependent tests skipped), Web typecheck passed, Web contract tests passed 3/3, Next production build generated 31/31 pages, and deployed runtime acceptance passed 3/3 after API/Web restart with a readiness delay.
- CI still has the independent npm audit advisory blocker documented above; Ruff import-order findings introduced by the CRUD endpoints were corrected in follow-up style commits.


## Web operational completion pass — 2026-10-03
- Web audit expanded beyond route rendering: core pages were compared against existing backend commands and read-only gaps were converted into operational actions where the domain permits mutation.
- Finance Web now creates chart-of-account records and fiscal periods and can open/close periods. Immutable posted accounting records remain non-editable by design; journal reversal/payment/invoice APIs remain the accounting lifecycle rather than destructive edit/delete.
- Procurement Web now creates Purchase Requests and exposes PR submit/approve/reject/cancel actions. Product, unit, and warehouse-location inputs use master-data selectors rather than requiring copied UUIDs.
- Sales Web now creates quotations, sends and accepts quotations into Sales Orders, confirms/cancels orders, and retains reservation/delivery/return fulfillment. Legal entity, customer, product, unit, and location use business selectors.
- Existing operational areas remain active: Inventory posting/reversal workflows, Approval decisions/cancellation, controlled Imports validation/commit, Reports/export, CRM lead/opportunity/activity workflows, and Master Data Create/Edit/Archive.
- Admin Audit and Subscription are intentionally read-only evidence/entitlement views; immutable audit evidence must not expose edit/delete, and subscription mutation is not fabricated without a commercial provisioning command.
- Verification on the deployment environment after this pass: Web typecheck passed, Next production build generated 31/31 pages, Web service restarted, and deployed runtime acceptance passed 3/3 (critical routes, health/readiness, demo login/session/context/authenticated reads).
