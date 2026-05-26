### WQ-042 Show empty state when a list has no records

- **Type**: bug
- **Priority**: P1
- **Created**: 2026-05-23
- **Area**: records-list

**Problem / Want**
Users with zero records saw a persistent loader. They should see the
empty state and a clear next action.

**Acceptance**
- [x] Users with zero records see the empty state instead of a persistent loader.
- [x] Users with records still see the populated list.
- [x] A test covers the zero-record path.

**Notes**
Repro: sign in as a user with zero records and open the records list.

**Verification**
- `pnpm test apps/web/records/list.test.tsx`: passed
- `pnpm typecheck`: passed
- Manual: opened the list as a zero-record user and confirmed the
  empty-state CTA appears.

**Outcome**
Changed: `apps/web/records/list.tsx`, `apps/web/records/list.test.tsx`.
PR: example-org/example-app#1234. One-line summary: replaced the
unconditional `<Loader />` with a length-aware branch that renders
`<EmptyState />` when the query returns `[]`.
