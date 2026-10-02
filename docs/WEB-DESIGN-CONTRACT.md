# NOMOS Web ERP Design Contract

Status: PASS — Phase 0 design translation.
Source basis: user-approved DESIGN.md supplied for the desired Web appearance. This contract translates that visual language to ERP surfaces; it does not replace domain/security contracts.

## Visual direction
Professional editorial SaaS/ERP: restrained, information-dense without feeling cramped, clear hierarchy, minimal decorative chrome.

Core tokens from approved source:
- app background #FAFAFA;
- primary surfaces white;
- interactive/accent Indigo #6366F1;
- spacing follows a 4px grid;
- card radius 12px;
- control radius 6px;
- elevation is restrained and used primarily for interaction/overlay hierarchy;
- Indigo communicates interaction/selection/status emphasis, not decoration.

Typography direction from source: General Sans / DM Sans with JetBrains Mono for codes, identifiers and numeric/technical content. Implementation must provide production-safe font loading/fallbacks without shipping unlicensed font files.

## ERP shell
Persistent desktop sidebar + top/header context area + main content. Sidebar groups follow product IA, not community-platform navigation.
Initial Inventory MVP:
Dashboard; Inventory (Stock, Receive, Issue, Transfer, Adjustment, Stock Count, Movements, Low Stock); Master Data (Products, Categories, Units, Warehouses, Locations); Management (Users, Roles & Permissions, Audit Log, Settings). Approvals appears when implemented; LINE remains hidden until its phase.

Tenant/company/branch context must be visible where operationally relevant, but a selector is never an authorization boundary.

## Page anatomy
List: page title + concise context + primary action; filter/search bar; data table; pagination.
Detail/document: identity/status header; metadata; lines/content; audit/reference area; action bar.
Form: grouped fields with labels/help/errors; no placeholder-only labels.
Dashboard: operational KPIs and actionable exceptions, not decorative charts.

## Components
DataTable: stable column alignment, sortable allowlisted columns, row selection only where bulk action is valid, empty/loading/error states, horizontal handling on tablet.
FilterBar: search + explicit filters; active filters visible and removable.
StatusBadge: semantic status; color is never sole carrier.
KpiCard: label/value/context/action; avoid chart decoration without decision value.
DocumentLines: product/unit/location/quantity columns optimized for keyboard entry; exact decimal display.
Form controls: 6px radius; visible focus; validation near field.
Card/Panel: 12px radius, subtle border/surface hierarchy; avoid excessive shadow.
Modal: confirmation/short focused task only.
Drawer: contextual inspect/edit where preserving list context is useful; not a substitute for complex document page.
Toast: acknowledgement, never the only place for critical error details.
AuditTimeline: actor/action/time/result/reason/reference with safe metadata.
Skeleton/Empty/Error: first-class states.

## Inventory UX
Receive/Issue/Transfer/Adjustment never report success before server commit.
Show document/transaction number and POSTED result after success.
Issue displays stock context but final sufficiency is server-validated in locked transaction.
Transfer clearly separates From and To and prevents same-location selection.
Adjustment is visually higher-risk, requires reason, and confirms before posting.
Reversal is an explicit action on posted transaction, never Edit/Delete.
Stock balance is a read projection; UI never exposes direct balance edit.

## Tables and numbers
SKU/document numbers use mono where useful. Numeric columns right-align. Quantities preserve meaningful unit precision without binary-float formatting. Dates/times display in user/tenant timezone with unambiguous detail on inspect. Table density may offer comfortable/compact later but default remains readable.

## States and permissions
Hide or disable unavailable actions for UX, while server authorization remains mandatory. Disabled state should explain why when useful. DRAFT/PENDING/POSTED/CANCELLED/REVERSED semantics follow domain contract, not arbitrary UI labels.

## Responsive/accessibility
Desktop is primary; tablet/barcode-scanner workflows are supported. Mobile may support read/light operations but is not allowed to distort desktop ERP information architecture.
Keyboard navigation, visible focus, semantic labels, contrast, non-color status cues and reasonable target sizes are required.
Thai/English content must not break layout; avoid fixed widths based only on English labels.

## Design anti-patterns
- Indigo everywhere as decoration;
- large empty marketing-style hero areas inside ERP;
- dashboard charts with no operational action;
- hidden critical fields behind hover only;
- direct-edit stock balance;
- optimistic stock POSTED state before server response;
- destructive delete for business history;
- dozens of Coming Soon menu items;
- inconsistent radii/spacing invented per screen.

## Implementation gate
Before Phase 5 E2E acceptance, create shared design tokens/components rather than per-page CSS copies. Visual implementation is checked against this contract and the approved source design, while business behavior is checked against domain/API contracts.
