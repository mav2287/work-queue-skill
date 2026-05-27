---
description: Delete Done and Cancelled items after a durable record exists (commit SHA, PR link, release notes, ADR). Confirms before deleting; pass --yes to skip confirmation.
---

Use the work-queue skill in **Retire** mode. Reference:
`SKILL.md` "Retention".

Flags: $ARGUMENTS

For each item in `Done` and `Cancelled`:

1. Confirm a durable record exists. Look in the item's `**Outcome**`
   subsection for a commit SHA, PR link, release entry, or other
   long-lived artifact. If none is present, the item is not safe to
   retire — leave it and report it as needing an Outcome first.
2. If a durable record exists, mark the item for deletion.

Unless the arguments contain `--yes`, summarize the proposed
deletions (ids, titles, durable-record references) and wait for the
user to confirm before applying any changes.

After deletion:

- Run `python3 <skill-dir>/scripts/validate_queue.py --strict
  WORK_QUEUE.md` to confirm the file still parses.
- Report what was retired and what (if anything) was kept back.

Do not mention transient queue ids in commit messages, PR titles, or
other durable artifacts during retirement — the ids are not durable
unless the host project explicitly treats them as such.
