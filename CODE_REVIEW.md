# Senior Code Review — work-queue-skill

Scope: full repo at `efcac53` — skill content, validators, packaging, CI.

Overall: small, well-organized project. Documentation and skill structure are tight and readable. The validators do real work, not theater. But there are concrete correctness bugs in both Python scripts, one broken runtime instruction in `SKILL.md`, and a couple of packaging foot-guns. None are catastrophic; all are fixable in a small follow-up.

---

## Blocking issues

### 1. `SKILL.md` references an env var that does not exist
`work-queue/SKILL.md:80`
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/validate_queue.py WORK_QUEUE.md
```
`CLAUDE_SKILL_DIR` is not set by Claude Code (verified against this session's env and the public skill loader behavior). When an agent follows the instruction literally the variable expands to empty and the command becomes `python3 /scripts/validate_queue.py …`, which fails with `No such file or directory`. The agent will then either silently skip validation or hallucinate a path.

Fix: either drop the env-var indirection and tell the agent to resolve the script via the skill's own bundled location (the agent already knows where SKILL.md lives), or document the variable somewhere the loader actually sets it. Easiest concrete fix:

```bash
python3 "$(dirname "$0")/scripts/validate_queue.py" WORK_QUEUE.md   # no
# better: instruct the agent to call work-queue/scripts/validate_queue.py
# using the absolute path it already resolved when reading SKILL.md.
```

### 2. `validate_queue.py` mis-parses fenced code blocks
`work-queue/scripts/validate_queue.py:49-79`

`parse_items` walks the file line by line and matches `^## ` / `^### WQ-` with no awareness of `` ``` `` fences. Any queue item whose Notes contain an example queue snippet (which is exactly what intake.md and the references encourage) will:

- have headings inside the fence treated as real `## Section` markers
- have `### WQ-NNN` lines inside the fence treated as new items

Reproduced locally with a Ready item whose Notes contained a fenced markdown example — the validator emitted 7 spurious errors including "duplicate section 'Ready'" and "Ready items must be sorted…", and split the body so the real item lost its Acceptance/Notes detection.

Fix: track a `in_fence` boolean toggled on lines that start with `` ``` `` (allowing optional info string) and skip the section/item regexes while inside. Same toggle should gate `acceptance_boxes` and `has_heading` to avoid the symmetric false positives on body parsing.

### 3. `acceptance_boxes` terminator is too eager
`work-queue/scripts/validate_queue.py:96-110`

The loop ends Acceptance as soon as it sees any line that is exactly `**X**`. That breaks legitimate Acceptance bodies that lead with an emphasized callout, e.g.:

```
**Acceptance**

**MUST**

- [ ] real criterion
```

The validator then reports "needs acceptance checkboxes" even though the item is fine. Reproduced.

Fix: terminate on the *known* next heading set (`Notes`, `Problem / Want`, `Verification`, `Questions`, `Blocked on`) — or, better, on the next blank-line-then-bold-heading pattern, not on any standalone bold token.

---

## Correctness / robustness issues

### 4. `parse_frontmatter` is a bespoke YAML parser
`scripts/validate_skill.py:17-32`

- Splits on `": "` (literal space-after-colon). A trailing-whitespace edit or a non-ASCII space breaks it with `unsupported frontmatter line`.
- `strip("\"'")` mis-handles values like `"foo'` (mixed quotes) by stripping both ends.
- Multi-line description (YAML `>` or `|`) would crash.

Skill frontmatter is small, so this works today, but it's a fragile foundation for a validator whose only job is being strict. Either pin to a one-line subset and document it, or import `tomllib`/`yaml` — Python stdlib doesn't ship YAML, so a documented single-line-scalars-only constraint is fine; just say so in a comment and reject anything else explicitly instead of silently producing wrong keys.

### 5. `validate_openai_yaml` does substring matching, not YAML parsing
`scripts/validate_skill.py:48-68`

Looking for the literal strings `interface:`, `display_name:`, etc., means a commented-out line passes, and a real YAML structural error (wrong nesting, duplicated keys) also passes. Either parse it as YAML (would require a dep — probably not worth it for this repo) or be honest that this is a smoke check and reduce the description from "validates" to "checks presence of required keys."

### 6. Markdown link checker scans the YAML frontmatter
`scripts/validate_skill.py:35-45`

`MARKDOWN_LINK_RE.findall(skill_text)` runs on the full text including the frontmatter block. The description field today has no `[x](y)` syntax, but if it ever does (a URL to the spec, for example), it will be checked as a relative file link. Strip the frontmatter slice off `skill_text` before scanning.

### 7. Mandatory-section rule is over-rigid
`work-queue/scripts/validate_queue.py:221-223`

`validate_sections` requires **all seven** status sections to be present. Real projects that only want `Ready`/`In progress`/`Done` get errored. The skill prose (`queue-format.md`) prescribes the full list, so this is internally consistent — but if you want this to be adoptable by existing repos with a different shape (the SKILL.md says "If the repo already has a queue/backlog file, use that file"), the validator contradicts the skill. Consider a `--strict-sections` flag, defaulting to off, and emit warnings instead.

