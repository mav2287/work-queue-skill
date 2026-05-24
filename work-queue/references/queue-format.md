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
<repro steps, links, file paths, commands, decisions, dependencies, and verification results>
```

Field and acceptance bullets may be indented, but the item heading must be a normal Markdown heading (`### WQ-001 ...`) outside of a fenced code block.

## Section Semantics

`Inbox`: raw captured input. It may be duplicated, vague, or unverified.

`Needs refinement`: real work, but not executable yet. Missing scope, repro, acceptance, impacted users, or technical verification.

`Ready`: executable end to end by an agent without returning to the requester for basic scope.

`In progress`: actively being worked. Prefer one item at a time unless the user explicitly asks for parallel execution.

`Blocked`: cannot proceed without an external answer, dependency, credential, approval, or missing artifact. Include a `Questions` or `Blocked on` line.

`Done`: completed and verified, waiting for retirement. Keep transient.

`Cancelled`: intentionally not doing the work, waiting for retirement. Keep transient.
