# Work Queue

Single source of truth for active work the agent can intake, refine, execute, verify, and retire.

## Queue Rules

- Status is the section the item lives in. Move the whole item; do not duplicate it.
- `Ready` means an agent can execute the item end to end without returning to the requester for basic scope.
- `Done` and `Cancelled` are transient. Delete them after a durable record exists.
- Default priority order: `P0`, `P1`, `P2`, `P3`.
- Default type values: `bug`, `feature`, `chore`, `docs`, `refactor`, `investigation`.

## In progress

_None._

## Blocked

_None._

## Ready

### WQ-002 Correct or implement the `/work-queue` slash-command claim

- **Type**: bug
- **Priority**: P0
- **Created**: 2026-05-26
- **Area**: docs

**Problem / Want**
`README.md` tells users they can invoke the skill with `/work-queue`, but no `commands/work-queue.md` ships in the package. Claude Code skills are invoked via the `Skill` tool or the `$work-queue` prefix, not as a slash command unless one is registered. Users will type `/work-queue`, see nothing, and assume the skill is broken.

**Acceptance**
- [ ] Either ship a real slash command under `work-queue/commands/` that triggers the skill, or update the README to remove the `/work-queue` claim and describe the actual invocation paths (`$work-queue` mention, automatic skill discovery).
- [ ] README documents the supported invocation paths for Claude Code and Codex separately.
- [ ] If a slash command is added, a smoke test or manual verification step confirms it loads.

**Notes**
README claim is at `README.md:39-43`. Skill is auto-discovered via SKILL.md frontmatter; slash commands are a separate file/directory convention.

### WQ-003 Fix template item ID so it parses

- **Type**: bug
- **Priority**: P0
- **Created**: 2026-05-26
- **Area**: templates

**Problem / Want**
`work-queue/templates/item.md` starts with `### WQ-XXX`. `ITEM_RE` in the validator requires `\d{3,}` after the dash, so `XXX` is silently ignored — the validator finds zero items and emits no error specific to the template placeholder. A user who copies the template verbatim believes the queue is valid.

**Acceptance**
- [ ] Template uses an ID that parses (for example `WQ-000`) so the validator reports the placeholder title instead of silently dropping the item.
- [ ] Alternatively, the validator emits a dedicated warning when it sees an obvious placeholder ID such as `WQ-XXX` outside a fenced block.
- [ ] A regression test covers the chosen behavior.

**Notes**
`ITEM_RE` lives at `work-queue/scripts/validate_queue.py:37`. Template at `work-queue/templates/item.md:1`.

### WQ-004 Verify and document Codex skill installation

- **Type**: investigation
- **Priority**: P0
- **Created**: 2026-05-26
- **Area**: packaging

**Problem / Want**
The README tells Codex users to rsync the skill into `${CODEX_HOME:-$HOME/.codex}/skills/work-queue/`. This path and the `agents/openai.yaml` interface schema have not been verified against current Codex CLI documentation. If either is wrong, the README's second-largest promise ("works with Codex") is broken.

**Acceptance**
- [ ] Cross-check the Codex CLI documented skill-loader path and schema for the current Codex release.
- [ ] Confirm `agents/openai.yaml` matches the documented interface (or update it).
- [ ] Update README install instructions to match verified behavior, including any version constraint.
- [ ] Record evidence (link to Codex doc or release notes) in Notes before closing.

**Notes**
Files touched: `README.md:30-35`, `work-queue/agents/openai.yaml`, `scripts/validate_skill.py:61-82`.

### WQ-005 Enforce single In progress item by default

- **Type**: feature
- **Priority**: P1
- **Created**: 2026-05-26
- **Area**: validator

**Problem / Want**
`references/queue-format.md` says "Prefer one item at a time unless the user explicitly asks for parallel execution," but the validator never checks the In progress count. Drain loops can drift into multi-claim states without any signal.

**Acceptance**
- [ ] Validator warns when In progress has more than one item.
- [ ] `--strict` (or equivalent flag) promotes the warning to an error.
- [ ] Regression test covers both single-item and multi-item In progress states.

**Notes**
Reference: `work-queue/references/queue-format.md:81`.

### WQ-006 Validate `Blocked on: WQ-NNN` references resolve

- **Type**: feature
- **Priority**: P1
- **Created**: 2026-05-26
- **Area**: validator