### 8. Indented bullets are invisible to the validator
`FIELD_RE` and `CHECKBOX_RE` both anchor with `^-`. A queue item with 2-space-indented bullets (common when nested under another bullet) is treated as having no fields and no acceptance boxes. Probably acceptable as a documented constraint, but worth a one-line note in `queue-format.md` so users don't waste time debugging "missing field 'Type'" when the field is right there.

### 9. Dead variable in `parse_items`
```python
def parse_items(text: str) -> tuple[list[Item], list[Section], list[str]]:
    ...
    warnings: list[str] = []
    ...
    return items, sections, warnings
```
`warnings` is never appended to and the caller ignores it (`items, sections, _ = parse_items(...)` would be honest; today it's spread into a real variable and then overwritten). Either delete the third return value or actually populate it.

### 10. Loose substring checks produce false positives/negatives
- Ready placeholder warning checks for `"<"`, `"tbd"`, `"todo"`, `"unknown"` anywhere in the lowercased body. Real Notes like `"<= 5%"`, `"unknown error path"`, `"TODO list reviewed"` will trip it. Either anchor to whole words (`\b(tbd|todo|unknown)\b`) or restrict the search to specific fields.
- Done-item verification check is `if "Verification" not in "\n".join(item.body)`. A Notes line that says "No verification performed" passes the check. The intent of the check is the opposite. Match `**Verification**` explicitly to require the heading.

---

## Packaging / DX

### 11. `cp -R work-queue/*` will silently drop dotfiles
`README.md:18-35`

Glob expansion under default shells excludes `.*`. There are no dotfiles in `work-queue/` today, but if a `.skillrc` or `.codexrc` ever lands there it won't be copied and nobody will notice. Switch all three install snippets to:

```bash
cp -R work-queue/. ~/.claude/skills/work-queue/
```

(The trailing `/.` copies contents including dotfiles into the destination.)

### 12. CI doesn't pin Python and doesn't test the failure surface
`.github/workflows/ci.yml`

- `python-version: "3.x"` floats to whatever is newest. Pin a minimum (`"3.10"` — required by your `int | None` annotations) and ideally a matrix of `3.10`/`3.12` to catch regressions early.
- The only validator coverage is the two happy-path queues. None of the bugs in §2/§3 above would have been caught by CI. Add a `tests/` directory with fixtures (`bad-fence.md`, `bad-acceptance.md`, etc.) and assert the validator exits non-zero with the expected error substrings. Even five-line `unittest`s are enough.

### 13. `validate_skill.py` does not validate the `scripts/` referenced from `SKILL.md`
The whole point of the package validator is that bundled assets exist. It checks links found in markdown, but not commands referenced in code fences. Given §1, a check that "every relative path that looks like `*.py` referenced from SKILL.md actually exists under the skill dir" would have caught the bad invocation.

### 14. Minor: tracked `.DS_Store`?
`ls -la` shows `.DS_Store` at the repo root and `.gitignore` lists it, but `git ls-files` shows it isn't tracked. Good — but the same file at `work-queue/.DS_Store` would silently be `cp -R`'d into a user's `~/.claude/skills/`. The `cp -R work-queue/.` fix would actually make this worse; add an explicit clean step or stop copying with `-R` and use `rsync --exclude='.DS_Store'` if you want belt-and-suspenders.

---

## Style / smaller notes

- `validate_queue.py:189` — `if "Blocked on" not in body and "Questions" not in body`. Two substring checks where you could match `^**(Blocked on|Questions)**` headings. Same pattern as §10.
- `validate_queue.py:251` — `if previous_key is not None and key < previous_key and previous_item is not None`. The third clause is implied by the first (they're updated together). Tightening removes a reader's "wait, can previous_key be set without previous_item?" pause.
- `validate_skill.py:101` — rejecting `<` / `>` in the description is a reasonable safety guard but the error message doesn't explain why. One-liner: "description is shown in agent UIs that may render markdown/HTML; angle brackets can produce malformed output."
- `references/drain.md:73-77` recommends "one commit per completed queue item" and "do not overwrite unrelated user changes." Good guidance, but worth restating in `SKILL.md`'s Drain Loop section so an agent that only reads SKILL.md still gets it. Right now step 9 says "Commit, checkpoint, or otherwise isolate" without the user-changes warning.
- `templates/item.md` uses `WQ-XXX`. Worth mentioning in a comment that this is intentional and must be edited before saving into a real queue (the validator will accept `WQ-XXX` because the regex requires only `\d{3,}` after the dash, but `XXX` would fail the regex — i.e. the template would not parse as an item at all, which is the correct behavior but is silent: it just won't be detected as an item and the user will get no Type/Priority errors).

---

## Recommendation

Ship-blocking fix list (in priority order):
1. Remove or correct the `${CLAUDE_SKILL_DIR}` invocation in `SKILL.md`.
2. Make `parse_items` fence-aware in `validate_queue.py`.
3. Tighten `acceptance_boxes` terminator to known headings.
4. Add at least one negative-path fixture per validator to CI.
5. Switch install instructions to `cp -R work-queue/.` and pin a minimum Python in CI.

Everything else is post-1.0 polish. The skill content itself (intake/drain/queue-format references, the Ready-bar definition, the explicit "do not silently expand scope" rule) is the strongest part of this repo and I'd leave it alone.
