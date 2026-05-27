# Queue Format

Use this format when creating or normalizing a queue file.

## Sections

Valid status sections, in order:

1. `## In progress`
2. `## Blocked`
3. `## Ready`
4. `## Needs refinement`
5. `## Inbox`
6. `## Done`
7. `## Cancelled`

Status is the section the item lives in. Move the entire item block between sections; do not duplicate it.

The validator warns when sections are missing by default so existing project queues can adopt the skill incrementally. Use `--strict-sections` to require this exact section set and order.

## Item IDs

Use `WQ-001`, `WQ-002`, and so on by default. Never reuse retired IDs.

Project-specific prefixes are allowed when an existing queue already uses them. Keep one prefix per queue unless migrating.

## Types

Allowed values:

- `bug`: expected and actual behavior differ.
- `feature`: new capability.
- `chore`: maintenance without intended behavior change.
- `docs`: documentation only.
- `refactor`: internal change with behavior preserved.
- `investigation`: answer an unknown before implementation can be scoped.

Do not invent new types without updating the queue's own rules.

## Priorities

- `P0`: drop everything.
- `P1`: next.
- `P2`: soon.
- `P3`: someday.

When draining without extra instructions, choose the oldest `Ready` item in the highest available priority.

## Created Date Sanity

`Created` must be `YYYY-MM-DD`. The validator warns when `Created` is in
the future or earlier than `2020-01-01` because both are usually typos.
Adjust the lower bound by editing `EARLIEST_SANE_DATE` in
`work-queue/scripts/validate_queue.py` for legacy projects.

## Local checks before asking (optional)

A Ready item may include a `**Local checks before asking**` subsection
inside Notes that names files, searches, docs, logs, or other queue
items the agent inspected before bringing a question back to the
human. It is the durable form of the question gate described in
`references/intake.md`.

The validator treats it as a recognized body heading so it terminates
the Acceptance block cleanly. The validator does not require it to be
present, but it warns if a Ready item still contains the literal text
"Example only" — that is the template placeholder and should be
replaced with real evidence.

## Verification and Outcome on Done items

When an item moves to `Done`, the body should grow two new
subsections:

- `**Verification**` — concise list of commands run and their results
  (passed/failed/skipped). Required by the validator under `--strict`.
  **Hand-written**: the variability is the value. Do not auto-fill.
- `**Outcome**` — what shipped: changed file paths, commit SHA or PR
  link, and a one-line summary. The validator warns when it is
  missing on a Done item. This is the durable record that survives
  retirement. **Auto-populated** from observable state during drain;
  see below.

### Auto-populated Outcome shape

The drain agent fills Outcome from data it already has at the moment
of completion:

- **Changed paths** come from `git diff --name-only` between the
  worktree's state when the item moved to `In progress` and the state
  when it moves to `Done`. Untracked files added during the item are
  included.
- **Commit reference** is the head SHA at completion. If a PR exists,
  the PR URL is included alongside the SHA.
- **One-line summary** is the only hand-written piece: a single
  sentence describing what shipped.

Example:

```markdown
**Outcome**
Changed: `apps/web/invoices/list.tsx`, `apps/web/invoices/list.test.tsx`.
Commit: a1b2c3d. PR: example-org/example-app#1234.
One-line summary: replaced the unconditional loader with a length-aware
branch that renders the empty state when the query returns no records.
```

When the project does not use git, the agent records the affected
paths it modified directly and notes "no commit" in place of the SHA.

## Item Template

```markdown
### WQ-XXX <short imperative title>

- **Type**: bug | feature | chore | docs | refactor | investigation
- **Priority**: P0 | P1 | P2 | P3
- **Created**: YYYY-MM-DD
- **Area**: <system, feature, package, docs, ci, etc.>

**Problem / Want**
<what is wrong or wanted, who is affected, and why it matters>

**Acceptance**
- [ ] <observable, testable condition for done>
- [ ] <failure path, edge case, or verification requirement>

**Notes**
<repro steps, local checks performed before asking, links, file paths, commands, decisions, dependencies, and verification results>
```

Field and acceptance bullets may be indented, but the item heading must be a normal Markdown heading (`### WQ-001 ...`) outside of a fenced code block.

## Known Limits and Scaling Path

The v1 schema is a single Markdown file per queue. That is intentional:
one file diffs cleanly, reviews easily, and stays portable across every
agent that loads markdown.

The single-file design becomes uncomfortable past roughly **50 active
items** (Ready + In progress + Blocked + Needs refinement combined).
Symptoms are predictable: merge conflicts on every PR, slow scroll,
duplicate items because nobody can see the existing ones, and a
section-reordering nightmare on hand edits.

Current workarounds:

- run `--fix` regularly so the file is always canonically ordered;
- aggressively retire Done and Cancelled items;
- split per-area (`frontend/WORK_QUEUE.md`, `backend/WORK_QUEUE.md`)
  and lint all of them in one CI step with the multi-file invocation.

Planned future evolution (not in v1):

- **index plus per-item files** — `WORK_QUEUE.md` becomes a short
  `- [ ]` index that links to per-item details under
  `work-queue/items/WQ-NNN.md`. Each item file carries YAML
  frontmatter (`id`, `status`, `priority`, `created`, `deps`) and
  Markdown body. This survives merges (each item is its own file),
  scales past hundreds of items, and keeps the at-a-glance review
  experience of the index. It is the pattern Backlog.md and Spec Kit
  converged on independently.

The item IDs and body schema in this document are designed to migrate
to the hybrid layout without rewriting items; only the location and
container change.

## Section Semantics

`Inbox`: raw captured input. It may be duplicated, vague, or unverified.

`Needs refinement`: real work, but not executable yet. Missing scope, repro, acceptance, impacted users, or technical verification.

`Ready`: executable end to end by an agent without returning to the requester for basic scope.

`In progress`: actively being worked. Prefer one item at a time unless the user explicitly asks for parallel execution.

`Blocked`: cannot proceed without an external answer, dependency, credential, approval, or missing artifact. Include a `Questions` or `Blocked on` line.

`Done`: completed and verified, waiting for retirement. Keep transient.

`Cancelled`: intentionally not doing the work, waiting for retirement. Keep transient.