**Problem / Want**
Items can reference other items by ID in a `Blocked on` line, but the validator never confirms the target exists. Dangling references rot silently as items get retired.

**Acceptance**
- [ ] Validator parses `Blocked on:` lines for `WQ-NNN`-style references.
- [ ] Validator errors when a referenced ID does not exist in the same queue file.
- [ ] Validator warns when a Blocked item references an item that is itself Done or Cancelled.
- [ ] Regression tests cover resolved, dangling, and retired-target references.

**Notes**
`BLOCKED_MARKER_RE` at `work-queue/scripts/validate_queue.py:42` already locates the line.

### WQ-007 Warn on duplicate item titles

- **Type**: feature
- **Priority**: P1
- **Created**: 2026-05-26
- **Area**: validator

**Problem / Want**
Duplicate IDs are caught, but duplicate titles are not. Two reports of the same bug landing in Inbox is the most common duplicate symptom and the validator should flag it.

**Acceptance**
- [ ] Validator emits a warning when two items share a normalized title (case-insensitive, whitespace-collapsed).
- [ ] Warning includes both IDs and line numbers.
- [ ] Regression test covers the duplicate-title case.

**Notes**
Normalization should be conservative to avoid false positives on common verbs like "Fix login".

### WQ-008 Range-check Created dates

- **Type**: feature
- **Priority**: P1
- **Created**: 2026-05-26
- **Area**: validator

**Problem / Want**
`Created` is validated for ISO-8601 format but not for plausibility. Future dates and pre-2020 dates almost always indicate a typo, and there is no signal to the agent that something is wrong.

**Acceptance**
- [ ] Validator warns when Created is in the future relative to the system clock.
- [ ] Validator warns when Created is earlier than a documented sanity threshold (for example 2020-01-01).
- [ ] Threshold and behavior are documented in `references/queue-format.md`.
- [ ] Regression tests cover future, ancient, and in-range dates.

**Notes**
`validate_date` at `work-queue/scripts/validate_queue.py:154`.

### WQ-009 Promote `Done` without Verification heading to a strict-mode error

- **Type**: feature
- **Priority**: P1
- **Created**: 2026-05-26
- **Area**: validator

**Problem / Want**
The validator only warns when a Done item is missing a `**Verification**` heading. The skill's whole reason for existing is to prevent "Done" without verification, so this should be an error under `--strict-sections` or a new `--strict` mode.

**Acceptance**
- [ ] Done items missing a `**Verification**` heading produce an error when strict mode is enabled.
- [ ] Default behavior remains a warning so existing queues are not broken.
- [ ] Regression tests cover strict and non-strict behavior.

**Notes**
Current check at `work-queue/scripts/validate_queue.py:229`.

### WQ-010 Decide how to validate `agents/openai.yaml` properly

- **Type**: investigation
- **Priority**: P1
- **Created**: 2026-05-26
- **Area**: validator

**Problem / Want**
`validate_openai_yaml` matches anchored substrings for required keys. Real YAML errors (bad nesting, duplicate keys, wrong types) still pass. A real parse would require adding PyYAML, which breaks the explicit no-third-party-deps stance in `scripts/validate_skill.py`. The trade-off is unresolved.

**Acceptance**
- [ ] Decision recorded: parse with PyYAML (and accept the dependency), or rename the function and docstring to reflect that it is a presence check.
- [ ] If renamed, README and CI step descriptions updated to match.
- [ ] If parsed, the dependency is pinned and the existing no-deps comment removed or revised.

**Notes**
Current implementation at `scripts/validate_skill.py:61-82`.

### WQ-011 Accept multiple files or glob in the queue validator

- **Type**: feature
- **Priority**: P1
- **Created**: 2026-05-26
- **Area**: validator

**Problem / Want**
`validate_queue.py` takes exactly one positional argument. Repos with multiple queues (per-area, per-team) cannot lint them in one CI step without a shell loop.

**Acceptance**
- [ ] Validator accepts one or more queue file paths.
- [ ] Validator accepts a `--glob` pattern or treats shell-expanded globs naturally.
- [ ] Exit code is non-zero if any file fails; per-file summaries are printed.
- [ ] Regression tests cover multi-file pass and mixed pass/fail invocations.

**Notes**
Argparse setup at `work-queue/scripts/validate_queue.py:355-368`.

