# Work Queue

Single source of truth for active work the agent can intake, refine, execute, verify, and retire.

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

_None._

## Needs refinement

_None._

## Inbox

_None._

## Done

_Transient. Delete after merge, release, or durable record._

## Cancelled

_Transient. Delete after the cancellation decision is recorded._
