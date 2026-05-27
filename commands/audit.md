---
description: Validate the queue format, readiness, priority order, dependency resolution, and Done hygiene. Pass a queue path as the argument; omit to use WORK_QUEUE.md.
---

Use the work-queue skill in **Audit** mode.

Queue file: $ARGUMENTS (default `WORK_QUEUE.md`).

Run the bundled validator with both `--strict` and `--strict-sections`
and report:

- **Errors** (must fix): structural issues, unknown sections,
  duplicate ids, invalid field values, unmet hard rules.
- **Warnings** (consider fixing): stale Inbox items, duplicate
  titles, unresolved `Depends on`, Done items missing `**Outcome**`,
  Ready items still containing placeholder text or example markers,
  out-of-range Created dates.
- **Canonical-form check**: run `--fix --check` to report whether the
  file would be rewritten by `--fix`. Do not apply the fix in Audit
  mode — Audit is read-only.

When the queue file does not exist, say so and stop; do not create
one in Audit mode.
