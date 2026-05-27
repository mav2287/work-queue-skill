import contextlib
import io
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "work-queue" / "scripts" / "validate_queue.py"
spec = importlib.util.spec_from_file_location("validate_queue", SCRIPT)
validate_queue = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["validate_queue"] = validate_queue
spec.loader.exec_module(validate_queue)


def queue_with_ready(body: str) -> str:
    return f"""# Work Queue

## In progress

_None._

## Blocked

_None._

## Ready

{body}

## Needs refinement

_None._

## Inbox

_None._

## Done

_None._

## Cancelled

_None._
"""


def item(item_id: str, priority: str = "P1", extra_notes: str = "") -> str:
    return f"""### {item_id} Fix sample bug

  - **Type**: bug
  - **Priority**: {priority}
  - **Created**: 2026-05-23
  - **Area**: tests

**Problem / Want**
Sample problem.

**Acceptance**
**MUST**
  - [ ] Sample criterion.

**Notes**
Sample notes.
{extra_notes}
"""


class ValidateQueueTests(unittest.TestCase):
    def validate_text(self, text: str, **kwargs) -> int:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "WORK_QUEUE.md"
            path.write_text(text, encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
                io.StringIO()
            ):
                return validate_queue.validate(path, **kwargs)

    def validate_capture(self, text: str, **kwargs) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "WORK_QUEUE.md"
            path.write_text(text, encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
                stderr
            ):
                code = validate_queue.validate(path, **kwargs)
        return code, stderr.getvalue()

    def test_duplicate_id_fails(self):
        text = queue_with_ready(item("WQ-001") + "\n" + item("WQ-001"))
        code, err = self.validate_capture(
            text, allow_done=False, strict_sections=True
        )
        self.assertEqual(code, 1)
        self.assertIn("duplicate ID", err)

    def test_missing_type_field_fails(self):
        bad = item("WQ-001").replace("  - **Type**: bug\n", "")
        code, err = self.validate_capture(
            queue_with_ready(bad), allow_done=False, strict_sections=True
        )
        self.assertEqual(code, 1)
        self.assertIn("missing field 'Type'", err)

    def test_invalid_type_fails(self):
        bad = item("WQ-001").replace("**Type**: bug", "**Type**: spaghetti")
        code, err = self.validate_capture(
            queue_with_ready(bad), allow_done=False, strict_sections=True
        )
        self.assertEqual(code, 1)
        self.assertIn("invalid Type 'spaghetti'", err)

    def test_invalid_priority_fails(self):
        bad = item("WQ-001").replace("**Priority**: P1", "**Priority**: P9")
        code, err = self.validate_capture(
            queue_with_ready(bad), allow_done=False, strict_sections=True
        )
        self.assertEqual(code, 1)
        self.assertIn("invalid Priority 'P9'", err)

    def test_malformed_created_fails(self):
        bad = item("WQ-001").replace(
            "**Created**: 2026-05-23", "**Created**: yesterday"
        )
        code, err = self.validate_capture(
            queue_with_ready(bad), allow_done=False, strict_sections=True
        )
        self.assertEqual(code, 1)
        self.assertIn("Created must be YYYY-MM-DD", err)

    def test_blocked_without_marker_fails(self):
        blocked = item("WQ-001").replace(
            "### WQ-001 Fix sample bug", "### WQ-001 Investigate"
        )
        text = queue_with_ready("_None._").replace(
            "## Blocked\n\n_None._",
            "## Blocked\n\n" + blocked,
        )
        code, err = self.validate_capture(
            text, allow_done=False, strict_sections=True
        )
        self.assertEqual(code, 1)
        self.assertIn("Blocked item needs", err)

    def test_done_without_outcome_warns(self):
        done_body = """### WQ-001 Fix sample bug

  - **Type**: bug
  - **Priority**: P1
  - **Created**: 2026-05-23
  - **Area**: tests

**Problem / Want**
Sample.

**Acceptance**
- [x] Done.

**Notes**
Sample.

**Verification**
- ran the thing: passed
"""
        text = queue_with_ready("_None._").replace(
            "## Done\n\n_None._",
            "## Done\n\n" + done_body,
        )
        code, err = self.validate_capture(
            text, allow_done=True, strict_sections=True
        )
        self.assertEqual(code, 0)
        self.assertIn("Outcome", err)

    def test_done_with_unchecked_acceptance_fails(self):
        done_body = item("WQ-001") + "\n**Verification**\n- ok\n"
        text = queue_with_ready("_None._").replace(
            "## Done\n\n_None._",
            "## Done\n\n" + done_body,
        )
        code, err = self.validate_capture(
            text, allow_done=True, strict_sections=True
        )
        self.assertEqual(code, 1)
        self.assertIn("unchecked acceptance boxes", err)

    def test_missing_problem_section_fails(self):
        bad = item("WQ-001").replace("**Problem / Want**", "**Problem**")
        code, err = self.validate_capture(
            queue_with_ready(bad), allow_done=False, strict_sections=True
        )
        self.assertEqual(code, 1)
        self.assertIn("missing Problem / Want", err)

    def test_unknown_section_fails(self):
        text = queue_with_ready(item("WQ-001")) + "\n## Bogus\n\n_None._\n"
        code, err = self.validate_capture(
            text, allow_done=False, strict_sections=False
        )
        self.assertEqual(code, 1)
        self.assertIn("unknown section 'Bogus'", err)

    def test_duplicate_section_fails(self):
        text = queue_with_ready(item("WQ-001")) + "\n## Ready\n\n_None._\n"
        code, err = self.validate_capture(
            text, allow_done=False, strict_sections=True
        )
        self.assertEqual(code, 1)
        self.assertIn("duplicate section 'Ready'", err)

    def test_empty_queue_warns(self):
        text = """# Work Queue

## In progress

_None._

## Blocked

_None._

## Ready

_None._

## Needs refinement

_None._

## Inbox

_None._

## Done

_None._

## Cancelled

_None._
"""
        code, err = self.validate_capture(
            text, allow_done=False, strict_sections=True
        )
        self.assertEqual(code, 0)
        self.assertIn("no queue items found", err)

    def test_file_not_found_returns_two(self):
        argv = sys.argv
        sys.argv = ["validate_queue.py", "/nonexistent/path/WORK_QUEUE.md"]
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
                io.StringIO()
            ):
                code = validate_queue.main()
        finally:
            sys.argv = argv
        self.assertEqual(code, 2)

    def test_fenced_queue_snippet_does_not_create_items_or_sections(self):
        fenced = """```markdown
## Ready

### WQ-999 Ignore fenced item

- [ ] Ignore this.
```
"""
        text = queue_with_ready(item("WQ-001", extra_notes=fenced))
        self.assertEqual(
            self.validate_text(text, allow_done=False, strict_sections=True), 0
        )

    def test_emphasized_acceptance_callout_does_not_end_acceptance(self):
        text = queue_with_ready(item("WQ-001"))
        self.assertEqual(
            self.validate_text(text, allow_done=False, strict_sections=True), 0
        )

    def test_ready_items_must_be_priority_sorted(self):
        text = queue_with_ready(item("WQ-001", "P2") + "\n" + item("WQ-002", "P1"))
        self.assertEqual(
            self.validate_text(text, allow_done=False, strict_sections=True), 1
        )

    def test_done_without_verification_warns_default_errors_strict(self):
        done_item = """### WQ-009 Old fix

- **Type**: bug
- **Priority**: P1
- **Created**: 2026-05-23
- **Area**: tests

**Problem / Want**
Was fixed.

**Acceptance**
- [x] Fixed.

**Notes**
Done without a Verification heading.
"""
        text = queue_with_ready(item("WQ-001")).replace(
            "## Done\n\n_None._",
            "## Done\n\n" + done_item,
        )
        self.assertEqual(
            self.validate_text(
                text, allow_done=True, strict_sections=True
            ),
            0,
        )
        self.assertEqual(
            self.validate_text(
                text, allow_done=True, strict_sections=True, strict=True
            ),
            1,
        )

    def test_future_created_date_warns(self):
        future_item = item("WQ-001").replace(
            "**Created**: 2026-05-23", "**Created**: 2099-12-31"
        )
        text = queue_with_ready(future_item)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "WORK_QUEUE.md"
            path.write_text(text, encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
                stderr
            ):
                code = validate_queue.validate(
                    path, allow_done=False, strict_sections=True
                )
        self.assertEqual(code, 0)
        self.assertIn("future", stderr.getvalue())

    def test_ancient_created_date_warns(self):
        ancient_item = item("WQ-001").replace(
            "**Created**: 2026-05-23", "**Created**: 2010-01-01"
        )
        text = queue_with_ready(ancient_item)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "WORK_QUEUE.md"
            path.write_text(text, encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
                stderr
            ):
                code = validate_queue.validate(
                    path, allow_done=False, strict_sections=True
                )
        self.assertEqual(code, 0)
        self.assertIn("before 2020", stderr.getvalue())

    def test_duplicate_titles_warn(self):
        text = queue_with_ready(item("WQ-001") + "\n" + item("WQ-002"))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "WORK_QUEUE.md"
            path.write_text(text, encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
                stderr
            ):
                code = validate_queue.validate(
                    path, allow_done=False, strict_sections=True
                )
        self.assertEqual(code, 0)
        self.assertIn("duplicate title", stderr.getvalue())

    def test_json_output_schema(self):
        invalid_item = item("WQ-001").replace(
            "**Priority**: P1", "**Priority**: P9"
        )
        text = queue_with_ready(invalid_item)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "WORK_QUEUE.md"
            path.write_text(text, encoding="utf-8")
            payload, code = validate_queue.validate_to_json(
                path, allow_done=False, strict_sections=True
            )
        self.assertEqual(code, 1)
        self.assertEqual(payload["file"], str(path))
        self.assertEqual(payload["error_count"], 1)
        self.assertEqual(payload["item_count"], 1)
        self.assertEqual(len(payload["findings"]), 1)
        finding = payload["findings"][0]
        self.assertEqual(finding["severity"], "error")
        self.assertEqual(finding["item_id"], "WQ-001")
        self.assertIsInstance(finding["line"], int)
        self.assertIn("Priority", finding["message"])

    def test_json_cli_emits_one_document(self):
        text = queue_with_ready(item("WQ-001"))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "WORK_QUEUE.md"
            path.write_text(text, encoding="utf-8")
            argv = sys.argv
            sys.argv = ["validate_queue.py", "--strict-sections", "--json", str(path)]
            stdout = io.StringIO()
            try:
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(
                    io.StringIO()
                ):
                    code = validate_queue.main()
            finally:
                sys.argv = argv
        self.assertEqual(code, 0)
        import json as _json
        doc = _json.loads(stdout.getvalue())
        self.assertEqual(len(doc["files"]), 1)
        self.assertEqual(doc["files"][0]["item_count"], 1)

    def test_fix_sorts_ready_by_priority_then_id(self):
        text = queue_with_ready(
            item("WQ-002", "P2") + "\n" + item("WQ-001", "P1") + "\n" + item("WQ-003", "P0")
        )
        fixed = validate_queue.fix_queue(text)
        ready_block = fixed[
            fixed.index("## Ready"):fixed.index("## Needs refinement")
        ]
        self.assertLess(ready_block.index("WQ-003"), ready_block.index("WQ-001"))
        self.assertLess(ready_block.index("WQ-001"), ready_block.index("WQ-002"))

    def test_fix_puts_status_sections_in_canonical_order(self):
        # Build a file where Done appears before In progress.
        scrambled = """# Work Queue

## Done

_None._

## In progress

_None._

## Ready

""" + item("WQ-001") + """

## Blocked

_None._

## Needs refinement

_None._

## Inbox

_None._

## Cancelled

_None._
"""
        fixed = validate_queue.fix_queue(scrambled)
        ip = fixed.index("## In progress")
        ready = fixed.index("## Ready")
        done = fixed.index("## Done")
        self.assertLess(ip, ready)
        self.assertLess(ready, done)

    def test_fix_check_returns_one_when_changes_needed(self):
        text = queue_with_ready(item("WQ-002", "P2") + "\n" + item("WQ-001", "P1"))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "WORK_QUEUE.md"
            path.write_text(text, encoding="utf-8")
            argv = sys.argv
            sys.argv = ["validate_queue.py", "--fix", "--check", str(path)]
            try:
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
                    io.StringIO()
                ):
                    code = validate_queue.main()
            finally:
                sys.argv = argv
            self.assertEqual(code, 1)
            # File must not have been modified
            self.assertEqual(path.read_text(encoding="utf-8"), text)

    def test_split_layout_detected_and_parses(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            index_path = tmp_path / "WORK_QUEUE.md"
            items_dir = tmp_path / "items"
            items_dir.mkdir()
            (items_dir / "WQ-001.md").write_text(
                """---
id: WQ-001
type: bug
priority: P1
created: 2026-05-23
area: tests
deps: []
---

### WQ-001 Fix sample bug

**Problem / Want**
Sample.

**Acceptance**
- [ ] Sample.

**Notes**
Sample.
""",
                encoding="utf-8",
            )
            index_path.write_text(
                """# Work Queue

## In progress

_None._

## Blocked

_None._

## Ready

- [ ] [WQ-001 Fix sample bug](items/WQ-001.md) — P1 bug

## Needs refinement

_None._

## Inbox

_None._

## Done

_None._

## Cancelled

_None._
""",
                encoding="utf-8",
            )
            self.assertEqual(validate_queue.detect_layout(index_path), "split")
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
                io.StringIO()
            ):
                code = validate_queue.validate(
                    index_path, allow_done=False, strict_sections=True
                )
        self.assertEqual(code, 0)

    def test_split_layout_dangling_link_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "items").mkdir()
            # Touch a sentinel item so detect_layout returns "split"
            (tmp_path / "items" / "WQ-002.md").write_text(
                """---
id: WQ-002
type: bug
priority: P1
created: 2026-05-23
area: tests
deps: []
---

### WQ-002 Real item

**Problem / Want**
Sample.

**Acceptance**
- [ ] Sample.

**Notes**
Sample.
""",
                encoding="utf-8",
            )
            index_path = tmp_path / "WORK_QUEUE.md"
            index_path.write_text(
                """# Work Queue

## In progress

_None._

## Blocked

_None._

## Ready

- [ ] [WQ-001 Missing](items/WQ-001.md) — P1 bug
- [ ] [WQ-002 Real item](items/WQ-002.md) — P1 bug

## Needs refinement

_None._

## Inbox

_None._

## Done

_None._

## Cancelled

_None._
""",
                encoding="utf-8",
            )
            stderr = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
                stderr
            ):
                code = validate_queue.validate(
                    index_path, allow_done=False, strict_sections=True
                )
        self.assertEqual(code, 1)
        self.assertIn("missing file WQ-001.md", stderr.getvalue())

    def test_fix_sorts_split_layout_index_links(self):
        body = """# Work Queue

## In progress

_None._

## Blocked

_None._

## Ready

- [ ] [WQ-002 Item B](items/WQ-002.md) — P2 feature
- [ ] [WQ-001 Item A](items/WQ-001.md) — P1 bug

## Needs refinement

_None._

## Inbox

_None._

## Done

_None._

## Cancelled

_None._
"""
        fixed = validate_queue.fix_queue(body)
        ready = fixed[fixed.index("## Ready"):fixed.index("## Needs refinement")]
        self.assertLess(ready.index("WQ-001"), ready.index("WQ-002"))

    def test_migrate_to_split_round_trips_item_content(self):
        single = queue_with_ready(item("WQ-001") + "\n" + item("WQ-002", "P2"))
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            path = tmp_path / "WORK_QUEUE.md"
            path.write_text(single, encoding="utf-8")
            written, errors = validate_queue.migrate_to_split(path)
            self.assertEqual(errors, [])
            self.assertEqual(written, 2)
            self.assertEqual(validate_queue.detect_layout(path), "split")
            self.assertTrue((tmp_path / "items" / "WQ-001.md").exists())
            self.assertTrue((tmp_path / "items" / "WQ-002.md").exists())
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
                io.StringIO()
            ):
                code = validate_queue.validate(
                    path, allow_done=False, strict_sections=True
                )
        self.assertEqual(code, 0)

    def test_migrate_refuses_to_overwrite_existing_items_dir(self):
        single = queue_with_ready(item("WQ-001"))
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            path = tmp_path / "WORK_QUEUE.md"
            path.write_text(single, encoding="utf-8")
            (tmp_path / "items").mkdir()
            written, errors = validate_queue.migrate_to_split(path)
        self.assertEqual(written, 0)
        self.assertTrue(any("refusing to overwrite" in e for e in errors))

    def test_fix_is_idempotent(self):
        text = queue_with_ready(item("WQ-001", "P0") + "\n" + item("WQ-002", "P1"))
        once = validate_queue.fix_queue(text)
        twice = validate_queue.fix_queue(once)
        self.assertEqual(once, twice)

    def test_main_accepts_multiple_files_and_fails_if_any_fail(self):
        good = queue_with_ready(item("WQ-001"))
        bad = queue_with_ready(
            item("WQ-001").replace("**Priority**: P1", "**Priority**: P9")
        )
        with tempfile.TemporaryDirectory() as tmp:
            good_path = Path(tmp) / "good.md"
            bad_path = Path(tmp) / "bad.md"
            good_path.write_text(good, encoding="utf-8")
            bad_path.write_text(bad, encoding="utf-8")

            argv = sys.argv
            sys.argv = ["validate_queue.py", str(good_path), str(bad_path)]
            try:
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
                    io.StringIO()
                ):
                    code = validate_queue.main()
            finally:
                sys.argv = argv
        self.assertEqual(code, 1)

    def test_main_accepts_multiple_good_files(self):
        good = queue_with_ready(item("WQ-001"))
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / "a.md"
            b = Path(tmp) / "b.md"
            a.write_text(good, encoding="utf-8")
            b.write_text(good, encoding="utf-8")
            argv = sys.argv
            sys.argv = ["validate_queue.py", str(a), str(b)]
            try:
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
                    io.StringIO()
                ):
                    code = validate_queue.main()
            finally:
                sys.argv = argv
        self.assertEqual(code, 0)

    def test_inbox_over_threshold_warns(self):
        items = "\n".join(item(f"WQ-{n:03d}") for n in range(1, 5))
        text = queue_with_ready("_None._").replace(
            "## Inbox\n\n_None._",
            "## Inbox\n\n" + items,
        )
        code, err = self.validate_capture(
            text,
            allow_done=False,
            strict_sections=True,
            max_inbox_size=2,
            max_inbox_age_days=0,
        )
        self.assertEqual(code, 0)
        self.assertIn("Inbox holds 4 items", err)

    def test_inbox_stale_item_warns(self):
        old = item("WQ-001").replace(
            "**Created**: 2026-05-23", "**Created**: 2025-01-01"
        )
        text = queue_with_ready("_None._").replace(
            "## Inbox\n\n_None._",
            "## Inbox\n\n" + old,
        )
        code, err = self.validate_capture(
            text,
            allow_done=False,
            strict_sections=True,
            max_inbox_size=0,
            max_inbox_age_days=30,
        )
        self.assertEqual(code, 0)
        self.assertIn("Inbox item has been waiting", err)

    def test_blocked_on_unknown_id_fails(self):
        blocked_body = """### WQ-002 Investigate flaky test

  - **Type**: investigation
  - **Priority**: P2
  - **Created**: 2026-05-23
  - **Area**: tests

**Problem / Want**
Need an external answer.

**Acceptance**
  - [ ] Decision recorded.

**Notes**
Local checks not yet performed.

**Blocked on**: WQ-999 to land first
"""
        text = queue_with_ready(item("WQ-001")).replace(
            "## Blocked\n\n_None._",
            "## Blocked\n\n" + blocked_body,
        )
        self.assertEqual(
            self.validate_text(text, allow_done=False, strict_sections=True), 1
        )

    def test_blocked_on_resolved_id_passes(self):
        blocked_body = """### WQ-002 Investigate flaky test

  - **Type**: investigation
  - **Priority**: P2
  - **Created**: 2026-05-23
  - **Area**: tests

**Problem / Want**
Need WQ-001 to land first.

**Acceptance**
  - [ ] Decision recorded.

**Notes**
Local checks not yet performed.

**Blocked on**: WQ-001 to land first
"""
        text = queue_with_ready(item("WQ-001")).replace(
            "## Blocked\n\n_None._",
            "## Blocked\n\n" + blocked_body,
        )
        self.assertEqual(
            self.validate_text(text, allow_done=False, strict_sections=True), 0
        )

    def test_single_in_progress_passes(self):
        text = queue_with_ready("_None._").replace(
            "## In progress\n\n_None._",
            "## In progress\n\n" + item("WQ-001"),
        )
        self.assertEqual(
            self.validate_text(text, allow_done=False, strict_sections=True), 0
        )

    def test_multiple_in_progress_warns_by_default_errors_in_strict(self):
        two = item("WQ-001") + "\n" + item("WQ-002")
        text = queue_with_ready("_None._").replace(
            "## In progress\n\n_None._",
            "## In progress\n\n" + two,
        )
        self.assertEqual(
            self.validate_text(text, allow_done=False, strict_sections=True), 0
        )
        self.assertEqual(
            self.validate_text(
                text, allow_done=False, strict_sections=True, strict=True
            ),
            1,
        )

    def test_template_pasted_verbatim_into_ready_fails(self):
        template_path = (
            ROOT / "work-queue" / "templates" / "item.md"
        )
        template_body = template_path.read_text(encoding="utf-8")
        text = queue_with_ready(template_body)
        self.assertEqual(
            self.validate_text(text, allow_done=False, strict_sections=True), 1
        )

    def test_placeholder_id_warns_even_when_otherwise_valid(self):
        text = queue_with_ready(item("WQ-000"))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "WORK_QUEUE.md"
            path.write_text(text, encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
                stderr
            ):
                code = validate_queue.validate(
                    path, allow_done=False, strict_sections=True
                )
        self.assertEqual(code, 0)
        self.assertIn("placeholder", stderr.getvalue())

    def test_missing_sections_warn_by_default_but_fail_when_strict(self):
        text = """# Work Queue

## Ready

""" + item("WQ-001")
        self.assertEqual(
            self.validate_text(text, allow_done=False, strict_sections=False), 0
        )
        self.assertEqual(
            self.validate_text(text, allow_done=False, strict_sections=True), 1
        )


if __name__ == "__main__":
    unittest.main()
