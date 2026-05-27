# Work Queue

Result of running Expand mode against `expand-input.md`. The four PRD
goals decompose into four Ready items, plus one item parked in `Needs
refinement` because the source document explicitly leaves a design
question open.

## Queue Rules

- Status is the section the item lives in. Move the whole item; do not duplicate it.
- `Ready` means an agent can execute the item end to end without returning to the requester for basic scope.
- `Done` and `Cancelled` are transient. Delete them after a durable record exists.
- Default priority order: `P0`, `P1`, `P2`, `P3`.
- Default type values: `bug`, `feature`, `chore`, `docs`, `refactor`, `investigation`.

## In progress

_None._

## Blocked

_None._

## Ready

### WQ-101 Show empty state on the invoice list when the user has zero invoices

- **Type**: bug
- **Priority**: P1
- **Created**: 2026-05-20
- **Area**: invoices

**Problem / Want**
Users with no invoices see a persistent loader on `apps/web/invoices/list.tsx`. They should see the design-system empty state with a clear next action. Support has fielded ~15 tickets traceable to this and the related issues in this PRD.

**Acceptance**
- [ ] Users with zero invoices see the standard empty state instead of a persistent loader.
- [ ] Users with one or more invoices still see the populated list.
- [ ] The zero-invoice path is covered by a test or documented manual verification using a zero-invoice account (see WQ-104).

**Notes**
**Local checks before asking**
- Read `apps/web/invoices/list.tsx`; the loader branch is unconditional.
- Confirmed the design system exports `EmptyState` at `apps/ui/empty-state/index.tsx`.

PRD goal 1. Empty-state link target is the subject of WQ-105 (Needs refinement).

### WQ-102 Sub-sort invoices sharing a created_at by id descending

- **Type**: bug
- **Priority**: P2
- **Created**: 2026-05-20
- **Area**: invoices

**Problem / Want**
Invoices sharing a `created_at` date appear in nondeterministic order, so the list shuffles between reloads. Per PRD this is a client-side fix only.

**Acceptance**
- [ ] When two or more invoices share a `created_at`, the row with the larger `id` appears first.
- [ ] The order is stable across reloads (a regression test enforces this).
- [ ] No server-side change required.

**Notes**
**Local checks before asking**
- Sort logic at `apps/web/invoices/list.tsx` uses `Array.prototype.sort` with a comparator on `created_at` only; no tiebreaker.

PRD goal 2 and non-goal.

### WQ-103 Fall back to the customer email when display name is blank

- **Type**: bug
- **Priority**: P2
- **Created**: 2026-05-20
- **Area**: invoices

**Problem / Want**
Rows render an empty container when `customer.displayName` is blank. The row looks broken. Falling back to `customer.email` produces a recognizable identifier.

**Acceptance**
- [ ] Rows with a non-blank `customer.displayName` render unchanged.
- [ ] Rows with a blank `customer.displayName` render `customer.email` in its place.
- [ ] Rows with both fields blank still render the row without console errors (the row is unusual but should not break the page).

**Notes**
**Local checks before asking**
- Render branch is at `apps/web/invoices/row.tsx` line ~42; the conditional only checks for `customer` truthiness, not `displayName`.

PRD goal 3.

### WQ-104 Add a zero-invoice account to the QA fixture set

- **Type**: chore
- **Priority**: P3
- **Created**: 2026-05-20
- **Area**: qa

**Problem / Want**
The empty state in WQ-101 has no fixture coverage today; QA has to create the account by hand each test cycle. A standing fixture removes that friction and gates regressions in CI.

**Acceptance**
- [ ] A `zero_invoice_user` fixture exists in the QA seed data set.
- [ ] CI E2E suite has at least one test that signs in as that user and asserts the empty state renders.

**Notes**
**Local checks before asking**
- Seed data lives at `tools/seed/fixtures.json`; no zero-invoice account currently.

PRD goal 4.

## Needs refinement

### WQ-105 Decide what the invoice-list empty state should link to

- **Type**: investigation
- **Priority**: P2
- **Created**: 2026-05-20
- **Area**: invoices

**Problem / Want**
PRD lists this as an open product question: should the empty-state CTA link to "create invoice" or to the import flow? The Ready item that implements the empty state (WQ-101) needs an answer before its CTA is wired.

**Acceptance**
- [ ] Product records a decision: create-invoice link, import link, both, or none.
- [ ] Decision recorded in the PRD or a follow-up doc.
- [ ] If "both," a follow-up Ready item is filed to choose between them at render time.

**Notes**
**Local checks before asking**
- PRD "Open questions" section explicitly leaves this undecided.

**Questions**
- Should the empty-state CTA target create-invoice, import, or both?

## Inbox

_None._

## Done

_Transient. Delete after merge, release, or durable record._

## Cancelled

_Transient. Delete after the cancellation decision is recorded._
