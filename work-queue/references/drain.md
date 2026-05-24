# Autonomous Drain

Use drain mode when the user wants the agent to keep clearing queued work instead of waiting for a new instruction after each item.

## Start Conditions

Before changing code:

1. Read the queue rules and the selected item.
2. Run the validator if a queue file exists and the script is available.
3. Confirm there is a `Ready` item.
4. If the project uses git, check worktree status and identify unrelated user changes before editing.
5. Move one selected item to `In progress`.
6. Note the selection rule if it was not obvious.

Default selection: highest priority first, then oldest created date, then lowest ID.

## Execution Loop

Repeat:

1. Re-read the active item and acceptance criteria.
2. Inspect the relevant code/docs/tests.
3. Implement the smallest complete change that satisfies the item.
4. Run targeted verification first, then broader checks when risk warrants it.
5. Update Notes with verification commands and results.
6. Check every acceptance box that is genuinely satisfied.
7. Move the item to `Done`, or move it to `Blocked` with exact questions or dependencies.
8. Checkpoint the completed item.
9. Pick the next `Ready` item and continue.

Do not stop after one successful item unless the user gave an item limit, time limit, budget limit, or explicitly asked to pause.

## Stopping Conditions

Stop and report when:

- no `Ready` items remain
- all remaining items are `Blocked`, `Needs refinement`, or `Inbox`
- a required command, credential, approval, network action, or external system is unavailable
- verification fails and further progress would mean guessing
- the user-specified item/time/budget limit is reached

When stopping, report the queue state and the next concrete unblocker.

## Scope Control

Never silently expand an item. If a separate issue appears, add a new queue item with evidence and continue the current item only if possible.

If acceptance is wrong or incomplete, prefer one of these:

- update the item if the change is an obvious refinement within the same scope
- add a `Questions` line and move it to `Blocked`
- create a new `Needs refinement` item for the discovered work

## Verification Notes

Record verification in Notes using concise command/result lines:

```markdown
**Verification**
- `pnpm test path/to/test.test.ts`: passed
- `pnpm typecheck`: passed
```

If verification could not run, record the reason and whether the item remains Done or must be Blocked.

## Checkpoints

Keep each item independently reviewable.

When the project uses git:

- Run status before starting each item and after finishing it.
- Do not overwrite unrelated user changes.
- Prefer one commit per completed queue item when the user has asked for an autonomous drain and commits are allowed.
- If commits are not allowed or not wanted, record the item boundary in Notes and keep changes grouped so the next item does not depend on unverified leftovers.
- Stop before the next item if the worktree has unresolved conflicts, failing verification from the completed item, or changes you cannot confidently attribute.

When committing, omit transient queue IDs from durable commit messages unless the project explicitly treats those IDs as durable.

## Retiring Items

After a merge, release, or other durable record exists, delete Done and Cancelled items instead of keeping an archive in the queue.

Do not mention transient queue IDs in code comments, durable docs, commit messages, PR titles, or PR bodies unless the owning project explicitly wants those IDs to be durable.
