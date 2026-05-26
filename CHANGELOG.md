# Changelog

All notable changes to this skill are documented here. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
this project adheres to [Semantic Versioning](https://semver.org).

## [Unreleased]

### Added

- `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, GitHub
  issue/PR templates.
- `.pre-commit-config.yaml` registering local hooks for the skill
  validator, the queue validator, and the regression suite.
- `Codex Interface Descriptor` section in the README plus a comment
  header in `work-queue/agents/openai.yaml` linking to the schema.

## [0.1.0] — 2026-05-26

Initial public release. Cuts a milestone after a full production-readiness
pass against the skill, its validators, packaging, and docs.

### Added

- `--strict` flag that promotes opinionated warnings to errors (multiple In
  progress items, Done without `**Verification**`). Implies
  `--strict-sections`.
- `--fix` mode that canonicalizes section order, sorts Ready by priority/
  date/id, and normalizes whitespace. `--fix --check` returns non-zero
  when changes would be made.
- `--json` mode that emits findings as one structured document on stdout.
- Multi-file invocation: `validate_queue.py` accepts any number of paths.
- `--max-inbox-size` and `--max-inbox-age-days` flags that warn on
  triage debt.
- Validator now warns on duplicate item titles, future or pre-2020
  `Created` dates, placeholder `WQ-000` ids, dangling `Blocked on:
  WQ-NNN` references, and `Example only` placeholder text left in Ready.
- `**Outcome**` body subsection convention for Done items; validator
  warns when it is missing.
- `Local checks before asking` recognized as a first-class body heading.
- Example fixture `work-queue/examples/done-with-outcome.md` showing the
  full Done pattern (Verification + Outcome).
- Bad-fixture suite under `tests/fixtures/bad/` plus a subprocess smoke
  test that runs the real CLI.
- `Trust Model for Queue Content` section in SKILL.md and
  `Untrusted Queue Content` in `references/drain.md` covering
  prompt-injection from queue items.
- `Concurrency Model` section in `references/drain.md`.
- `Secrets Hygiene` section in `references/intake.md`.
- `Known Limits and Scaling Path` section in `references/queue-format.md`
  naming the ~50 active items comfort ceiling and the hybrid layout
  evolution.
- `Verification and Outcome on Done items` and `Created Date Sanity`
  sections in `references/queue-format.md`.
- `When to Use This Skill` README section distinguishing this queue from
  the host agent's in-session task tracker.
- Validators section in README listing every flag and exit code.
- CI step that fails the build when OS or IDE metadata reappears in the
  checkout.

### Changed

- README now documents the OpenAI-documented Codex install paths
  (`.agents/skills` and `$HOME/.agents/skills`) and keeps a back-compat
  note for `~/.codex/skills/`.
- README replaces the false `/work-queue` slash-command claim with an
  `Invoking the Skill` section describing the real `$work-queue` and
  auto-discovery paths.
- Item template id is now `WQ-000` (parses, fails on placeholder title)
  and the validator warns on the placeholder id.
- `validate_openai_yaml` renamed to `check_openai_yaml_presence` with a
  docstring spelling out the no-deps trade-off (back-compat alias
  retained).
- `validate_queue.validate` and `collect` accept the new flags as keyword
  arguments.

### Fixed

- `.gitignore` covers `.DS_Store`, `Thumbs.db`, `Desktop.ini`, `.idea/`,
  `.vscode/`, and common Python caches.

[0.1.0]: https://github.com/replace-me/replace-me/releases/tag/v0.1.0
