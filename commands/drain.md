---
description: Continuously execute Ready items until the queue is empty, blocked, or a user-specified limit is reached. Pass an integer limit (e.g. "3") to cap the run; omit for unlimited.
---

Use the work-queue skill in **Drain** mode. Reference:
`references/drain.md`.

Optional limit: $ARGUMENTS

Before starting:

1. Run the validator: `python3 <skill-dir>/scripts/validate_queue.py
   --strict WORK_QUEUE.md`.
2. Check `In progress`. If it holds an item the current session did
   not put there, stop and ask the user whether to continue,
   re-claim, or revert it to `Ready` (see `references/drain.md`
   "Resuming a Drain"). Do not silently take a second item alongside.

For each selected Ready item:

1. Skip items whose `Depends on` targets are not all `Done`.
2. Move the item to `In progress` as a **separate edit** before any
   code changes. Do not collapse `Ready` → `In progress` and
   `In progress` → `Done` into one write.
3. Implement the smallest complete change that satisfies acceptance.
4. Verify; record `**Verification**` hand-written with the commands
   you ran and their results.
5. Auto-populate `**Outcome**` from `git diff --name-only` since the
   In progress claim, the head commit SHA, and one prose sentence
   describing what shipped.
6. Move to `Done`, or to `Blocked` with exact missing information.
7. Commit per item with the queue id omitted from the durable commit
   message.

Stop when no Ready items remain (or all remaining are blocked by
unmet dependencies), a required tool or approval is unavailable,
verification fails and further progress would mean guessing, or the
user-provided limit is reached. Report the queue state and the next
concrete unblocker.
