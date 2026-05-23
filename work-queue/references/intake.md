# Intake

Use intake to turn many bug reports, fixes, chores, and feature requests into queue items without forcing the user to supervise every decision.

## Intake Workflow

1. Capture the raw item.
2. Check for duplicates or related active items.
3. Verify cheap facts locally before asking the user.
4. Identify the smallest useful work item.
5. Write testable acceptance criteria.
6. Put the item in the correct section.
7. Continue until the whole batch is classified.

## Verify Before Asking

Use available project context first:

- Search code for named routes, components, commands, models, config, and error strings.
- Inspect relevant tests, logs, screenshots, issues, docs, or previous queue items when available.
- Reproduce simple bugs locally when the environment is available.
- Preserve source evidence in Notes with file paths, command output summaries, or links.

Do not ask the user a question that local inspection can answer quickly.

## Clarifying Questions

Ask questions only when the answer changes scope, priority, acceptance, or feasibility.

Prefer batched questions for large intake. Group by item and ask the minimum set needed to decide whether an item is Ready.

Good questions:

- Which role, tenant, plan, device, browser, or account is affected?
- What exact URL and click path reproduces it?
- What should happen instead?
- Is the reported threshold, field, or label exact?
- Is this a launch blocker or regular priority?

Poor questions:

- Anything a quick repo search would answer.
- Broad "can you clarify?" prompts without naming the missing decision.
- Questions about implementation preference when acceptance is already clear.

## Readiness Decisions

Place in `Ready` when scope, repro or investigation target, acceptance, and likely verification are clear.

Place in `Needs refinement` when the report is real but missing details an agent would need before implementation.

Place in `Blocked` when work depends on an external answer, another active item, unavailable credential, production log, approval, or vendor/system state.

Leave in `Inbox` only during initial capture or when the input has not yet been triaged.

## Acceptance Criteria

Acceptance must be observable and testable. Include failure paths, edge cases, and verification expectations.

Avoid vague acceptance:

- "UI works."
- "Fix auth bug."
- "Make it better."

Prefer concrete acceptance:

- "Users with zero records see the empty state instead of a crash."
- "Malformed CSV rows are skipped with a visible row-level error."
- "Unauthenticated requests are redirected without creating a session record."

## Investigations

Use `investigation` when the deliverable is a decision, not production code.

Investigation acceptance should say:

- what question must be answered
- what evidence must be collected
- where the decision will be recorded
- whether follow-up implementation items should be opened

Do not close an investigation by quietly writing production code unless the queue item explicitly allows that.
