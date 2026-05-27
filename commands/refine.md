---
description: Raise existing Needs refinement or Inbox items to the Ready bar. Pass an item id (e.g. WQ-007) to focus on one item; omit to refine the whole queue.
---

Use the work-queue skill in **Refine** mode. References:
`SKILL.md` "Ready Bar" and `references/intake.md`.

Focus: $ARGUMENTS (if empty, refine every item in `Needs refinement`
and triage the contents of `Inbox`).

For each item:

1. Verify what can be verified locally before asking the user
   anything (apply the question gate).
2. If scope, repro, acceptance, and impacted users are all clear,
   move to `Ready`.
3. If the report is real but missing pieces, keep it in
   `Needs refinement` and name the specific gaps in Notes.
4. If the work depends on an external answer or artifact, move it to
   `Blocked` with a `Blocked on` or `Questions` marker.

Do not promote an item to `Ready` by guessing — the question gate
applies. If you must ask the user a question, include a `Checked:`
line listing inspection actually performed.
