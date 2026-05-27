# Distribution Decision

Investigation closed 2026-05-26 as part of WQ-033. Records which
discoverability channels this skill should target, the submission
process for each, and the maintenance cost.

## Candidate channels

### 1. awesome-claude-code lists

- **Process**: PR adding the repo URL + one-line description to the
  relevant section of `rohitg00/awesome-claude-code-toolkit` (and any
  successor list).
- **Audience**: developers actively browsing curated Claude Code lists;
  high signal, modest volume.
- **Cost**: one PR, no ongoing maintenance.
- **Decision**: **in scope.** Highest signal-to-effort ratio.

### 2. mcpmarket.com / Agensi catalog

- **Process**: web submission form; both catalogs list Codex- and
  Claude-compatible skills. Agensi runs the `skills.sh` Vercel-backed
  installer that pulls from its catalog.
- **Audience**: users searching for ready-to-install skills; broadest
  reach of any current channel.
- **Cost**: one submission per catalog; a new release requires updating
  the listing (the release CI in `WQ-027` produces a zip the catalogs
  can link to directly).
- **Decision**: **in scope.** Submit both.

### 3. openai/skills (official Codex catalog)

- **Process**: the catalog appears curated; PRs from non-OpenAI authors
  are uncommon and there is no documented submission flow.
- **Audience**: every Codex user (built-in catalog), but only if
  accepted.
- **Cost**: PR attempt may go unanswered; low expected value.
- **Decision**: **defer.** Revisit if OpenAI documents a community
  submission flow.

### 4. anthropics/skills (official Anthropic catalog)

- **Process**: same posture as `openai/skills`; no documented community
  submission flow today.
- **Audience**: every Claude Code user (built-in catalog).
- **Cost**: same as above.
- **Decision**: **defer.** Revisit when a flow is published.

### 5. GitHub repo polish (topics, README badges)

- **Process**: set repo topics (`claude-code`, `codex`, `agent-skill`,
  `markdown-task-queue`), add a one-line GitHub repo description and
  social-preview image.
- **Audience**: organic search traffic.
- **Cost**: low, one-time.
- **Decision**: **in scope.**

## Status

This document is analysis only. No submissions have been filed and no
follow-up queue items have been created. Whether and when to submit to
any channel is the owner's call; this doc exists so the analysis does
not need to be repeated.
