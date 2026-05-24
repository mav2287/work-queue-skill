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


def parse_frontmatter(skill_md: Path) -> tuple[dict[str, str], str]:
    text = skill_md.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError("SKILL.md must start with YAML frontmatter")

    frontmatter: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        if ": " not in line:
            raise ValueError(f"unsupported frontmatter line: {line!r}")
        key, value = line.split(": ", 1)
        frontmatter[key.strip()] = value.strip().strip("\"'")

    return frontmatter, text


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
    required_lines = [
        "interface:",
        "display_name:",
        "short_description:",
        "default_prompt:",
    ]
    for marker in required_lines:
        if marker not in text:
            errors.append(f"agents/openai.yaml missing {marker}")

    if f"${skill_name}" not in text:
        errors.append(f"agents/openai.yaml default_prompt should mention ${skill_name}")

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
            errors.append("frontmatter description must not contain angle brackets")

        errors.extend(validate_markdown_links(skill_dir, skill_text))
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
