#!/usr/bin/env python3
"""Validate a Markdown work queue."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any


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
    "Local checks before asking",
    "Verification",
    "Outcome",
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
SPLIT_LINK_RE = re.compile(
    r"^\s*-\s+\[[\sxX]\]\s+\[([A-Z][A-Z0-9]*-\d{3,})\s+([^\]]+?)\]\(items/[^)]+\)"
)
ITEM_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
FRONTMATTER_FIELD_RE = re.compile(r"^([a-z][a-z0-9_]*)\s*:\s*(.*?)\s*$")
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


def iter_unfenced(lines: list[str]) -> Iterator[str]:
    in_fence = False
    for line in lines:
        if is_fence(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            yield line


def detect_layout(queue_path: Path) -> str:
    """Return "split" if a sibling ``items/`` directory holds WQ-NNN.md files, else "single"."""
    items_dir = queue_path.parent / "items"
    if items_dir.is_dir() and any(items_dir.glob("WQ-*.md")):
        return "split"
    return "single"


def _parse_item_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Strip an item file's YAML frontmatter; return (fields, body)."""
    match = ITEM_FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        field_match = FRONTMATTER_FIELD_RE.match(line)
        if not field_match:
            continue
        value = field_match.group(2)
        if len(value) >= 2 and value[0] in {"'", '"'} and value[0] == value[-1]:
            value = value[1:-1]
        fields[field_match.group(1)] = value
    return fields, text[match.end():]


