### WQ-014 Show empty state when a list has no records

- **Type**: bug
- **Priority**: P1
- **Created**: 2026-05-23
- **Area**: records-list

**Problem / Want**
Users with zero records see a persistent loading state. They should see the normal empty state and a clear next action.

**Acceptance**
- [ ] Users with zero records see an empty state instead of a persistent loader.
- [ ] Users with records still see the populated list.
- [ ] The failure path is covered by a test or documented manual verification using a zero-record account.

**Notes**
**Local checks before asking**
- Searched `apps/web/records/` for the loader component and confirmed the empty-state branch is missing.
- Read existing test `apps/web/records/list.test.tsx`; it does not cover the zero-record path.
- Checked WORK_QUEUE.md for prior related items; no duplicates.

Repro:
- Sign in as a user with zero records and open the records list.
