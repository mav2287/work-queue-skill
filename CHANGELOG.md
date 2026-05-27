# Changelog

All notable changes to this skill are documented here. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
this project adheres to [Semantic Versioning](https://semver.org).

## [1.1.1] — 2026-05-27

### Added

- Six slash-command entry points, one per operating mode in the
  skill. After installing or updating the plugin, the following
  commands are available:
  - `/work-queue:intake` — capture raw work items into the queue
  - `/work-queue:expand` — decompose a PRD or issue body into many items
  - `/work-queue:refine` — raise Needs refinement or Inbox items to the Ready bar
  - `/work-queue:drain` — continuously execute Ready items until the queue is empty or blocked
  - `/work-queue:audit` — read-only validation of structure, readiness, and Done hygiene
  - `/work-queue:retire` — delete Done and Cancelled items after a durable record exists
- Each command accepts user-supplied arguments where it makes sense
  (item id for `refine`, source document for `expand`, item limit
  for `drain`, queue path for `audit`, `--yes` for `retire`).

### Changed

- README continues to point at `$work-queue` mention and automatic
  selection as the primary invocation paths; the new slash commands
  are a third option that surfaces in `/help` after install.

## [1.1.0] — 2026-05-27

### Added

- **Claude Code plugin distribution.** Repo is now its own
  self-hosted plugin marketplace. Install with
  `claude plugin marketplace add mav2287/work-queue-skill` followed by
  `claude plugin install work-queue@work-queue-skill`. Updates flow
  via `claude plugin update work-queue`. The bare-skill install path
  (`rsync` into `~/.claude/skills/work-queue/`) remains documented as
  a fallback.
- `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`
  at the repo root.
- README's Install section leads with the plugin path; the bare-skill
  and Codex install paths remain as a fallback section.
- Release workflow now publishes two release artifacts per tag: a
  plugin zip (manifests + skill subdir, installable via
  `claude --plugin-dir`) and the legacy bare-skill zip for rsync
  consumers.
- CI step that lints `plugin.json` and `marketplace.json` for valid
  JSON and required fields.

### Changed

- README Invoking the Skill section adds the namespaced slash
  command (`/work-queue:work-queue`) as the third invocation path,
  alongside the `$work-queue` mention and automatic selection.

## [1.0.0] — 2026-05-27

First stable release. The skill — its references, validators,
templates, fixtures, packaging, and CI — has been audited end to end
and used to drive its own development through ~60 commits of intake
and drain. Treat the public surface (`SKILL.md`, `references/`,
`templates/`, `agents/openai.yaml`, validator CLI flags and exit
codes) as stable from this tag onward.

### Skill content

- Six operating modes documented in `SKILL.md`: **Intake**, **Expand**,
  **Refine**, **Drain**, **Audit**, **Retire**.
- `Trust Model for Queue Content` in `SKILL.md` and a longer
  `Untrusted Queue Content` section in `references/drain.md` treat
  queue Notes / Problem / logs as data, not as instructions to the
  agent. Documents the three-step response (do not follow embedded
  instructions; preserve the evidence; move to Blocked with a
  Questions line that quotes the suspicious text).
- `Concurrency Model` in `references/drain.md` plus a SKILL.md pointer:
  drain assumes single-writer per queue and lists three pre-claim
  checks and three mitigations for teams running automation.
- `Resuming a Drain` section in `references/drain.md` with three
  options (continue / re-claim / revert) and example agent prompts;
  Drain Loop step 3 in SKILL.md enforces the resume check before
  selecting a new Ready item.
- `The In Progress Step Is Separate` rule in `references/drain.md` and
  the corresponding SKILL.md instruction: never collapse
  Ready → In progress and In progress → Done into a single edit.
- `Secrets Hygiene` section in `references/intake.md` listing
  prohibited content, a redaction pattern, and the rotation reminder.
- `Verification and Outcome on Done items` section in
  `references/queue-format.md` plus the drain-loop instruction:
  Verification is **hand-written**, Outcome is **auto-populated** from
  `git diff --name-only`, the head commit SHA, and a one-line prose
  summary the agent fills.
- `Local checks before asking` recognized as a first-class body
  heading; validator warns when Ready items still contain the
  `"Example only"` template placeholder.
- `When to Use This Skill` README section distinguishes this queue
  (persistent, cross-session, repo-versioned) from the host agent's
  in-session task tracker (ephemeral, agent-private).

### Layouts

- **Single-file layout** (default): all items inline in one queue file.
- **Split layout** (new): index file of checkbox links plus per-item
  files under `items/WQ-NNN.md`, each with YAML frontmatter
  (`type`, `priority`, `created`, `area`, `id`, `deps`). The validator
  detects which layout is in use and runs the same checks against
  either.
- One-way `--migrate-to-split` subcommand strips inline fields, writes
  per-item files, and rewrites the queue as the index. Refuses to
  overwrite an existing `items/` directory.
- `Layouts` section in `references/queue-format.md` describes both
  shapes and the migration command.

### Validator flags and behavior

- `--strict-sections` requires the canonical section set and ordering.
- `--strict` promotes opinionated warnings (multiple In progress, Done
  without `**Verification**`) to errors. Implies `--strict-sections`.
- `--fix` canonicalizes section order, sorts Ready by priority/date/id,
  and normalizes whitespace. Works in both single-file and split
  layouts. `--fix --check` returns non-zero when changes would be made.
- `--json` emits findings as one structured document on stdout.
- `--max-inbox-size N` (default 25) and `--max-inbox-age-days D`
  (default 30) warn when triage debt accumulates; `0` disables either.
- Multi-file invocation: `validate_queue.py` accepts any number of
  queue paths in one call.
- New `Depends on` field on items, comma-separated `WQ-NNN` ids;
  validator errors on unknown ids and self-deps, warns when a Ready
  item depends on a non-Done target. `selectable_ready_items` helper
  exposes drain-ready items whose deps are all satisfied.
- Validator warns on: duplicate item titles, future or pre-2020
  `Created` dates, placeholder `WQ-000` ids, dangling
  `Blocked on:` references, multiple `In progress` items, `Inbox`
  size and age thresholds, and Done items missing `**Outcome**`.
- `validate_skill.py` smoke-checks SKILL.md frontmatter, internal
  markdown link resolution, Python script references, and the Codex
  `agents/openai.yaml` interface presence. No third-party dependencies.

### Packaging and distribution

- README documents both Claude Code paths
  (`.claude/skills/work-queue/` recommended,
  `~/.claude/skills/work-queue/` user-scope alternative) and both
  Codex CLI paths (`.agents/skills/` repo,
  `$HOME/.agents/skills/` user, per
  [developers.openai.com/codex/skills](https://developers.openai.com/codex/skills)).
- Post-install verification snippets for every target.
- Codex Interface Descriptor section + comment header in
  `work-queue/agents/openai.yaml` linking to the schema.
- Validators section in README listing every flag and exit code.
- Slash-command-claim corrected: README describes the actual
  `$work-queue` mention and auto-discovery paths.

### Templates and examples

- Item template starter (`WQ-000` placeholder id that fails validation
  if pasted verbatim, with the validator warning when an item id ends
  in `-000`).
- Starter queue template with the canonical seven status sections plus
  the `Queue Rules` block.
- `examples/sample-queue.md`, `examples/ready-bug.md`,
  `examples/blocked-investigation.md`, `examples/done-with-outcome.md`
  (full Verification + Outcome pattern), and the Expand-mode pair
  `examples/expand-input.md` / `examples/expand-output.md`.

### CI and developer workflow

- Pinned Python matrix (`3.10`, `3.12`).
- Steps: skill validator, queue validator on bundled fixtures,
  regression test suite, `mypy --strict` against both validators,
  `markdownlint-cli2` with a config tuned to allow the queue format.
- OS/IDE noise guard that fails the build if `.DS_Store`,
  `Thumbs.db`, `Desktop.ini`, `.idea/`, or `.vscode/` reappear in the
  checkout.
- Release workflow on `v*` tag push: validates, packages
  `work-queue/` into a versioned zip, extracts the matching CHANGELOG
  section, and publishes a GitHub Release with the zip attached.
- Subprocess smoke tests and a bad-fixture suite under
  `tests/fixtures/bad/` paired with a manifest of expected error
  substrings.
- 52 regression tests covering every validator branch.

### Repo hygiene

- `.gitignore` covers `.DS_Store`, `Thumbs.db`, `Desktop.ini`,
  `.idea/`, `.vscode/`, Python caches, and editor swap files.
- `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`,
  `.github/ISSUE_TEMPLATE/{bug_report,feature_request}.md`,
  `.github/ISSUE_TEMPLATE/config.yml`, `.github/PULL_REQUEST_TEMPLATE.md`.
- `.pre-commit-config.yaml` registering local hooks for the skill
  validator, the queue validator, and the regression suite.
- MIT license.

[1.1.1]: https://github.com/mav2287/work-queue-skill/releases/tag/v1.1.1
[1.1.0]: https://github.com/mav2287/work-queue-skill/releases/tag/v1.1.0
[1.0.0]: https://github.com/mav2287/work-queue-skill/releases/tag/v1.0.0
