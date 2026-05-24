#!/usr/bin/env python3
"""Validate a Markdown work queue."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path


VALID_SECTIONS = [
    "In progress",
    "Blocked",
    "Ready",
    "Needs refinement",
    "Inbox",
    "Done",
    "Cancelled",
]
VALID_TYPES = {"bug", "feature", "chore", "docs", "refactor", "investigation"}
VALID_PRIORITIES = {"P0", "P1", "P2", "P3"}
NON_STATUS_SECTIONS = {"Queue Rules"}
PRIORITY_RANK = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}

SECTION_RE = re.compile(r"^##\s+(.+?)\s*$")
ITEM_RE = re.compile(r"^###\s+([A-Z][A-Z0-9]*-\d{3,})\s+(.+?)\s*$")
FIELD_RE = re.compile(r"^-\s+\*\*(Type|Priority|Created|Area)\*\*:\s*(.+?)\s*$")
CHECKBOX_RE = re.compile(r"^-\s+\[( |x|X)\]\s+(.+?)\s*$")


@dataclass
class Item:
    id: str
    title: str
    section: str
    line: int
    body: list[str]


@dataclass
class Section:
    name: str
    line: int


def parse_items(text: str) -> tuple[list[Item], list[Section], list[str]]:
    items: list[Item] = []
    sections: list[Section] = []
    warnings: list[str] = []
    current_section = ""
    current_item: Item | None = None

    for index, line in enumerate(text.splitlines(), start=1):
        section_match = SECTION_RE.match(line)
        if section_match:
            current_section = section_match.group(1).strip()
            sections.append(Section(current_section, index))
            current_item = None
            continue

        item_match = ITEM_RE.match(line)
        if item_match:
            current_item = Item(
                id=item_match.group(1),
                title=item_match.group(2).strip(),
                section=current_section,
                line=index,
                body=[],
            )
            items.append(current_item)
            continue

        if current_item is not None:
            current_item.body.append(line)

    return items, sections, warnings


def extract_fields(item: Item) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in item.body:
        match = FIELD_RE.match(line)
        if match:
            fields[match.group(1)] = match.group(2).strip()
    return fields


def has_heading(item: Item, heading: str) -> bool:
    marker = f"**{heading}**"
    return any(line.strip() == marker for line in item.body)


def acceptance_boxes(item: Item) -> list[tuple[str, str]]:
    boxes: list[tuple[str, str]] = []
    in_acceptance = False
    for line in item.body:
        stripped = line.strip()
        if stripped == "**Acceptance**":
            in_acceptance = True
            continue
        if in_acceptance and stripped.startswith("**") and stripped.endswith("**"):
            break
        if in_acceptance:
            match = CHECKBOX_RE.match(line)
            if match:
                boxes.append((match.group(1), match.group(2)))
    return boxes


def validate_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def id_sort_value(item_id: str) -> tuple[str, int]:
    prefix, _, number = item_id.rpartition("-")
    try:
        numeric = int(number)
    except ValueError:
        numeric = 0
    return prefix, numeric


def validate_item(item: Item, allow_done: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    fields = extract_fields(item)
    prefix = f"{item.id} line {item.line}"

    if item.section not in VALID_SECTIONS:
        errors.append(f"{prefix}: item is not inside a valid status section")

    if not item.title or item.title.startswith("<"):
        errors.append(f"{prefix}: title is missing or still a placeholder")

    for field in ["Type", "Priority", "Created", "Area"]:
        if field not in fields:
            errors.append(f"{prefix}: missing field '{field}'")

    item_type = fields.get("Type", "")
    if item_type and item_type not in VALID_TYPES:
        errors.append(f"{prefix}: invalid Type '{item_type}'")

    priority = fields.get("Priority", "")
    if priority and priority not in VALID_PRIORITIES:
        errors.append(f"{prefix}: invalid Priority '{priority}'")

    created = fields.get("Created", "")
    if created and not validate_date(created):
        errors.append(f"{prefix}: Created must be YYYY-MM-DD")

    if not has_heading(item, "Problem / Want"):
        errors.append(f"{prefix}: missing Problem / Want section")
    if not has_heading(item, "Acceptance"):
        errors.append(f"{prefix}: missing Acceptance section")
    if not has_heading(item, "Notes"):
        errors.append(f"{prefix}: missing Notes section")

    boxes = acceptance_boxes(item)
    if item.section in {"Ready", "In progress", "Done"} and not boxes:
        errors.append(f"{prefix}: {item.section} item needs acceptance checkboxes")

    if item.section == "Done":
        unchecked = [text for mark, text in boxes if mark == " "]
        if unchecked:
            errors.append(f"{prefix}: Done item has unchecked acceptance boxes")
        if not allow_done:
            warnings.append(
                f"{prefix}: Done items should be retired after a durable record exists"
            )
        if "Verification" not in "\n".join(item.body):
            warnings.append(f"{prefix}: Done item should record verification in Notes")

    if item.section == "Blocked":
        body = "\n".join(item.body)
        if "Blocked on" not in body and "Questions" not in body:
            errors.append(f"{prefix}: Blocked item needs 'Blocked on' or 'Questions'")

    if item.section == "Ready":
        body = "\n".join(item.body).lower()
        placeholders = ["<", "tbd", "todo", "clarify", "unknown"]
        if any(token in body for token in placeholders):
            warnings.append(
                f"{prefix}: Ready item may still contain placeholders or uncertainty"
            )

    return errors, warnings


def validate_sections(sections: list[Section]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    status_sections = [section for section in sections if section.name in VALID_SECTIONS]
    seen: dict[str, int] = {}

    for section in sections:
        if section.name in VALID_SECTIONS or section.name in NON_STATUS_SECTIONS:
            continue
        errors.append(f"line {section.line}: unknown section '{section.name}'")

    for section in status_sections:
        if section.name in seen:
            errors.append(
                f"line {section.line}: duplicate section '{section.name}' first seen on line {seen[section.name]}"
            )
        seen[section.name] = section.line

    for section_name in VALID_SECTIONS:
        if section_name not in seen:
            errors.append(f"missing required section '## {section_name}'")

    actual_order = [section.name for section in status_sections]
    expected_order = [name for name in VALID_SECTIONS if name in actual_order]
    if actual_order != expected_order:
        errors.append(
            "status sections should be ordered: "
            + " -> ".join(f"## {name}" for name in VALID_SECTIONS)
        )

    return errors, warnings


def validate_ready_order(items: list[Item]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    ready_items = [item for item in items if item.section == "Ready"]
    previous_key: tuple[int, date, tuple[str, int]] | None = None
    previous_item: Item | None = None

    for item in ready_items:
        fields = extract_fields(item)
        priority = fields.get("Priority")
        created = parse_date(fields.get("Created", ""))
        if priority not in PRIORITY_RANK or created is None:
            continue

        key = (PRIORITY_RANK[priority], created, id_sort_value(item.id))
        if previous_key is not None and key < previous_key and previous_item is not None:
            errors.append(
                f"{item.id} line {item.line}: Ready items must be sorted by priority, created date, then ID; appears after {previous_item.id}"
            )
        previous_key = key
        previous_item = item

    return errors, warnings


def validate(path: Path, allow_done: bool) -> int:
    text = path.read_text(encoding="utf-8")
    items, sections, warnings = parse_items(text)
    errors: list[str] = []
    section_errors, section_warnings = validate_sections(sections)
    errors.extend(section_errors)
    warnings.extend(section_warnings)

    seen: dict[str, int] = {}
    for item in items:
        if item.id in seen:
            errors.append(
                f"{item.id} line {item.line}: duplicate ID first seen on line {seen[item.id]}"
            )
        seen[item.id] = item.line

        item_errors, item_warnings = validate_item(item, allow_done)
        errors.extend(item_errors)
        warnings.extend(item_warnings)

    order_errors, order_warnings = validate_ready_order(items)
    errors.extend(order_errors)
    warnings.extend(order_warnings)

    if not items:
        warnings.append("no queue items found")

    for message in warnings:
        print(f"WARN: {message}", file=sys.stderr)
    for message in errors:
        print(f"ERROR: {message}", file=sys.stderr)

    if errors:
        print(f"Queue validation failed: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1

    print(f"Queue validation passed: {len(items)} item(s), {len(warnings)} warning(s)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("queue_file", type=Path)
    parser.add_argument(
        "--allow-done",
        action="store_true",
        help="Do not warn merely because Done items are present.",
    )
    args = parser.parse_args()

    if not args.queue_file.exists():
        print(f"ERROR: file not found: {args.queue_file}", file=sys.stderr)
        return 2

    return validate(args.queue_file, args.allow_done)


if __name__ == "__main__":
    raise SystemExit(main())
