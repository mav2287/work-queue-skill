# Work Queue Agent Skill

An Agent Skills-compatible skill for Claude Code and Codex. It turns large batches of bugs, fixes, chores, docs work, investigations, and feature requests into an executable work queue that agents can drain without a prompt after every item.

The skill treats the queue as an active execution system, not a product backlog or archive:

- capture raw work quickly
- refine vague reports into agent-ready tasks
- prioritize and select the next Ready item
- implement, verify, and record results
- move blocked work out of the way
- delete completed items after a durable record exists

## Install

Install for Claude Code as a user skill:

```bash
mkdir -p ~/.claude/skills/work-queue
rsync -a --exclude='.DS_Store' work-queue/ ~/.claude/skills/work-queue/
```

Install for Claude Code as a project skill:

```bash
mkdir -p .claude/skills/work-queue
rsync -a --exclude='.DS_Store' work-queue/ .claude/skills/work-queue/
```

Install for Codex as a user skill:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills/work-queue"
rsync -a --exclude='.DS_Store' work-queue/ "${CODEX_HOME:-$HOME/.codex}/skills/work-queue/"
```

Claude Code can invoke it with:

```text
/work-queue
```

Claude Code or Codex can also be asked to use `$work-queue`.

The skill itself is the `work-queue/` directory. The root of this repository is packaging, CI, and documentation for publishing.

## Queue File

The default queue file is `WORK_QUEUE.md`. A starter template lives at:

```text
work-queue/templates/WORK_QUEUE.md
```

The validator can check queue structure:

```bash
python3 work-queue/scripts/validate_queue.py WORK_QUEUE.md
```

The package validator checks skill metadata and bundled file links:

```bash
python3 scripts/validate_skill.py work-queue
```

## Repository Status

This repo is structured so the root is publishable, while the actual skill lives in `work-queue/`.

Released under the MIT License.