### WQ-012 Add a `--fix` mode for safe canonicalization

- **Type**: feature
- **Priority**: P1
- **Created**: 2026-05-26
- **Area**: validator

**Problem / Want**
The validator is read-only. Reordering Ready by priority/age, normalizing section order, and collapsing whitespace are all mechanical and safe — agents and humans both end up doing them by hand.

**Acceptance**
- [ ] `--fix` reorders Ready items per documented priority rule, reorders status sections to canonical order, and normalizes trailing whitespace.
- [ ] `--fix` never changes item body content beyond whitespace.
- [ ] `--fix` writes in place and prints a diff summary; `--fix --check` returns non-zero when changes would be made.
- [ ] Regression tests cover both the rewriting and the no-op cases.

**Notes**
Sort order already implemented in `validate_ready_order` at `work-queue/scripts/validate_queue.py:288`.

### WQ-013 Add `--json` output for editor and agent integration

- **Type**: feature
- **Priority**: P1
- **Created**: 2026-05-26
- **Area**: validator

**Problem / Want**
Agents and editors that consume validator output today must parse `WARN:` / `ERROR:` text lines. A structured output makes integration robust.

**Acceptance**
- [ ] `--json` prints a single JSON document with errors and warnings, each carrying file, line, item id, severity, and message fields.
- [ ] Human output remains the default.
- [ ] Regression test asserts the JSON schema is stable.

**Notes**
Use only stdlib `json`.

### WQ-014 Document validator exit codes and CLI surface

- **Type**: docs
- **Priority**: P1
- **Created**: 2026-05-26
- **Area**: docs

**Problem / Want**
Exit code 2 (file not found) is undocumented. The README mentions the validator but does not describe flags, exit codes, or recommended CI usage.

**Acceptance**
- [ ] README has a Validator section listing every flag, exit code, and an example CI invocation.
- [ ] `--help` output matches the documented surface.
- [ ] Skill `SKILL.md` Validation section links to the README rather than duplicating it.

**Notes**
Current docs are scattered between `README.md:55-65` and `SKILL.md:84-92`.

### WQ-015 Expand unit-test coverage for `validate_queue.py`

- **Type**: chore
- **Priority**: P1
- **Created**: 2026-05-26
- **Area**: tests

**Problem / Want**
Existing tests exercise only fence handling, acceptance terminator, priority sort, and section strictness. Most of the validator's error and warning branches are uncovered.

**Acceptance**
- [ ] Tests cover: duplicate ID, missing Type/Priority/Created/Area, invalid Type, invalid Priority, malformed Created, Blocked without `Blocked on`/`Questions`, Done with unchecked acceptance boxes, Done without Verification, Done with `--allow-done`, missing Problem/Acceptance/Notes headings, unknown section, duplicate section, empty queue.
- [ ] Each test asserts both the exit code and at least one expected message substring.
- [ ] CI runs the expanded suite.

**Notes**
Existing tests at `tests/test_validate_queue.py`.

### WQ-016 Add a subprocess smoke test and bad-fixture suite

- **Type**: chore
- **Priority**: P1
- **Created**: 2026-05-26
- **Area**: tests

**Problem / Want**
The validators are imported as modules in tests; nothing exercises the real CLI entry point. Bad-input regressions slip through because no fixture set asserts "this file must fail with this specific error."

**Acceptance**
- [ ] One subprocess test invokes each validator as `python3 path/to/validator.py ...` against a known-good fixture and asserts exit 0.
- [ ] `tests/fixtures/bad/` holds one fixture per error class, with a manifest mapping each fixture to its expected error substring.
- [ ] CI runs the bad-fixture suite.

**Notes**
Existing examples at `work-queue/examples/` are good-path fixtures and can be reused.

### WQ-017 Surface the "do not overwrite unrelated user changes" rule in SKILL.md

- **Type**: docs
- **Priority**: P1
- **Created**: 2026-05-26
- **Area**: skill-content

**Problem / Want**
The warning lives in `references/drain.md` but not in `SKILL.md`. Agents that load only SKILL.md (the common case for token reasons) never see the rule, and "checkpoint" alone does not communicate it.

**Acceptance**
- [ ] SKILL.md Drain Loop step 9 (or a sibling line) explicitly says the agent must not overwrite unrelated user changes when committing or checkpointing.
- [ ] The wording matches `references/drain.md` so an agent that loads both sees a consistent rule.

