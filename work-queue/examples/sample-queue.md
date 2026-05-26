# Work Queue

Single source of truth for active work.

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

### WQ-001 Show empty state when a list has no records

- **Type**: bug
- **Priority**: P1
- **Created**: 2026-05-23
- **Area**: records-list

**Problem / Want**
Users with zero records see a persistent loading state. They should see the normal empty state.

**Acceptance**
- [ ] Users with zero records see an empty state.
- [ ] Users with records still see the populated list.

**Notes**
- Repro: sign in as a user with zero records and open the records list.

## Needs refinement

_None._

## Inbox

_None._

## Done

_Transient._

## Cancelled

_Transient._
