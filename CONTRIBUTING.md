# Contributing

Thanks for taking the time. This project is a Markdown work-queue skill
for Claude Code and Codex, plus two stdlib-only Python validators. The
contribution loop is intentionally small: edit, run two commands, send a
PR.

## Dev loop

```bash
# 1. Install Python 3.10+ (already required by CI matrix).
python3 --version

# 2. Run the regression tests.
python3 -m unittest discover -s tests

# 3. Validate the skill itself.
python3 scripts/validate_skill.py work-queue

# 4. Validate the bundled queue fixtures.
python3 work-queue/scripts/validate_queue.py --strict-sections \
    work-queue/templates/WORK_QUEUE.md \
    work-queue/examples/sample-queue.md \
    work-queue/examples/done-with-outcome.md
```

No third-party dependencies. The validators run on a clean stdlib
install; do not introduce a dependency without a recorded decision in
`CHANGELOG.md`.

### Optional: pre-commit hooks

Install [pre-commit](https://pre-commit.com) and run:

```bash
pre-commit install
```

The bundled `.pre-commit-config.yaml` registers three local hooks that
run the skill validator, the queue validator against bundled fixtures,
and the regression tests on every commit that touches the relevant
files. The hooks are `language: system` so no extra Python environment
is created.

## Filing changes

Open an issue first when the change is larger than a few lines, so we
can agree on scope before code. For small fixes (typos, validator
messages, doc cleanup) just send the PR.

For everything: keep PRs scoped to one concern, follow the existing
commit-message style (imperative subject, no scope prefix, body
wraps at ~72 columns), and update `CHANGELOG.md` under the
`[Unreleased]` section when the change is user-visible.

## Skill content edits

When you change anything under `work-queue/`, run the queue validator
afterwards. The skill is the published artifact; anything not caught by
the validator will surface in users' real queues.

When you change a body heading name (anything in `BODY_HEADINGS`),
update `references/queue-format.md` and `templates/item.md` in the same
PR. The validator only knows about names listed in code.

## Releasing

Releases are cut by pushing a `v*` tag. The `Release` workflow
validates, packages `work-queue/` into a zip, and publishes a GitHub
Release with the matching `CHANGELOG.md` section as the body. The
workflow refuses to release if the changelog has no entry for the
version, so the changelog update is a hard gate.

## Reporting bugs

Use the queue format the skill teaches: file issues with
expected/observed behaviour, the repro path, and the smallest possible
acceptance criteria. The maintainers will mirror Ready issues into the
local `WORK_QUEUE.md` and drain them.

## Code of conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