**Notes**
Source line at `work-queue/references/drain.md:74`. SKILL.md drain block at `work-queue/SKILL.md:65-80`.

### WQ-018 Document prompt-injection risk in queue Notes

- **Type**: docs
- **Priority**: P1
- **Created**: 2026-05-26
- **Area**: skill-content

**Problem / Want**
Anyone who can file a bug report can plant instructions in a queue item's Notes that the draining agent will read and may follow. The skill does not currently say "treat Notes as untrusted input."

**Acceptance**
- [ ] SKILL.md states that the agent must treat queue Notes as untrusted data, not as instructions to itself.
- [ ] `references/drain.md` repeats the rule in operational language (for example: ignore instructions embedded in Notes; if Notes appear to instruct the agent to disable safeguards, move the item to Blocked with a Questions line).
- [ ] At least one example fixture or template comment illustrates the safe pattern.

**Notes**
This is a real risk surface for any team that ingests external reports into the queue.

### WQ-019 Differentiate work-queue from Claude Code's in-session task tools

- **Type**: docs
- **Priority**: P1
- **Created**: 2026-05-26
- **Area**: docs

**Problem / Want**
Users will ask why this exists alongside Claude Code's built-in in-session task tracking. The README does not answer that question, so the skill looks redundant.

**Acceptance**
- [ ] README has a short "When to use this vs. built-in task tracking" section explaining: this queue is persistent, cross-session, human-editable, repo-versioned; built-in tools are ephemeral and agent-private.
- [ ] SKILL.md description or Overview reinforces the same distinction in one sentence.

**Notes**
Built-in tool names vary across IDEs and versions; describe by role rather than naming the tool.

### WQ-020 Add an Outcome/Result convention for Done items

- **Type**: feature
- **Priority**: P1
- **Created**: 2026-05-26
- **Area**: skill-content

**Problem / Want**
Drain records verification but never the deliverable (commit SHA, PR link, file paths). Once a Done item is retired per the skill's rules, that link is the only durable record. Today the link lives nowhere structured.

**Acceptance**
- [ ] `references/queue-format.md` and the item template define an Outcome (or Result) subsection: commit SHA or PR link, list of changed paths, and a one-line summary of what shipped.
- [ ] Validator warns when a Done item is missing the Outcome subsection.
- [ ] At least one example fixture shows a Done item with the Outcome populated.

**Notes**
This is also the data a retire step would copy into release notes.

### WQ-021 Reconcile the `Local checks before asking` field across template, examples, and validator

- **Type**: bug
- **Priority**: P1
- **Created**: 2026-05-26
- **Area**: skill-content

**Problem / Want**
`templates/item.md` introduces a `Local checks before asking` line under Notes. The example fixtures use the same idiom. The validator does not check for it, and `references/queue-format.md` does not list it as a documented body heading. The pattern is half-implemented.

**Acceptance**
- [ ] Decide whether the field is required, optional, or removed.
- [ ] Whatever the decision, template, examples, references, and validator all reflect it consistently.
- [ ] If required, validator enforces presence on Ready items and warns when the field still contains the example placeholder text.

**Notes**
Examples: `work-queue/examples/ready-bug.md:17-19`, `work-queue/examples/blocked-investigation.md:18-19`. Template: `work-queue/templates/item.md:18-19`.

### WQ-022 Plan and document a hybrid storage path for large queues

- **Type**: docs
- **Priority**: P2
- **Created**: 2026-05-26
- **Area**: skill-content

**Problem / Want**
The single-file design is unwieldy past a few dozen items and conflicts on every merge. Competing tools (Backlog.md, Spec Kit) all converged on an index file plus one file per item. The skill should at minimum document the scaling limit and the planned evolution so adopters can decide.

**Acceptance**
- [ ] References include a known-limits section that names the single-file scaling ceiling and the recommended workaround for now.
- [ ] A short design note (in references or a new design doc) sketches the hybrid index-plus-per-item layout so the item schema can be planned for it.
- [ ] No code change required for this item; implementation is a separate future item.

**Notes**
Hybrid pattern: `WORK_QUEUE.md` index using `- [ ]` syntax, per-item details under `work-queue/items/WQ-NNN.md` with YAML frontmatter.

