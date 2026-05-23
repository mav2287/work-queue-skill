# Claude Work Queue Skill

A Claude Code skill for turning large batches of bugs, fixes, chores, docs work, investigations, and feature requests into an executable work queue that agents can drain without a prompt after every item.

The skill treats the queue as an active execution system, not a product backlog or archive:

- capture raw work quickly
- refine vague reports into agent-ready tasks
- prioritize and select the next Ready item
- implement, verify, and record results
- move blocked work out of the way
- delete completed items after a durable record exists

## Install

As a Claude Code user skill:

```bash
mkdir -p ~/.claude/skills/work-queue
cp -R work-queue/* ~/.claude/skills/work-queue/
```

As a project skill:

```bash
mkdir -p .claude/skills/work-queue
cp -R work-queue/* .claude/skills/work-queue/
```

Then invoke it with:

```text
/work-queue
```

or ask Claude to use `$work-queue`.

## Queue File

The default queue file is `WORK_QUEUE.md`. A starter template lives at:

```text
work-queue/templates/WORK_QUEUE.md
```

The validator can check queue structure:

```bash
python3 work-queue/scripts/validate_queue.py WORK_QUEUE.md
```

## Repository Status

This repo is structured so the root is publishable, while the actual skill lives in `work-queue/`.

No license has been added yet. Add one before public release if you want explicit reuse rights.
