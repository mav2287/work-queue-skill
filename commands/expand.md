---
description: Decompose a single PRD, design doc, or long issue body into many Ready queue items in one pass. Paste the source as the argument.
---

Use the work-queue skill in **Expand** mode. Reference:
`references/intake.md` "Expand Mode".

Source document: $ARGUMENTS

Process:

1. Read the whole document first; do not start emitting items until
   the full scope is understood.
2. Identify atomic units of work — each unit must be completable end
   to end by a single agent session.
3. Assign sequential `WQ-NNN` ids; never reuse retired ids.
4. Draft observable, testable acceptance for each item; do not punt
   acceptance to the drain session.
5. Identify inter-item dependencies and record them on the dependent
   item via the `Depends on` field.
6. Place each item in the right section. Items whose scope cannot be
   inferred from the source go to `Needs refinement` with the gap
   named — never to `Ready` with a guess.
7. Run the validator on the resulting queue before handing back.

If the expansion would emit more than ~25 items, stop after the first
batch and confirm with the user before continuing.

If no source document is supplied, ask the user for one before
proceeding.
