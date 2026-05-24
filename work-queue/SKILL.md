---
name: work-queue
description: Intake, refine, prioritize, and autonomously drain a Markdown work queue for bugs, fixes, chores, docs, investigations, and feature work. Use when the user wants to capture many work items, turn vague reports into agent-ready tasks, verify codebase facts before asking clarifying questions, pick the next item, run a queue without repeated prompting, move work through Ready/In progress/Blocked/Done, validate queue structure, or clean up completed items.
---

# Work Queue

## Overview

Manage a Markdown work queue as an execution system, not an archive. Convert raw reports into clear, testable work items, then keep pulling Ready items until the queue is empty, blocked, or the user gives a stopping condition.

Default queue file: `WORK_QUEUE.md`. If the repo already has a queue/backlog file, use that file unless the user asks to migrate.

## Operating Modes

Choose the mode from the user's request:

- **Intake**: capture many raw reports without starting implementation.
- **Refine**: raise existing items to the Ready bar.
- **Drain**: repeatedly execute Ready items with minimal user intervention.
- **Audit**: validate queue format, readiness, priority order, and blocked/done hygiene.
- **Retire**: delete shipped Done/Cancelled items after their durable record exists elsewhere.

Read the matching reference only when needed:

- [references/queue-format.md](references/queue-format.md): statuses, fields, IDs, priorities, and templates.
- [references/intake.md](references/intake.md): mass intake and readiness rules.
- [references/drain.md](references/drain.md): autonomous execution loop and stopping conditions.
- [templates/WORK_QUEUE.md](templates/WORK_QUEUE.md): starter queue file.

## Intake Rules

Verify what can be verified locally before asking the user. Use code search, tests, logs, issue context, screenshots, and existing docs where available.

Before asking any clarifying question, pass the question gate:

1. List the exact local checks that could answer the question.
2. Run the cheap checks first: search named routes/components/errors/config, inspect nearby docs/tests, and read existing queue items.
3. Ask only for facts that still cannot be recovered locally.
4. When asking, include a short `Checked:` line so the user is not sent back to inspect the same codebase.

Do not turn vague reports into Ready items. If scope, repro, affected user, expected behavior, observed behavior, or acceptance criteria are missing, place the item in `Needs refinement` or `Blocked`.

For large batches, keep intake moving:

1. Capture every raw item.
2. Group duplicates and related reports.
3. Verify cheap facts from the repo before asking.
4. Ask batched clarifying questions only for items that cannot be made executable.
5. Put clear work in `Ready`; put real-but-unclear work in `Needs refinement`; put externally dependent work in `Blocked`.

## Ready Bar

An item is Ready only when a capable agent can complete it end to end without asking what the user meant.

Ready items must include:

- specific scope and area
- expected behavior and observed behavior for bugs
- repro path or investigation target
- testable acceptance criteria, including failure paths
- notes with relevant file paths, commands, links, logs, screenshots, or decisions
- priority and type from the allowed values

## Drain Loop

When the user asks to run the queue, continue without stopping after each item:

1. Validate or inspect the queue.
2. Check current worktree state when the project uses git and preserve unrelated user changes.
3. Select the next Ready item by priority, then age, unless the user provides another rule.
4. Move exactly one item to `In progress`.
5. Implement the smallest complete change that satisfies acceptance.
6. Run appropriate verification.
7. Record verification in Notes.
8. Move the item to `Done`, or to `Blocked` with exact missing information.
9. Commit, checkpoint, or otherwise isolate the completed item when the project workflow supports it.
10. Repeat until no Ready items remain, a command/approval/tool is blocked, or the user-specified limit is reached.

Do not silently change scope. If the implementation reveals a separate problem, add a new queue item instead of expanding the current one.

## Validation

Run the validator when creating or changing a queue:

```bash
python3 /absolute/path/to/installed/work-queue/scripts/validate_queue.py WORK_QUEUE.md
```

Resolve the script path relative to this `SKILL.md` file; the bundled validator lives at `scripts/validate_queue.py`.

Use `--allow-done` when the project intentionally keeps Done items temporarily.

## Retention

The queue tracks active work only. Delete Done and Cancelled items after the work has a durable record in code, a merged PR, release notes, issue tracker, ADR, or another long-lived artifact.
