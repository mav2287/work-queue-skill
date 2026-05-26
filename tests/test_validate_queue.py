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
