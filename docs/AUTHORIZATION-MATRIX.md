# Authorization Matrix

Status: APPROVED — Phase 1–6 implemented baseline plus reserved four-core permission contract.

Roles are templates only. Server code authorizes permissions, never role names. Permissions listed for later phases are namespace contracts and are seeded/activated with their implementing migration, not evidence that those modules already exist.

## Risk
LOW: read.
MEDIUM: normal business mutation.
HIGH: correction, approval override, security/configuration, financial posting/period control, sensitive export.

## Platform / Inventory implemented baseline
| Operation | Permission | Risk |
|---|---|---:|
| View tenant/org | tenant.read / organization.read | LOW |
| Edit tenant/org | tenant.manage / organization.manage | HIGH |
| View/manage users | user.read / user.manage | LOW/HIGH |
| View/manage roles | role.read / role.manage | LOW/HIGH |
| View/manage catalog | product.read / product.manage | LOW/MEDIUM |
| View/manage warehouse | warehouse.read / warehouse.manage | LOW/HIGH |
| View stock | inventory.read | LOW |
| Receive/issue/transfer | inventory.receive / inventory.issue / inventory.transfer | MEDIUM |
| Adjust/reverse/opening | inventory.adjust | HIGH |
| Stock count | inventory.count (+ inventory.adjust to post variance) | MEDIUM/HIGH |
| View audit | audit.read | HIGH |
| Export reports | report.read + report.export | LOW/MEDIUM |

## Reserved Partners & CRM
| Operation | Permission | Risk |
|---|---|---:|
| View partners/customers/suppliers | partner.read | LOW |
| Manage partner/contact/address | partner.manage | MEDIUM |
| View CRM leads/opportunities/activities | crm.read | LOW |
| Manage CRM pipeline/activity | crm.manage | MEDIUM |

## Reserved Sales & CRM
| Operation | Permission | Risk |
|---|---|---:|
| View QT/SO/order tracking | sales.read | LOW |
| Create/edit/send QT | quotation.manage | MEDIUM |
| Accept/reject/expire/cancel QT | quotation.transition | MEDIUM |
| Create/edit/confirm SO | sales_order.manage | MEDIUM |
| Hold/cancel high-impact SO | sales_order.override | HIGH |
| Reserve/release stock for SO | sales.reserve | MEDIUM |
| Post delivery/return | sales.fulfill | MEDIUM |
| Override price/discount/credit exception | sales.override | HIGH |

## Reserved Procurement & Purchasing
| Operation | Permission | Risk |
|---|---|---:|
| View procurement/PO tracking | procurement.read | LOW |
| Manage PR | purchase_request.manage | MEDIUM |
| Manage RFQ/supplier responses/award | rfq.manage | MEDIUM |
| Create/edit/submit PO | purchase_order.manage | MEDIUM |
| Approve/hold/cancel exceptional PO | purchase_order.approve / purchase_order.override | HIGH |
| Post Goods Receipt/Return orchestration | procurement.receive | MEDIUM |

## Reserved Finance & Accounting
| Operation | Permission | Risk |
|---|---|---:|
| View accounting/GL | accounting.read | LOW |
| Manage Chart of Accounts/posting config | accounting.configure | HIGH |
| Create/post manual journal | journal.manage / journal.post | MEDIUM/HIGH |
| Reverse journal | journal.reverse | HIGH |
| View/manage AR invoices/open items | ar.read / ar.manage | LOW/MEDIUM |
| Post customer invoice/credit note | ar.post | HIGH |
| View/manage AP invoices/open items | ap.read / ap.manage | LOW/MEDIUM |
| Post supplier invoice/debit-credit note | ap.post | HIGH |
| Create/post receipts/payments | payment.manage / payment.post | MEDIUM/HIGH |
| Manage tax configuration | tax.manage | HIGH |
| Manage exchange rates | fx.manage | HIGH |
| Close/reopen fiscal period | fiscal_period.close / fiscal_period.reopen | HIGH |
| View/export financial statements | financial_report.read / financial_report.export | LOW/HIGH |

## Scope contract
Phase 1–6 grants are tenant-wide, but RequestContext/application authorization must be extendable to legal_entity_ids, branch_ids and warehouse_ids. Finance posting is always legal-entity scoped. Sales/Procurement documents must validate legal entity/branch where the document owns those dimensions. Client-supplied scope is never trusted; effective scope is server-derived intersection of membership/grant and resource ownership.

A default branch is UX context only and never authorization.

## Separation of duties
- user.manage/role.manage cannot escape tenant membership.
- High-risk grants are audited.
- Approval can require a second actor independent from permission possession.
- A configured policy may prevent the requester/preparer from self-approving.
- Financial period reopen, journal reversal and high-risk payment should support stronger SoD/approval without redesigning permission namespaces.
- Sales price/discount and Procurement amount exceptions may require approval even when base mutation permission exists.
- Disabled user/membership invalidates protected access.

## Denial
Unauthenticated -> AUTHENTICATION_REQUIRED.
Inactive/expired membership -> deny/session invalidation.
Missing permission/scope -> PERMISSION_DENIED.
Guessed cross-tenant business ID -> RESOURCE_NOT_FOUND where disclosure would leak existence.
Invalid same-tenant state -> domain error.

## Required tests
For every protected operation when implemented:
1. allowed permission + owned scope succeeds;
2. missing permission denies;
3. out-of-scope legal entity/branch/warehouse denies;
4. disabled user/membership denies;
5. guessed other-tenant ID cannot read/mutate/reference;
6. direct API denial works independent of UI;
7. role change follows refresh policy;
8. high-risk mutation has audit evidence;
9. approval/SoD cannot be bypassed by base permission;
10. cross-core command re-authorizes source and target ownership.
