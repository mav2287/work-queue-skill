#!/usr/bin/env python3
"""Validate a Markdown work queue."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path


EARLIEST_SANE_DATE = date(2020, 1, 1)

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
BODY_HEADINGS = {
    "Problem / Want",
    "Acceptance",
    "Notes",
    "Verification",
    "Questions",
    "Blocked on",
}

SECTION_RE = re.compile(r"^##\s+(.+?)\s*$")
ITEM_RE = re.compile(r"^###\s+([A-Z][A-Z0-9]*-\d{3,})\s+(.+?)\s*$")
FIELD_RE = re.compile(r"^\s*-\s+\*\*(Type|Priority|Created|Area)\*\*:\s*(.+?)\s*$")
CHECKBOX_RE = re.compile(r"^\s*-\s+\[( |x|X)\]\s+(.+?)\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
BOLD_HEADING_RE = re.compile(r"^\*\*([^*]+)\*\*$")
BLOCKED_MARKER_RE = re.compile(r"^(?:-\s+)?\*\*(Blocked on|Questions)\*\*:?\s*.*$")
ID_REFERENCE_RE = re.compile(r"\b([A-Z][A-Z0-9]*-\d{3,})\b")
PLACEHOLDER_RE = re.compile(
    r"<[^>\n]+>|\b(?:tbd|todo|clarify)\b|\bneeds\s+clarification\b",
    re.IGNORECASE,
)


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


def is_fence(line: str) -> bool:
    return bool(FENCE_RE.match(line))


def iter_unfenced(lines: list[str]):
    in_fence = False
    for line in lines:
        if is_fence(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            yield line


def parse_items(text: str) -> tuple[list[Item], list[Section]]:
    items: list[Item] = []
    sections: list[Section] = []
    current_section = ""
    current_item: Item | None = None
    in_fence = False

    for index, line in enumerate(text.splitlines(), start=1):
        if is_fence(line):
            if current_item is not None:
                current_item.body.append(line)
            in_fence = not in_fence
            continue

        if in_fence:
            if current_item is not None:
                current_item.body.append(line)
            continue

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

    return items, sections


def extract_fields(item: Item) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in iter_unfenced(item.body):
        match = FIELD_RE.match(line)
        if match:
            fields[match.group(1)] = match.group(2).strip()
    return fields


def has_heading(item: Item, heading: str) -> bool:
    marker = f"**{heading}**"
    return any(line.strip() == marker for line in iter_unfenced(item.body))


def acceptance_boxes(item: Item) -> list[tuple[str, str]]:
    boxes: list[tuple[str, str]] = []
    in_acceptance = False
    for line in iter_unfenced(item.body):
        stripped = line.strip()
        if stripped == "**Acceptance**":
            in_acceptance = True
            continue
        heading_match = BOLD_HEADING_RE.match(stripped)
        if in_acceptance and heading_match and heading_match.group(1) in BODY_HEADINGS:
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


def has_blocked_marker(item: Item) -> bool:
    return any(BLOCKED_MARKER_RE.match(line.strip()) for line in iter_unfenced(item.body))


def validate_item(
    item: Item, allow_done: bool, strict: bool = False
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    fields = extract_fields(item)
    prefix = f"{item.id} line {item.line}"

    if item.section not in VALID_SECTIONS:
        errors.append(f"{prefix}: item is not inside a valid status section")

    if not item.title or item.title.startswith("<"):
        errors.append(f"{prefix}: title is missing or still a placeholder")

    _, _, number = item.id.rpartition("-")
    if number.isdigit() and int(number) == 0:
        warnings.append(
            f"{prefix}: item id looks like the template placeholder (id ends in -000); assign a real id before draining"
        )

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
    elif created:
        created_date = parse_date(created)
        if created_date is not None:
            today = date.today()
            if created_date > today:
                warnings.append(
                    f"{prefix}: Created {created} is in the future (today is {today.isoformat()}); likely typo"
                )
            elif created_date < EARLIEST_SANE_DATE:
                warnings.append(
                    f"{prefix}: Created {created} is before {EARLIEST_SANE_DATE.isoformat()}; likely typo"
                )

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
        if not has_heading(item, "Verification"):
            message = f"{prefix}: Done item must record verification in Notes"
            if strict:
                errors.append(message)
            else:
                warnings.append(message)

    if item.section == "Blocked":
        if not has_blocked_marker(item):
            errors.append(f"{prefix}: Blocked item needs 'Blocked on' or 'Questions'")

    if item.section == "Ready":
        body = "\n".join(iter_unfenced(item.body))
        if PLACEHOLDER_RE.search(body):
            warnings.append(
                f"{prefix}: Ready item may still contain placeholders or uncertainty"
            )

    return errors, warnings


def validate_sections(
    sections: list[Section], strict_sections: bool
) -> tuple[list[str], list[str]]:
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
            message = f"missing required section '## {section_name}'"
            if strict_sections:
                errors.append(message)
            else:
                warnings.append(message)

    actual_order = [section.name for section in status_sections]
    expected_order = [name for name in VALID_SECTIONS if name in actual_order]
    if actual_order != expected_order:
        message = "status sections should be ordered: " + " -> ".join(
            f"## {name}" for name in VALID_SECTIONS
        )
        if strict_sections:
            errors.append(message)
        else:
            warnings.append(message)

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
        if previous_key is not None and key < previous_key:
            assert previous_item is not None
            errors.append(
                f"{item.id} line {item.line}: Ready items must be sorted by priority, created date, then ID; appears after {previous_item.id}"
            )
        previous_key = key
        previous_item = item

    return errors, warnings


def normalize_title(title: str) -> str:
    return " ".join(title.lower().split())


def validate_duplicate_titles(items: list[Item]) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    seen: dict[str, Item] = {}
    for item in items:
        if not item.title or item.title.startswith("<"):
            continue
        if item.section in {"Done", "Cancelled"}:
            continue
        key = normalize_title(item.title)
        existing = seen.get(key)
        if existing is None:
            seen[key] = item
            continue
        warnings.append(
            f"{item.id} line {item.line}: duplicate title of {existing.id} (line {existing.line}); possible duplicate report"
        )
    return [], warnings


def validate_blocked_references(
    items: list[Item],
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    by_id: dict[str, Item] = {item.id: item for item in items}
    for item in items:
        if item.section != "Blocked":
            continue
        for line in iter_unfenced(item.body):
            stripped = line.strip()
            if not BLOCKED_MARKER_RE.match(stripped):
                continue
            for ref in ID_REFERENCE_RE.findall(stripped):
                if ref == item.id:
                    continue
                target = by_id.get(ref)
                if target is None:
                    errors.append(
                        f"{item.id} line {item.line}: Blocked on/Questions references unknown id {ref}"
                    )
                elif target.section in {"Done", "Cancelled"}:
                    warnings.append(
                        f"{item.id} line {item.line}: references {ref} which is now in '{target.section}' and may be retired"
                    )
    return errors, warnings


def validate_in_progress(
    items: list[Item], strict: bool
) -> tuple[list[str], list[str]]:
    in_progress = [item for item in items if item.section == "In progress"]
    if len(in_progress) <= 1:
        return [], []
    ids = ", ".join(f"{item.id} (line {item.line})" for item in in_progress)
    message = (
        f"In progress holds {len(in_progress)} items; the skill recommends one at a time: {ids}"
    )
    return ([message], []) if strict else ([], [message])


def validate(
    path: Path,
    allow_done: bool,
    strict_sections: bool,
    strict: bool = False,
) -> int:
    if strict:
        strict_sections = True
    text = path.read_text(encoding="utf-8")
    items, sections = parse_items(text)
    warnings: list[str] = []
    errors: list[str] = []
    section_errors, section_warnings = validate_sections(sections, strict_sections)
    errors.extend(section_errors)
    warnings.extend(section_warnings)

    seen: dict[str, int] = {}
    for item in items:
        if item.id in seen:
            errors.append(
                f"{item.id} line {item.line}: duplicate ID first seen on line {seen[item.id]}"
            )
        seen[item.id] = item.line

        item_errors, item_warnings = validate_item(item, allow_done, strict=strict)
        errors.extend(item_errors)
        warnings.extend(item_warnings)

    order_errors, order_warnings = validate_ready_order(items)
    errors.extend(order_errors)
    warnings.extend(order_warnings)

    in_progress_errors, in_progress_warnings = validate_in_progress(items, strict)
    errors.extend(in_progress_errors)
    warnings.extend(in_progress_warnings)

    ref_errors, ref_warnings = validate_blocked_references(items)
    errors.extend(ref_errors)
    warnings.extend(ref_warnings)

    dup_errors, dup_warnings = validate_duplicate_titles(items)
    errors.extend(dup_errors)
    warnings.extend(dup_warnings)

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
    parser.add_argument(
        "queue_files",
        type=Path,
        nargs="+",
        help="One or more queue files. Shell globs (WORK_QUEUE*.md) are accepted.",
    )
    parser.add_argument(
        "--allow-done",
        action="store_true",
        help="Do not warn merely because Done items are present.",
    )
    parser.add_argument(
        "--strict-sections",
        action="store_true",
        help="Require the canonical section set and ordering.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote opinionated warnings (multiple In progress, missing Verification on Done, etc.) to errors. Implies --strict-sections.",
    )
    args = parser.parse_args()

    worst = 0
    multi = len(args.queue_files) > 1
    for queue_file in args.queue_files:
        if multi:
            print(f"::: {queue_file}", file=sys.stderr)
        if not queue_file.exists():
            print(f"ERROR: file not found: {queue_file}", file=sys.stderr)
            worst = max(worst, 2)
            continue
        result = validate(
            queue_file,
            args.allow_done,
            args.strict_sections,
            strict=args.strict,
        )
        worst = max(worst, result)
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
