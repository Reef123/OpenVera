#!/usr/bin/env python3
"""Tests for curate-mode.py's deterministic subcommands and the size-cap
checker in vera_config.

check_file_sizes backs three enforcement points (doctor.py, /doc-sync Step 8,
/curate's MEMORY.md hard rule). MEMORY.md over its cap means silent
truncation at load time, so a checker regression is invisible context loss.

Stdlib unittest, runs on macOS system Python 3.9.6:

    python3 -m unittest discover -s tests
    python3 tests/test_curate_mode.py
"""
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS_DIR = _REPO_ROOT / "vera-system" / "scripts"
sys.path.insert(0, str(_SCRIPTS_DIR))

import vera_config  # noqa: E402


def _write_lines(path, n):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(f"line {i}" for i in range(n)))


class CheckFileSizesTests(unittest.TestCase):
    def test_empty_root_reports_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(vera_config.check_file_sizes(Path(tmp)), [])

    def test_file_under_cap_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_lines(root / "vera-system" / "state.md", 50)
            self.assertEqual(vera_config.check_file_sizes(root), [])

    def test_file_over_cap_reported_with_count_and_cap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_lines(root / "vera-system" / "memory" / "MEMORY.md", 250)
            over = vera_config.check_file_sizes(root)
            self.assertEqual(len(over), 1)
            rel, lines, cap = over[0]
            self.assertEqual(rel, "vera-system/memory/MEMORY.md")
            self.assertEqual(lines, 250)
            self.assertEqual(cap, 200)

    def test_file_exactly_at_cap_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_lines(root / "vera-system" / "state.md", 100)
            self.assertEqual(vera_config.check_file_sizes(root), [])

    def test_multiple_breaches_all_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_lines(root / "vera-system" / "state.md", 150)
            _write_lines(root / "vera-system" / "memory" / "lessons.md", 200)
            over = vera_config.check_file_sizes(root)
            self.assertEqual(len(over), 2)

    def test_lessons_md_is_capped(self):
        self.assertIn("vera-system/memory/lessons.md", vera_config.SIZE_THRESHOLDS)


class CurateModeCliTests(unittest.TestCase):
    """The CLI runs against the real repo, so assert output SHAPE, not values."""

    def _run(self, *args):
        return subprocess.run(
            [sys.executable, str(_SCRIPTS_DIR / "curate-mode.py"), *args],
            capture_output=True, text=True, timeout=30,
        )

    def test_age_prints_age_days(self):
        result = self._run("age")
        self.assertEqual(result.returncode, 0)
        self.assertRegex(result.stdout.strip(), r"^AGE_DAYS=-?\d+$")

    def test_sizes_prints_ok_or_over_lines(self):
        result = self._run("sizes")
        out = result.stdout.strip()
        if result.returncode == 0:
            self.assertEqual(out, "OK")
        else:
            self.assertEqual(result.returncode, 1)
            for line in out.splitlines():
                self.assertRegex(line, r"^OVER file=\S+ lines=\d+ cap=\d+$")


if __name__ == "__main__":
    sys.exit(unittest.main())