def parse_split_queue(
    queue_path: Path,
) -> tuple[list[Item], list[Section], list[str]]:
    """Parse a split-layout queue. Returns (items, sections, parse_errors)."""
    text = queue_path.read_text(encoding="utf-8")
    sections: list[Section] = []
    parse_errors: list[str] = []
    section_for_id: dict[str, tuple[str, int]] = {}
    seen_ids: set[str] = set()
    current_section = ""
    in_fence = False

    for index, line in enumerate(text.splitlines(), start=1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        section_match = SECTION_RE.match(line)
        if section_match:
            current_section = section_match.group(1).strip()
            sections.append(Section(current_section, index))
            continue
        link_match = SPLIT_LINK_RE.match(line)
        if link_match:
            item_id = link_match.group(1)
            if item_id in seen_ids:
                parse_errors.append(
                    f"{item_id} line {index}: duplicate index link first seen on line {section_for_id[item_id][1]}"
                )
                continue
            seen_ids.add(item_id)
            section_for_id[item_id] = (current_section, index)

    items_dir = queue_path.parent / "items"
    items: list[Item] = []
    for item_id, (section, link_line) in section_for_id.items():
        item_path = items_dir / f"{item_id}.md"
        if not item_path.exists():
            parse_errors.append(
                f"{item_id} line {link_line}: index links to missing file {item_path.name}"
            )
            continue
        item_text = item_path.read_text(encoding="utf-8")
        frontmatter, body = _parse_item_frontmatter(item_text)
        body_lines = body.splitlines()

        title = ""
        for body_line in body_lines:
            title_match = ITEM_RE.match(body_line)
            if title_match:
                title = title_match.group(2).strip()
                break

        synthetic: list[str] = []
        for key in ("type", "priority", "created", "area"):
            value = frontmatter.get(key, "")
            synthetic.append(f"- **{key.capitalize()}**: {value}")
        synthetic.append("")
        synthetic.extend(body_lines)

        items.append(
            Item(
                id=item_id,
                title=title,
                section=section,
                line=link_line,
                body=synthetic,
            )
        )

    return items, sections, parse_errors


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
        if not has_heading(item, "Outcome"):
            warnings.append(
                f"{prefix}: Done item should record Outcome (changed files, PR or commit reference) before retirement"
            )

    if item.section == "Blocked":
        if not has_blocked_marker(item):
            errors.append(f"{prefix}: Blocked item needs 'Blocked on' or 'Questions'")

    if item.section == "Ready":
        body = "\n".join(iter_unfenced(item.body))
        if PLACEHOLDER_RE.search(body):
            warnings.append(
                f"{prefix}: Ready item may still contain placeholders or uncertainty"
            )
        if "Example only" in body or "example only" in body:
            warnings.append(
                f"{prefix}: Ready item still contains 'Example only' placeholder text"
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


DEFAULT_MAX_INBOX_SIZE = 25
DEFAULT_MAX_INBOX_AGE_DAYS = 30


def validate_inbox(
    items: list[Item], max_size: int, max_age_days: int
) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    inbox = [item for item in items if item.section == "Inbox"]
    if max_size > 0 and len(inbox) > max_size:
        warnings.append(
            f"Inbox holds {len(inbox)} items; triage threshold is {max_size}"
        )
    if max_age_days > 0:
        today = date.today()
        for item in inbox:
            fields = extract_fields(item)
            created = parse_date(fields.get("Created", ""))
            if created is None:
                continue
            age_days = (today - created).days
            if age_days > max_age_days:
                warnings.append(
                    f"{item.id} line {item.line}: Inbox item has been waiting {age_days} days (threshold {max_age_days})"
                )
    return [], warnings


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


_SPLIT_LINK_TRAIL_RE = re.compile(r"—\s*(P[0-3])\b")


def _split_link_sort_key(line: str) -> tuple[int, tuple[str, int]]:
    match = SPLIT_LINK_RE.match(line)
    if not match:
        return 9, ("", 0)
    item_id = match.group(1)
    priority_match = _SPLIT_LINK_TRAIL_RE.search(line)
    priority = priority_match.group(1) if priority_match else ""
    return PRIORITY_RANK.get(priority, 9), id_sort_value(item_id)


def _item_sort_key(item_lines: list[str]) -> tuple[int, date, tuple[str, int]]:
    header_match = ITEM_RE.match(item_lines[0])
    item_id = header_match.group(1) if header_match else "ZZ-999"
    priority_rank = 9
    created = date.max
    in_fence = False
    for line in item_lines[1:]:
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        field_match = FIELD_RE.match(line)
        if not field_match:
            continue
        if field_match.group(1) == "Priority":
            priority_rank = PRIORITY_RANK.get(field_match.group(2).strip(), 9)
        elif field_match.group(1) == "Created":
            parsed = parse_date(field_match.group(2).strip())
            if parsed is not None:
                created = parsed
    return priority_rank, created, id_sort_value(item_id)


def _split_section_body(body: list[str]) -> tuple[list[str], list[list[str]]]:
    pre: list[str] = []
    items: list[list[str]] = []
    current: list[str] | None = None
    in_fence = False
    for line in body:
        if FENCE_RE.match(line):
            in_fence = not in_fence
            (current if current is not None else pre).append(line)
            continue
        if not in_fence and ITEM_RE.match(line):
            if current is not None:
                items.append(current)
            current = [line]
            continue
        (current if current is not None else pre).append(line)
    if current is not None:
        items.append(current)
    return pre, items


def _trim_block(lines: list[str]) -> list[str]:
    start = 0
    end = len(lines)
    while start < end and lines[start].strip() == "":
        start += 1
    while end > start and lines[end - 1].strip() == "":
        end -= 1
    return lines[start:end]


def fix_queue(text: str) -> str:
    lines = [line.rstrip() for line in text.splitlines()]

    sections: list[tuple[str, list[str]]] = []
    preamble: list[str] = []
    current_name: str | None = None
    current_body: list[str] = []
    in_fence = False

    for line in lines:
        if FENCE_RE.match(line):
            in_fence = not in_fence
            target = current_body if current_name is not None else preamble
            target.append(line)
            continue
        if not in_fence:
            section_match = SECTION_RE.match(line)
            if section_match:
                if current_name is not None:
                    sections.append((current_name, current_body))
                current_name = section_match.group(1).strip()
                current_body = []
                continue
        target = current_body if current_name is not None else preamble
        target.append(line)
    if current_name is not None:
        sections.append((current_name, current_body))

    status_sections = [(n, b) for n, b in sections if n in VALID_SECTIONS]
    other_sections = [
        (n, _trim_block(b)) for n, b in sections if n not in VALID_SECTIONS
    ]

    rank = {name: index for index, name in enumerate(VALID_SECTIONS)}
    status_sections.sort(key=lambda pair: rank[pair[0]])

    fixed_status: list[tuple[str, list[str]]] = []
    for name, body in status_sections:
        if name == "Ready":
            # Detect split layout by presence of link lines.
            link_indices = [
                i for i, line in enumerate(body) if SPLIT_LINK_RE.match(line)
            ]
            if link_indices:
                non_link = [
                    line for i, line in enumerate(body) if i not in set(link_indices)
                ]
                links = [body[i] for i in link_indices]
                links.sort(key=_split_link_sort_key)
                pre = _trim_block(non_link)
                new_body = list(pre)
                if pre and links:
                    new_body.append("")
                new_body.extend(links)
                fixed_status.append((name, new_body))
            else:
                pre, items = _split_section_body(body)
                items.sort(key=_item_sort_key)
                pre = _trim_block(pre)
                trimmed_items = [_trim_block(it) for it in items]
                new_body = list(pre)
                if pre and trimmed_items:
                    new_body.append("")
                for index, it in enumerate(trimmed_items):
                    if index > 0:
                        new_body.append("")
                    new_body.extend(it)
                fixed_status.append((name, new_body))
        else:
            fixed_status.append((name, _trim_block(body)))

    out: list[str] = list(_trim_block(preamble))
    all_sections = other_sections + fixed_status
    for name, body in all_sections:
        if out:
            out.append("")
        out.append(f"## {name}")
        if body:
            out.append("")
            out.extend(body)
    return "\n".join(out) + "\n"


_FINDING_WITH_ID_RE = re.compile(
    r"^(?P<id>[A-Z][A-Z0-9]*-\d{3,})\s+line\s+(?P<line>\d+):\s*(?P<message>.*)$"
)
_FINDING_LINE_ONLY_RE = re.compile(
    r"^line\s+(?P<line>\d+):\s*(?P<message>.*)$"
)


def _parse_finding(
    severity: str, message: str, file_path: Path
) -> dict[str, Any]:
    match = _FINDING_WITH_ID_RE.match(message)
    if match:
        return {
            "file": str(file_path),
            "severity": severity,
            "item_id": match.group("id"),
            "line": int(match.group("line")),
            "message": match.group("message").strip(),
        }
    match = _FINDING_LINE_ONLY_RE.match(message)
    if match:
        return {
            "file": str(file_path),
            "severity": severity,
            "item_id": None,
            "line": int(match.group("line")),
            "message": match.group("message").strip(),
        }
    return {
        "file": str(file_path),
        "severity": severity,
        "item_id": None,
        "line": None,
        "message": message,
    }


def collect(
    path: Path,
    allow_done: bool,
    strict_sections: bool,
    strict: bool = False,
    max_inbox_size: int = DEFAULT_MAX_INBOX_SIZE,
    max_inbox_age_days: int = DEFAULT_MAX_INBOX_AGE_DAYS,
) -> tuple[list[str], list[str], int]:
    if strict:
        strict_sections = True
    layout = detect_layout(path)
    warnings: list[str] = []
    errors: list[str] = []
    if layout == "split":
        items, sections, split_errors = parse_split_queue(path)
        errors.extend(split_errors)
    else:
        text = path.read_text(encoding="utf-8")
        items, sections = parse_items(text)
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

    inbox_errors, inbox_warnings = validate_inbox(
        items, max_inbox_size, max_inbox_age_days
    )
    errors.extend(inbox_errors)
    warnings.extend(inbox_warnings)

    if not items:
        warnings.append("no queue items found")

    return errors, warnings, len(items)


def migrate_to_split(queue_path: Path) -> tuple[int, list[str]]:
    """One-way migrate a single-file queue to the split (index + items/) layout.

    Returns (items_written, errors). Writes per-item files under
    ``items/`` next to the queue file, then rewrites the queue file as
    an index of checkbox links. Refuses to overwrite an existing
    items/ directory.
    """
    errors: list[str] = []
    if detect_layout(queue_path) == "split":
        return 0, [f"{queue_path}: already in split layout; nothing to do"]

    text = queue_path.read_text(encoding="utf-8")
    items, sections = parse_items(text)

    items_dir = queue_path.parent / "items"
    if items_dir.exists():
        return 0, [
            f"{items_dir}: directory already exists; refusing to overwrite. Move or remove it first."
        ]

    items_dir.mkdir(parents=True)
    written = 0
    for item in items:
        if item.section not in VALID_SECTIONS:
            continue
        fields = extract_fields(item)
        # Strip the inline field block from the body so it lives only in frontmatter.
        stripped_body = _strip_inline_fields(item.body)
        # Reconstruct the item file: frontmatter + heading + body.
        frontmatter_lines = ["---"]
        for key in ("type", "priority", "created", "area"):
            frontmatter_lines.append(f"{key}: {fields.get(key.capitalize(), '')}")
        frontmatter_lines.append(f"id: {item.id}")
        frontmatter_lines.append("deps: []")
        frontmatter_lines.append("---")
        frontmatter_lines.append("")
        frontmatter_lines.append(f"### {item.id} {item.title}")
        frontmatter_lines.append("")
        frontmatter_lines.extend(stripped_body)
        contents = "\n".join(frontmatter_lines).rstrip() + "\n"
        (items_dir / f"{item.id}.md").write_text(contents, encoding="utf-8")
        written += 1

    # Build the index. Preserve any preamble before the first section.
    preamble = _extract_preamble(text)
    out_lines: list[str] = preamble[:]
    if preamble:
        out_lines.append("")
    items_by_section: dict[str, list[Item]] = {name: [] for name in VALID_SECTIONS}
    for item in items:
        if item.section in items_by_section:
            items_by_section[item.section].append(item)
    for section_name in VALID_SECTIONS:
        if out_lines:
            out_lines.append("")
        out_lines.append(f"## {section_name}")
        out_lines.append("")
        section_items = items_by_section[section_name]
        if not section_items:
            out_lines.append("_None._")
            continue
        if section_name == "Ready":
            section_items = sorted(section_items, key=lambda i: _item_sort_key([f"### {i.id} {i.title}"] + i.body))
        for item in section_items:
            fields = extract_fields(item)
            tag = f"P{fields.get('Priority', '')[1:]} {fields.get('Type', '')}".strip()
            out_lines.append(
                f"- [ ] [{item.id} {item.title}](items/{item.id}.md) — {tag}"
            )

    queue_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    return written, errors


def _strip_inline_fields(body: list[str]) -> list[str]:
    """Drop the `- **Type**: ...` field block (and the blank line that follows) from a body."""
    output: list[str] = []
    skipping = True
    for line in body:
        if skipping and FIELD_RE.match(line):
            continue
        if skipping and line.strip() == "":
            # Stop skipping after the first blank that follows the field block.
            if output:
                output.append(line)
            skipping = False
            continue
        skipping = False
        output.append(line)
    # Trim leading blanks
    while output and output[0].strip() == "":
        output.pop(0)
    return output


def _extract_preamble(text: str) -> list[str]:
    """Lines before the first ## section, trailing blanks stripped."""
    out: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            out.append(line)
            continue
        if not in_fence and SECTION_RE.match(line):
            break
        out.append(line)
    while out and out[-1].strip() == "":
        out.pop()
    return out


def validate(
    path: Path,
    allow_done: bool,
    strict_sections: bool,
    strict: bool = False,
    max_inbox_size: int = DEFAULT_MAX_INBOX_SIZE,
    max_inbox_age_days: int = DEFAULT_MAX_INBOX_AGE_DAYS,
) -> int:
    errors, warnings, item_count = collect(
        path,
        allow_done,
        strict_sections,
        strict=strict,
        max_inbox_size=max_inbox_size,
        max_inbox_age_days=max_inbox_age_days,
    )

    for message in warnings:
        print(f"WARN: {message}", file=sys.stderr)
    for message in errors:
        print(f"ERROR: {message}", file=sys.stderr)

    if errors:
        print(f"Queue validation failed: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1

    print(f"Queue validation passed: {item_count} item(s), {len(warnings)} warning(s)")
    return 0


def validate_to_json(
    path: Path,
    allow_done: bool,
    strict_sections: bool,
    strict: bool = False,
) -> tuple[dict[str, Any], int]:
    errors, warnings, item_count = collect(
        path, allow_done, strict_sections, strict=strict
    )
    findings = [_parse_finding("error", m, path) for m in errors] + [
        _parse_finding("warning", m, path) for m in warnings
    ]
    payload = {
        "file": str(path),
        "item_count": item_count,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "findings": findings,
    }
    return payload, 1 if errors else 0


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
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Canonicalize section order, sort Ready by priority/date/id, and normalize trailing whitespace. Rewrites the file in place.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit findings as one JSON document on stdout instead of human-readable lines.",
    )
    parser.add_argument(
        "--max-inbox-size",
        type=int,
        default=DEFAULT_MAX_INBOX_SIZE,
        help=f"Warn when Inbox holds more than N items (default {DEFAULT_MAX_INBOX_SIZE}, 0 disables).",
    )
    parser.add_argument(
        "--max-inbox-age-days",
        type=int,
        default=DEFAULT_MAX_INBOX_AGE_DAYS,
        help=f"Warn when an Inbox item is older than N days (default {DEFAULT_MAX_INBOX_AGE_DAYS}, 0 disables).",
    )
    parser.add_argument(
        "--migrate-to-split",
        action="store_true",
        help="One-way migration from single-file layout to split (index + items/) layout. Refuses to overwrite an existing items/ directory.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="With --fix, exit non-zero if the file would change instead of writing.",
    )
    args = parser.parse_args()

    if args.migrate_to_split:
        worst = 0
        for queue_file in args.queue_files:
            if not queue_file.exists():
                print(f"ERROR: file not found: {queue_file}", file=sys.stderr)
                worst = max(worst, 2)
                continue
            written, errors = migrate_to_split(queue_file)
            for message in errors:
                print(f"ERROR: {message}", file=sys.stderr)
            if errors:
                worst = max(worst, 1)
                continue
            print(f"{queue_file}: migrated {written} item(s) to split layout")
        return worst

    if args.fix:
        worst = 0
        for queue_file in args.queue_files:
            if not queue_file.exists():
                print(f"ERROR: file not found: {queue_file}", file=sys.stderr)
                worst = max(worst, 2)
                continue
            original = queue_file.read_text(encoding="utf-8")
            fixed = fix_queue(original)
            if original == fixed:
                print(f"{queue_file}: already canonical")
                continue
            if args.check:
                print(f"{queue_file}: would rewrite (run without --check to apply)")
                worst = max(worst, 1)
                continue
            queue_file.write_text(fixed, encoding="utf-8")
            print(f"{queue_file}: rewrote")
        return worst

    if args.json:
        payloads: list[dict[str, Any]] = []
        worst = 0
        for queue_file in args.queue_files:
            if not queue_file.exists():
                payloads.append(
                    {
                        "file": str(queue_file),
                        "item_count": 0,
                        "error_count": 1,
                        "warning_count": 0,
                        "findings": [
                            {
                                "file": str(queue_file),
                                "severity": "error",
                                "item_id": None,
                                "line": None,
                                "message": f"file not found: {queue_file}",
                            }
                        ],
                    }
                )
                worst = max(worst, 2)
                continue
            payload, code = validate_to_json(
                queue_file,
                args.allow_done,
                args.strict_sections,
                strict=args.strict,
            )
            payloads.append(payload)
            worst = max(worst, code)
        print(json.dumps({"files": payloads}, indent=2))
        return worst

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
            max_inbox_size=args.max_inbox_size,
            max_inbox_age_days=args.max_inbox_age_days,
        )
        worst = max(worst, result)
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
