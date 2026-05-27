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

### Claude Code: install as a plugin (recommended)

This repository is its own Claude Code [plugin
marketplace](https://code.claude.com/docs/en/plugin-marketplaces). Add
the marketplace once, install the plugin, and updates flow via
`claude plugin update`.

```bash
claude plugin marketplace add mav2287/work-queue-skill
claude plugin install work-queue@work-queue-skill
```

The plugin caches under `~/.claude/plugins/cache/` and the skill is
namespaced as `work-queue:work-queue` (slash invocation), or you can
mention it with `$work-queue`. To update later:

```bash
claude plugin update work-queue
```

### Claude Code: bare-skill install (fallback when `claude plugin` is unavailable)

This is the older path: copy the skill directory into a Claude
skill-loading location. Works without the plugin CLI.

Project-scope (checked into the repo's `.claude/skills/`):

```bash
mkdir -p .claude/skills/work-queue
rsync -a --exclude='.DS_Store' work-queue/ .claude/skills/work-queue/
```

User-scope (available across every project on the machine):

```bash
mkdir -p ~/.claude/skills/work-queue
rsync -a --exclude='.DS_Store' work-queue/ ~/.claude/skills/work-queue/
```

If you have both a plugin install and a bare-skill install, the
plugin copy takes precedence.

### Codex CLI

Codex does not (yet) participate in the Claude Code plugin
marketplace. Use the bare-skill install for Codex.

User-scope (path documented at
[developers.openai.com/codex/skills](https://developers.openai.com/codex/skills)):

```bash
mkdir -p "$HOME/.agents/skills/work-queue"
rsync -a --exclude='.DS_Store' work-queue/ "$HOME/.agents/skills/work-queue/"
```

Repo-scope (checked in for the team):

```bash
mkdir -p .agents/skills/work-queue
rsync -a --exclude='.DS_Store' work-queue/ .agents/skills/work-queue/
```

Older Codex CLI releases also discovered skills at `~/.codex/skills/`.
If you target a release that still uses that path, mirror the install
into both directories until you have upgraded.

### Verify the install

After installation, confirm the skill is present and well-formed.

For the plugin install, list installed plugins and confirm
`work-queue` is enabled:

```bash
claude plugin list
```

For a bare-skill install, pick the snippet that matches your target.

Claude Code, user-scope:

```bash
test -f "$HOME/.claude/skills/work-queue/SKILL.md" \
  && python3 "$HOME/.claude/skills/work-queue/scripts/validate_queue.py" \
       --strict-sections "$HOME/.claude/skills/work-queue/templates/WORK_QUEUE.md"
```

Claude Code, project-scope (run from the repo root):

```bash
test -f .claude/skills/work-queue/SKILL.md \
  && python3 .claude/skills/work-queue/scripts/validate_queue.py \
       --strict-sections .claude/skills/work-queue/templates/WORK_QUEUE.md
```

Codex CLI, user-scope:

```bash
test -f "$HOME/.agents/skills/work-queue/SKILL.md" \
  && python3 "$HOME/.agents/skills/work-queue/scripts/validate_queue.py" \
       --strict-sections "$HOME/.agents/skills/work-queue/templates/WORK_QUEUE.md"
```

Each snippet exits 0 only when both the `SKILL.md` file is present and
the bundled starter template validates — that is, the skill installed
correctly and its validator can execute. Then in the agent, ask:

```text
Use $work-queue and tell me which queue file you would operate on.
```

A response that names `WORK_QUEUE.md` (and offers to create it if
missing) means the agent has discovered the skill.

## Invoking the Skill

After installation the skill is auto-discovered by the agent from its
`SKILL.md` frontmatter. Four ways to invoke it:

- **Mention prefix** — `use $work-queue to triage the inbox`. Works
  regardless of install method.
- **Automatic selection** — the agent picks the skill on its own when
  a request matches the description in `SKILL.md`.
- **Namespaced slash command** (plugin install only) —
  `/work-queue:work-queue` selects the plugin's skill explicitly.
- **Per-mode slash commands** (plugin install only) — six namespaced
  shortcuts, one per operating mode. See the next section.

A first-run prompt that exercises the skill end-to-end:

```text
Use $work-queue to read WORK_QUEUE.md, validate it, and start draining
Ready items until the queue is empty or blocked.
```

### Per-mode slash commands (plugin install)

The plugin ships one command per documented operating mode. Each
accepts arguments where it makes sense.

| Command | What it does | Arguments |
|---|---|---|
| `/work-queue:intake` | Capture raw work items into the queue without starting implementation. | Optional inline items. With no args, asks the user. |
| `/work-queue:expand` | Decompose a PRD, design doc, or long issue body into many Ready items in one pass. | The source document as the argument. |
| `/work-queue:refine` | Raise Needs refinement / Inbox items to the Ready bar. | Optional item id (e.g. `WQ-007`); omit to refine the whole queue. |
| `/work-queue:drain` | Continuously execute Ready items until the queue is empty, blocked, or a limit is reached. | Optional integer item-count limit. |
| `/work-queue:audit` | Read-only validation of structure, readiness, dependency resolution, Done hygiene. Never modifies the file. | Optional queue path; defaults to `WORK_QUEUE.md`. |
| `/work-queue:retire` | Delete Done and Cancelled items whose `**Outcome**` names a durable record. Confirms before deleting. | Pass `--yes` to skip the confirmation prompt. |

These commands are not available with the bare-skill install — they
ship in the plugin's `commands/` directory. Bare-skill users can
trigger the same behavior via the `$work-queue` mention prefix and
naming the mode in plain language (`$work-queue, intake the following…`).

The skill itself is the `work-queue/` directory. The root of this
repository is packaging, CI, and documentation for publishing.

## Codex Interface Descriptor

The skill ships `work-queue/agents/openai.yaml` for Codex CLI's
display and discovery layer. Schema reference:
[developers.openai.com/codex/skills](https://developers.openai.com/codex/skills).
The top-level `interface` key and the three nested fields
(`display_name`, `short_description`, `default_prompt`) are required;
`policy` and `dependencies` are optional. The bundled
`scripts/validate_skill.py` smoke-checks that the required keys are
present.

## When to Use This Skill

This skill is for **persistent, cross-session, human-editable** work
tracking that lives in a repo file under version control.

Use it when:

- you want a queue that survives `clear`, new sessions, and machine
  changes,
- you want humans to read, edit, and review the queue alongside code
  (in PRs, code review, CI),
- you want the agent to drain Ready items autonomously over many turns.

Use the host agent's in-session task tracker (Claude Code's TodoWrite,
Codex's task list, etc.) when:

- the work belongs to the current session and does not need to survive
  it,
- the tasks are agent-private scratchpad notes, not deliverables a
  reviewer would want,
- you want the host UI to render checkboxes inline as the agent works.

The two are complementary: keep durable work here; use the host's
in-session tracker for the per-turn execution log.

## Queue File

The default queue file is `WORK_QUEUE.md`. A starter template lives at:

```text
work-queue/templates/WORK_QUEUE.md
```

## Validators

Two stdlib-only validators ship with the skill.

### `validate_queue.py`

Checks a queue file (or a list of them) against the format rules in
[work-queue/references/queue-format.md](work-queue/references/queue-format.md).

```bash
python3 work-queue/scripts/validate_queue.py WORK_QUEUE.md
python3 work-queue/scripts/validate_queue.py --strict-sections queues/*.md
python3 work-queue/scripts/validate_queue.py --strict WORK_QUEUE.md
python3 work-queue/scripts/validate_queue.py --fix WORK_QUEUE.md
python3 work-queue/scripts/validate_queue.py --json WORK_QUEUE.md | jq .
```

Flags:

| Flag | Effect |
|---|---|
| `--allow-done` | Suppress the "Done items should be retired" warning. |
| `--strict-sections` | Require the canonical section set and ordering. |
| `--strict` | Promote opinionated warnings (multiple In progress, missing Verification on Done) to errors. Implies `--strict-sections`. |
| `--fix` | Canonicalize section order, sort Ready by priority/date/id, and trim whitespace. Rewrites in place. |
| `--fix --check` | Exit non-zero if `--fix` would change the file; do not write. |
| `--json` | Emit one JSON document on stdout instead of human-readable lines. |
| `--max-inbox-size N` | Warn when Inbox holds more than `N` items (default 25, 0 disables). |
| `--max-inbox-age-days D` | Warn when an Inbox item is older than `D` days (default 30, 0 disables). |
| `--migrate-to-split` | One-way migration from single-file layout to split (index + `items/`) layout. Refuses to overwrite an existing `items/` directory. |

Exit codes:

| Code | Meaning |
|---|---|
| `0` | All files valid (warnings allowed). |
| `1` | At least one file has an error. |
| `2` | Input file not found. |

Recommended CI invocation:

```bash
python3 work-queue/scripts/validate_queue.py --strict WORK_QUEUE.md
```

### `validate_skill.py`

Smoke-checks the packaged skill itself: SKILL.md frontmatter, that
internal markdown links resolve, that Python script references
resolve, and that `agents/openai.yaml` contains the expected keys.

```bash
python3 scripts/validate_skill.py work-queue
```

Exits `0` when the skill is well-formed, `1` otherwise.

## Releases

Versioned per [Semantic Versioning](https://semver.org). The full
release history lives in [CHANGELOG.md](CHANGELOG.md).

## Repository Status

This repo is structured so the root is publishable, while the actual skill lives in `work-queue/`.

Released under the MIT License.
