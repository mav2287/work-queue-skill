import contextlib
import io
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_skill.py"
spec = importlib.util.spec_from_file_location("validate_skill", SCRIPT)
validate_skill = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["validate_skill"] = validate_skill
spec.loader.exec_module(validate_skill)


def write_skill(root: Path, skill_body: str, openai_yaml: str | None = None) -> Path:
    skill_dir = root / "work-queue"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(skill_body, encoding="utf-8")
    agents = skill_dir / "agents"
    agents.mkdir()
    (agents / "openai.yaml").write_text(
        openai_yaml
        or """interface:
  display_name: "Work Queue"
  short_description: "Drain work queues."
  default_prompt: "Use $work-queue to drain the queue."
""",
        encoding="utf-8",
    )
    return skill_dir


class ValidateSkillTests(unittest.TestCase):
    def validate_silently(self, skill_dir: Path) -> int:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            io.StringIO()
        ):
            return validate_skill.validate(skill_dir)

    def test_frontmatter_links_are_not_checked_as_body_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = write_skill(
                Path(tmp),
                """---
name: work-queue
description: See [docs](missing.md) for details.
---

# Work Queue
""",
            )
            self.assertEqual(self.validate_silently(skill_dir), 0)

    def test_missing_referenced_script_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = write_skill(
                Path(tmp),
                """---
name: work-queue
description: Validate queues.
---

# Work Queue

```bash
python3 scripts/missing.py WORK_QUEUE.md
```
""",
            )
            self.assertEqual(self.validate_silently(skill_dir), 1)

    def test_commented_openai_keys_do_not_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = write_skill(
                Path(tmp),
                """---
name: work-queue
description: Validate queues.
---

# Work Queue
""",
                """interface:
  display_name: "Work Queue"
  # short_description: "Drain work queues."
  default_prompt: "Use $work-queue to drain the queue."
""",
            )
            self.assertEqual(self.validate_silently(skill_dir), 1)


if __name__ == "__main__":
    unittest.main()