### WQ-023 Document the drain concurrency model

- **Type**: docs
- **Priority**: P2
- **Created**: 2026-05-26
- **Area**: skill-content

**Problem / Want**
Nothing in the skill addresses what happens when two agent sessions drain the same queue at once. The likely outcomes (double-claim, conflicting commits, merge conflicts) are predictable and avoidable.

**Acceptance**
- [ ] `references/drain.md` states the assumed concurrency model (single writer per queue).
- [ ] Recommended mitigations are documented: lock file, branch per drain session, or refusing to start drain if In progress already holds an item the current session did not claim.
- [ ] SKILL.md links to the section.

**Notes**
A heavier "advisory file lock" feature can be its own item later.

### WQ-024 Warn against pasting secrets into queue Notes

- **Type**: docs
- **Priority**: P2
- **Created**: 2026-05-26
- **Area**: skill-content

**Problem / Want**
Drain encourages pasting log output and repro commands into Notes. Tokens, cookies, and connection strings end up in a committed file. There is no warning today.

**Acceptance**
- [ ] `references/intake.md` warns against pasting credentials, tokens, cookies, or connection strings into Notes and links to a recommended redaction pattern.
- [ ] Item template Notes section repeats the warning briefly.
- [ ] Optional follow-up item filed for a validator pre-commit check.

**Notes**
A real secret scan is out of scope; documentation is the v1 deliverable.

### WQ-025 Validator warning for Inbox growth and staleness

- **Type**: feature
- **Priority**: P2
- **Created**: 2026-05-26
- **Area**: validator

**Problem / Want**
An unbounded Inbox is the queue's failure mode. There is no signal when triage debt accumulates.

**Acceptance**
- [ ] Validator warns when Inbox holds more than a configurable threshold (default 25).
- [ ] Validator warns when any Inbox item has a Created date older than a configurable threshold (default 30 days).
- [ ] Thresholds are flags on the validator and are documented in the README.
- [ ] Regression tests cover under/over the threshold.

**Notes**
Same mechanism can later cover stale Blocked items.

### WQ-026 Cut a v0.1.0 release with CHANGELOG and a git tag

- **Type**: chore
- **Priority**: P2
- **Created**: 2026-05-26
- **Area**: release

**Problem / Want**
The repo has no version, no CHANGELOG, and no tags. Adopters cannot pin to a release, and there is no record of what changed between snapshots.

**Acceptance**
- [ ] `CHANGELOG.md` exists, follows Keep-a-Changelog format, and covers the work landed up to the tagged commit.
- [ ] A `v0.1.0` annotated tag is pushed.
- [ ] README links to the changelog.

**Notes**
The skill metadata does not currently carry a version field; if the spec allows one, add it here.

### WQ-027 Add release CI on tag push

- **Type**: feature
- **Priority**: P2
- **Created**: 2026-05-26
- **Area**: ci

**Problem / Want**
There is no automation for cutting a release artifact (a zip of the `work-queue/` directory plus CHANGELOG entry). All release work today would be manual.

**Acceptance**
- [ ] GitHub Actions workflow triggers on tags matching `v*`.
- [ ] Workflow validates the skill, packages `work-queue/` into a release zip, and attaches it to the GitHub Release.
- [ ] Workflow extracts the matching CHANGELOG section as the release body.

**Notes**
Depends on WQ-026 for the changelog format.

### WQ-028 Add CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, and issue/PR templates

- **Type**: docs
- **Priority**: P2
- **Created**: 2026-05-26
- **Area**: packaging

**Problem / Want**
Standard OSS hygiene files are missing. Contributors do not know how to file a bug, propose a change, or report a vulnerability.

**Acceptance**
- [ ] `CONTRIBUTING.md` documents the dev loop: install Python, run validators, run tests, expected style.
- [ ] `SECURITY.md` documents how to report vulnerabilities.
- [ ] `CODE_OF_CONDUCT.md` (Contributor Covenant or equivalent) added.
- [ ] `.github/ISSUE_TEMPLATE/` and `.github/PULL_REQUEST_TEMPLATE.md` added with sensible defaults.

**Notes**
Templates should reference the work-queue itself as the canonical place for actionable issues, once that is set up for this repo.

### WQ-029 Document the source schema for `agents/openai.yaml`

