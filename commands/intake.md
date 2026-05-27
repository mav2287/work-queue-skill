---
description: Capture raw work items into the queue without starting implementation. Pass items inline as arguments, or invoke with no arguments to triage what the user describes next.
---

Use the work-queue skill in **Intake** mode. References:
`SKILL.md` "Operating Modes" and `references/intake.md`.

Input to capture: $ARGUMENTS

Apply the question gate before asking the user anything: verify what
can be verified locally (search the codebase for named routes,
components, commands, errors; inspect nearby tests, docs, and existing
queue items) before requesting clarification. Place each item in:

- `Ready` — executable end to end by an agent without further scope clarification.
- `Needs refinement` — real work, but missing scope / repro / acceptance / impacted users.
- `Blocked` — depends on an external answer, dependency, credential, approval, or vendor state.
- `Inbox` — only during initial capture when the input has not yet been triaged.

If no arguments are supplied, ask the user what they want to capture
and apply the same rules to whatever they provide.
