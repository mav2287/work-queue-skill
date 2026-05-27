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

## Question Gate

Do not ask the user to do codebase research for the agent. Before asking a question, first answer:

- What exact code/docs/tests/logs could answer this?
- Did I search the named route, component, command, model, config key, error string, or visible label?
- Did I inspect the most relevant nearby files?
- Did I check existing queue items or project docs for the same decision?
- Is the remaining question about user intent, business priority, inaccessible production data, credentials, or external policy?

Only ask after those checks are exhausted or unavailable.

When a question is still needed, use this shape:

```markdown
Checked: <files/searches/docs/logs inspected>
Question: <the missing fact only the user or an external system can provide>
Why it matters: <what scope, acceptance, or priority decision depends on it>
```

Do not invent the `Checked` line. It must describe inspection actually performed in the target project. If no inspection was possible, write `Checked: not performed (<reason>)` and keep the item out of `Ready`.

If there is no time or environment to inspect the codebase, say that explicitly and put the item in `Needs refinement` or `Blocked`; do not present the question as if inspection had already happened.

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

## Expand Mode

Use `Expand` mode when the user hands the agent **one** source
document — a PRD, design doc, long bug report, RFC, or GitHub issue
body — and wants it decomposed into many queue items in one pass.
Expand is intake with a higher ceiling on output: instead of capturing
N raw reports, the agent reads one document and emits N executable
items.

### Process

1. **Read the whole document first.** Do not start emitting items until
   the full scope is understood. Skim the table of contents, headings,
   and any explicit acceptance the document already names.
2. **Identify atomic units of work.** Each unit is something a single
   agent session can complete end to end and verify. A "rebuild the
   billing UI" line is not atomic; "add the empty state to the
   invoice list" is.
3. **Assign IDs sequentially.** Pick the next free `WQ-NNN` and
   increment. Never reuse retired IDs (`queue-format.md`).
4. **Draft acceptance for each item.** Acceptance must be observable
   and testable — see `references/intake.md` "Acceptance Criteria".
   The Expand pass owns the acceptance; do not punt it to the drain
   session.
5. **Identify inter-item dependencies.** When item B genuinely cannot
   start until item A is Done, record it on item B (the schema for
   this is in `queue-format.md`).
6. **Place each item in the right section.** Items that satisfy the
   Ready bar go to `Ready`. Items the source document leaves
   ambiguous go to `Needs refinement` with the specific gap named.
   Items dependent on an external answer go to `Blocked`.
7. **Run the validator** on the resulting queue file before handing
   back to the user.

### The Question Gate Still Applies

Expand does not bypass the question gate. If the source document
does not say what the failure path should be, or whether a behavior
applies to one role or all, the resulting item goes to `Needs
refinement` with the gap named in Notes. It does **not** go to
`Ready` with a guess and a comment that says "TBD".

The `Local checks before asking` evidence is still required: items
that look ready from a quick read of the source but rest on
unverified assumptions about the target project go to `Needs
refinement` until the assumptions are checked.

### Volume and Cost

Expand can emit dozens of items in a single pass. Two cautions:

- **Do not pad the queue.** Every item the agent drafts is something
  a future session has to read. Avoid creating boilerplate items
  ("update the README to mention X") unless the source explicitly
  asks for it.
- **Stop and confirm before emitting more than ~25 items.** Long
  expansions risk pulling in scope the user did not intend. Emit the
  first batch, ask whether the user wants to continue, and proceed
  only on explicit yes.

### Example

See `work-queue/examples/expand-input.md` for a short example PRD and
`work-queue/examples/expand-output.md` for the resulting queue items.

## Secrets Hygiene

Drain encourages pasting commands, log output, and repro steps into
Notes. The queue file is committed to the repo, mirrored to every
collaborator, and read by every future drain session — so anything
pasted into Notes is durable and visible.

Never paste any of the following into Notes (or anywhere else in a
queue item):

- API tokens, OAuth client secrets, session cookies, JWTs
- database connection strings or credentials
- private keys (SSH, TLS, signing)
- environment dumps that contain the above

Recommended redaction pattern when log output is needed:

```text
Authorization: Bearer <redacted>
DATABASE_URL=postgres://<redacted>@db/app
```

If a secret was committed in error, rotate it immediately — `git rm`
or a force-push is not sufficient; the value must be considered
public the moment it reaches a remote.

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