- **Type**: docs
- **Priority**: P2
- **Created**: 2026-05-26
- **Area**: docs

**Problem / Want**
The Codex interface file ships with no link to the spec it implements. Anyone editing it has to guess what fields exist and what they mean.

**Acceptance**
- [ ] `agents/openai.yaml` carries a top-of-file comment linking to the canonical schema doc for the Codex release it targets.
- [ ] README or a new `docs/codex.md` documents the same.

**Notes**
Resolve as part of, or after, WQ-004.

### WQ-030 Add a pre-commit hook running both validators on examples and templates

- **Type**: feature
- **Priority**: P2
- **Created**: 2026-05-26
- **Area**: ci

**Problem / Want**
The most common regression is a docs edit that breaks the bundled examples or the starter template. CI catches it eventually; a pre-commit hook catches it before push.

**Acceptance**
- [ ] `.pre-commit-config.yaml` runs `validate_skill.py` against `work-queue/` and `validate_queue.py` against every fixture under `work-queue/examples/` and `work-queue/templates/`.
- [ ] CONTRIBUTING (WQ-028) documents how to install it.

**Notes**
Use the `local` pre-commit hook type to avoid pulling external repos.

### WQ-031 Add a verification step to README install instructions

- **Type**: docs
- **Priority**: P2
- **Created**: 2026-05-26
- **Area**: docs

**Problem / Want**
After running the rsync command, the user has no way to confirm the skill is loaded. They will assume failure on the first test prompt that does not auto-invoke the skill.

**Acceptance**
- [ ] README install sections include a verification command for each target (Claude Code user, Claude Code project, Codex) that exits non-zero if the skill is not installed.
- [ ] Verification examples match the actual current CLI behavior.

**Notes**
A simple `ls "$HOME/.claude/skills/work-queue/SKILL.md"` plus a guidance line about invoking the skill is acceptable.

### WQ-032 Recommend user-vs-project install path in README

- **Type**: docs
- **Priority**: P2
- **Created**: 2026-05-26
- **Area**: docs

**Problem / Want**
The README presents three install variants with equal weight. New users do not know which to pick or what the trade-offs are.

**Acceptance**
- [ ] README leads with one recommended install path and a one-line rationale.
- [ ] Other paths are presented as alternatives with the trade-off named (per-repo team adoption vs. per-user convenience).

**Notes**
Recommendation should align with how the skill is most commonly used in practice; the writer of this item is welcome to pick.

### WQ-033 Decide whether to publish to discoverability channels

- **Type**: investigation
- **Priority**: P2
- **Created**: 2026-05-26
- **Area**: release

**Problem / Want**
Competing skills are discovered through `mcpmarket.com`, `awesome-claude-code`, and references in `anthropics/skills`. This skill is unlisted everywhere. The investigation should produce a decision on which channels to target.

**Acceptance**
- [ ] List candidate channels with submission process and audience for each.
- [ ] Record a decision on which channels to submit to and which to skip, with a one-line rationale per choice.
- [ ] File Ready follow-up items for the submissions that are in scope.

**Notes**
Independent of code work; can be done in parallel with anything else.

### WQ-034 Replace the absolute-path placeholder in SKILL.md Validation snippet

- **Type**: docs
- **Priority**: P3
- **Created**: 2026-05-26
- **Area**: skill-content

**Problem / Want**
`SKILL.md` validation snippet reads `python3 /absolute/path/to/installed/work-queue/scripts/validate_queue.py`. This is technically correct but ugly, and agents will copy it literally.

**Acceptance**
- [ ] Snippet shows the two real install paths (`~/.claude/skills/work-queue/...` and `.claude/skills/work-queue/...`) and tells the agent to pick whichever matches the current installation.
- [ ] No literal "/absolute/path/to/..." string remains in SKILL.md.

**Notes**
`work-queue/SKILL.md:86-90`.

### WQ-035 Decide whether to include `## Queue Rules` in the starter template

- **Type**: chore
- **Priority**: P3
- **Created**: 2026-05-26
- **Area**: templates

**Problem / Want**
`templates/WORK_QUEUE.md` omits the `## Queue Rules` section while the validator's `NON_STATUS_SECTIONS` set explicitly accepts it. The bundled `examples/sample-queue.md` also omits it. The half-supported state is confusing.

