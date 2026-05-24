#!/usr/bin/env python3
"""Validate the packaged work-queue skill without third-party dependencies."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
NAME_RE = re.compile(r"^[a-z0-9-]{1,64}$")
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
FRONTMATTER_LINE_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9_-]*)\s*:\s*(.*?)\s*$")
PYTHON_PATH_RE = re.compile(
    r"(?<![\w./-])(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\.py(?![\w.-])"
)


def parse_frontmatter(skill_md: Path) -> tuple[dict[str, str], str]:
    text = skill_md.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError("SKILL.md must start with YAML frontmatter")

    # This validator intentionally supports only one-line YAML scalars. Skill
    # metadata should stay simple enough to validate without PyYAML.
    frontmatter: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        line_match = FRONTMATTER_LINE_RE.match(line)
        if not line_match:
            raise ValueError(f"unsupported frontmatter line: {line!r}")
        key, value = line_match.groups()
        if value in {"|", ">"}:
            raise ValueError(f"multiline frontmatter value is not supported: {key}")
        if (value.startswith('"') or value.startswith("'")) and value[0] != value[-1]:
            raise ValueError(f"frontmatter value has mismatched quotes: {key}")
        if len(value) >= 2 and value[0] in {"'", '"'}:
            value = value[1:-1]
        frontmatter[key.strip()] = value

    return frontmatter, text[match.end() :]


def validate_markdown_links(skill_dir: Path, skill_text: str) -> list[str]:
    errors: list[str] = []
    for raw_target in MARKDOWN_LINK_RE.findall(skill_text):
        if "://" in raw_target or raw_target.startswith("#"):
            continue
        target = raw_target.split("#", 1)[0]
        if not target:
            continue
        if not (skill_dir / target).exists():
            errors.append(f"SKILL.md links to missing file: {raw_target}")
    return errors


def validate_openai_yaml(skill_dir: Path, skill_name: str) -> list[str]:
    errors: list[str] = []
    metadata = skill_dir / "agents" / "openai.yaml"
    if not metadata.exists():
        return errors

    text = metadata.read_text(encoding="utf-8")
    if not re.search(r"^interface:\s*$", text, re.MULTILINE):
        errors.append("agents/openai.yaml missing top-level interface key")

    default_prompt = ""
    for key in ["display_name", "short_description", "default_prompt"]:
        match = re.search(rf"^  {key}:\s*(.+)$", text, re.MULTILINE)
        if not match:
            errors.append(f"agents/openai.yaml missing interface.{key}")
        elif key == "default_prompt":
            default_prompt = match.group(1)

    if default_prompt and f"${skill_name}" not in default_prompt:
        errors.append(f"agents/openai.yaml default_prompt should mention ${skill_name}")

    return errors


def validate_referenced_scripts(skill_dir: Path, skill_text: str) -> list[str]:
    errors: list[str] = []
    for script_path in sorted(set(PYTHON_PATH_RE.findall(skill_text))):
        if not script_path.startswith("scripts/"):
            continue
        if not (skill_dir / script_path).exists():
            errors.append(f"SKILL.md references missing script: {script_path}")
    return errors


def validate(skill_dir: Path) -> int:
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.exists():
        errors.append("missing SKILL.md")
    else:
        try:
            frontmatter, skill_text = parse_frontmatter(skill_md)
        except ValueError as exc:
            errors.append(str(exc))
            frontmatter = {}
            skill_text = ""

        skill_name = frontmatter.get("name", "")
        description = frontmatter.get("description", "")

        if not skill_name:
            errors.append("frontmatter missing name")
        elif not NAME_RE.fullmatch(skill_name):
            errors.append("frontmatter name must be lowercase hyphen-case, max 64 chars")
        elif skill_name != skill_dir.name:
            errors.append(
                f"frontmatter name '{skill_name}' does not match directory '{skill_dir.name}'"
            )

        if not description:
            errors.append("frontmatter missing description")
        elif len(description) > 1024:
            errors.append("frontmatter description must be 1024 chars or fewer")
        elif "<" in description or ">" in description:
            errors.append(
                "frontmatter description must not contain angle brackets; agent UIs may render it as markdown or HTML"
            )

        errors.extend(validate_markdown_links(skill_dir, skill_text))
        errors.extend(validate_referenced_scripts(skill_dir, skill_text))
        if skill_name:
            errors.extend(validate_openai_yaml(skill_dir, skill_name))

    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if errors:
        print(f"Skill validation failed: {len(errors)} error(s)")
        return 1

    print(f"Skill validation passed: {skill_dir}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_dir", type=Path)
    args = parser.parse_args()
    return validate(args.skill_dir)


if __name__ == "__main__":
    raise SystemExit(main())
