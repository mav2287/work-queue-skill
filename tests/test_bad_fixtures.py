"""Run validate_queue.py against known-bad fixtures via subprocess.

Each fixture under tests/fixtures/bad/ is paired with an expected
substring in manifest.json. The test asserts the validator exits
non-zero and the expected substring appears on stderr. This catches
regressions where a refactor silently changes an error message or
suppresses a check entirely.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "work-queue" / "scripts" / "validate_queue.py"
GOOD_FIXTURES = ROOT / "work-queue" / "examples"
BAD_FIXTURES = ROOT / "tests" / "fixtures" / "bad"
MANIFEST = BAD_FIXTURES / "manifest.json"


class BadFixtureSuite(unittest.TestCase):
    def test_each_bad_fixture_fails_with_expected_message(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertTrue(manifest, "manifest must list at least one fixture")
        missing = [name for name in manifest if not (BAD_FIXTURES / name).exists()]
        self.assertFalse(missing, f"manifest lists missing fixtures: {missing}")
        for name, expected_substring in manifest.items():
            with self.subTest(fixture=name):
                result = subprocess.run(
                    [
                        sys.executable,
                        str(VALIDATOR),
                        str(BAD_FIXTURES / name),
                    ],
                    capture_output=True,
                    text=True,
                )
                self.assertNotEqual(
                    result.returncode,
                    0,
                    f"{name} should have failed validation but did not",
                )
                self.assertIn(expected_substring, result.stderr, name)

    def test_bundled_examples_pass_subprocess_smoke(self):
        for example in sorted(GOOD_FIXTURES.glob("*.md")):
            # Bundled examples include single-item snippets that aren't full
            # queue files, so skip ones without the canonical "## Ready"
            # header.
            text = example.read_text(encoding="utf-8")
            if "\n## Ready" not in text:
                continue
            with self.subTest(fixture=example.name):
                result = subprocess.run(
                    [
                        sys.executable,
                        str(VALIDATOR),
                        str(example),
                    ],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(
                    result.returncode,
                    0,
                    f"{example.name} failed: {result.stderr}",
                )


if __name__ == "__main__":
    unittest.main()