**Acceptance**
- [ ] Decide: either add `## Queue Rules` to the starter template (and document it as recommended) or remove the `NON_STATUS_SECTIONS` allowance and update references.
- [ ] Template, example, validator, and references all agree.

**Notes**
Validator constant at `work-queue/scripts/validate_queue.py:25`.

### WQ-036 Lift "omit transient queue IDs from durable commit messages" into SKILL.md

- **Type**: docs
- **Priority**: P3
- **Created**: 2026-05-26
- **Area**: skill-content

**Problem / Want**
This is one of the strongest opinions in the skill and is buried at the bottom of `references/drain.md`. Agents that load only SKILL.md never see it.

**Acceptance**
- [ ] SKILL.md Drain Loop or Retention section states the rule in one line and points at `references/drain.md` for the detail.

**Notes**
Source: `work-queue/references/drain.md:80-81`, `:86`.

### WQ-037 Add `mypy --strict` on the validator scripts

- **Type**: chore
- **Priority**: P3
- **Created**: 2026-05-26
- **Area**: ci

**Problem / Want**
The validators are typed by convention but not checked. Adding `mypy --strict` is cheap and catches a real class of bugs in regex-heavy code.

**Acceptance**
- [ ] `mypy --strict scripts/validate_skill.py work-queue/scripts/validate_queue.py` runs in CI and passes.
- [ ] Any new typing dependencies are dev-only.

**Notes**
The current `int | None` annotations already require Python 3.10, which CI uses.

### WQ-038 Add markdownlint to CI

- **Type**: chore
- **Priority**: P3
- **Created**: 2026-05-26
- **Area**: ci

**Problem / Want**
Skill content is all markdown; no linter enforces consistent heading levels, list markers, or trailing whitespace.

**Acceptance**
- [ ] `markdownlint-cli2` (or equivalent) runs in CI against `README.md`, `work-queue/**/*.md`, and `tests/fixtures/**/*.md`.
- [ ] Configuration tuned to skip rules that conflict with queue-format requirements.

**Notes**
Watch for rules that flag the deeply-nested checkbox patterns used in acceptance lists.

### WQ-039 Verify the LICENSE year and copyright

- **Type**: chore
- **Priority**: P3
- **Created**: 2026-05-26
- **Area**: packaging

**Problem / Want**
LICENSE year and holder were not audited. A wrong year is harmless; an unverified copyright line is a small papercut.

**Acceptance**
- [ ] LICENSE shows the correct year (2026 today) and the intended holder name.

**Notes**
File: `LICENSE`.

## Needs refinement

_None._

## Inbox

_None._

## Done

### WQ-001 Stop committing OS and IDE metadata

- **Type**: chore
- **Priority**: P0
- **Created**: 2026-05-26
- **Area**: packaging

**Problem / Want**
`.DS_Store` files exist at repo root and inside `work-queue/`, and `.idea/` is untracked but uncovered by `.gitignore`. A sloppy `git add -A` would commit them, and CI does not fail when they reappear.

**Acceptance**
- [x] Existing `.DS_Store` files removed from the working tree.
- [x] `.gitignore` covers `**/.DS_Store`, `.idea/`, `.vscode/`, and other common editor/OS noise.
- [x] CI step fails the build when any tracked or working-tree path matches the ignored set.

**Notes**
Expanded `.gitignore` to cover OS metadata (DS_Store, Thumbs.db, Desktop.ini), editor caches (.idea, .vscode, swap files), and Python caches. Added a `Reject OS and IDE metadata` step to `.github/workflows/ci.yml` that prunes `.git`/`node_modules` then fails the build when DS_Store, Thumbs.db, Desktop.ini, or .idea/.vscode contents are present in the checkout.

**Verification**
- `find . \( -path ./.git -o -path ./node_modules \) -prune -o \( -name .DS_Store -o -name Thumbs.db -o -name Desktop.ini \) -print`: no output after cleanup
- `python3 scripts/validate_skill.py work-queue`: passed
- `python3 work-queue/scripts/validate_queue.py --strict-sections WORK_QUEUE.md`: passed

**Outcome**
Changed: `.gitignore`, `.github/workflows/ci.yml`. Deleted: `./.DS_Store`, `work-queue/.DS_Store`.

_Transient. Delete after merge, release, or durable record._

## Cancelled

_Transient. Delete after the cancellation decision is recorded._
