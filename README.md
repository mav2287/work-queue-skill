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

Install for Codex CLI as a user skill (path documented at
[developers.openai.com/codex/skills](https://developers.openai.com/codex/skills)):

```bash
mkdir -p "$HOME/.agents/skills/work-queue"
rsync -a --exclude='.DS_Store' work-queue/ "$HOME/.agents/skills/work-queue/"
```

Install for Codex CLI as a repository skill (checked in for the team):

```bash
mkdir -p .agents/skills/work-queue
rsync -a --exclude='.DS_Store' work-queue/ .agents/skills/work-queue/
```

Older Codex CLI releases also discovered skills at `~/.codex/skills/`.
If you target a release that still uses that path, mirror the install
into both directories until you have upgraded.

## Invoking the Skill

After installation the skill is auto-discovered by the agent from its
`SKILL.md` frontmatter. There is no separate `/work-queue` slash command
unless the host project registers one — invoke the skill by either:

- mentioning it in a prompt with the `$` prefix, for example
  `use $work-queue to triage the inbox`, or
- letting the agent select it automatically when a request matches the
  description in `work-queue/SKILL.md`.

A first-run prompt that exercises the skill end-to-end:

```text
Use $work-queue to read WORK_QUEUE.md, validate it, and start draining
Ready items until the queue is empty or blocked.
```

The skill itself is the `work-queue/` directory. The root of this
repository is packaging, CI, and documentation for publishing.

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
