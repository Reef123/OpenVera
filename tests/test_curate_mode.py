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
import contextlib
import importlib.util
import io
import re
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS_DIR = _REPO_ROOT / "vera-system" / "scripts"
sys.path.insert(0, str(_SCRIPTS_DIR))

import vera_config  # noqa: E402

# curate-mode.py has a hyphenated name, so it can't be imported normally.
_spec = importlib.util.spec_from_file_location("curate_mode", str(_SCRIPTS_DIR / "curate-mode.py"))
curate_mode = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(curate_mode)


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


class PromotionLedgerTests(unittest.TestCase):
    """Pure-function tests against tempfile fixtures. The promotion ledger
    backs curate Step 6.6: a checker bug here either falsely fails a good
    pattern or silently validates a dead one."""

    TODAY = date(2026, 6, 10)

    def _ledger(self, root):
        return root / "vera-system" / "memory" / "promotions.tsv"

    def _lessons(self, root):
        return root / "vera-system" / "memory" / "lessons.md"

    def _write_lessons(self, root, lines):
        path = self._lessons(root)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Lessons\n\n" + "\n".join(lines) + "\n")

    def _seed(self, root, promoted_on, match="vite env cache", status="PROVISIONAL",
              status_date="-", note="-"):
        path = self._ledger(root)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            curate_mode.PROMOTIONS_HEADER + "\n"
            + f"{promoted_on}\t{match}\tBuild gotchas\t{status}\t{status_date}\t{note}\n"
        )

    # --- record ---

    def test_record_creates_file_with_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = self._ledger(Path(tmp))
            out = curate_mode.record_promotion(ledger, "vite env cache", "Build gotchas", self.TODAY)
            self.assertIn('RECORDED match="vite env cache"', out)
            lines = ledger.read_text().splitlines()
            self.assertEqual(lines[0], curate_mode.PROMOTIONS_HEADER)
            self.assertEqual(lines[1].split("\t")[3], "PROVISIONAL")

    def test_record_is_idempotent_for_same_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = self._ledger(Path(tmp))
            curate_mode.record_promotion(ledger, "vite env cache", "Build gotchas", self.TODAY)
            out = curate_mode.record_promotion(ledger, "Vite ENV Cache", "Build gotchas", self.TODAY)
            self.assertIn("EXISTS", out)
            self.assertEqual(len(ledger.read_text().splitlines()), 2)  # header + 1 row

    def test_sanitize_field_collapses_tabs_and_newlines(self):
        self.assertEqual(curate_mode.sanitize_field("a\tb\r\nc  "), "a b c")
        self.assertEqual(curate_mode.sanitize_field("\t\n"), "")

    # --- check ---

    def test_check_no_ledger_prints_no_promotions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out, changed = curate_mode.check_promotions(
                self._ledger(root), self._lessons(root), self.TODAY)
            self.assertEqual(out, ["NO_PROMOTIONS"])
            self.assertFalse(changed)

    def test_check_clean_under_window_stays_provisional(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed(root, "2026-06-05")
            self._write_lessons(root, ["- 2026-06-08 [build/app] something unrelated"])
            out, changed = curate_mode.check_promotions(
                self._ledger(root), self._lessons(root), self.TODAY)
            self.assertEqual(out, ['CLEAN match="vite env cache" days=5'])
            self.assertFalse(changed)

    def test_check_validates_after_fourteen_clean_days(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed(root, "2026-05-20")
            self._write_lessons(root, ["- 2026-06-01 [build/app] something unrelated"])
            out, changed = curate_mode.check_promotions(
                self._ledger(root), self._lessons(root), self.TODAY)
            self.assertEqual(out, ['VALIDATED match="vite env cache" days=21'])
            self.assertTrue(changed)
            self.assertIn("\tVALIDATED\t2026-06-10\t", self._ledger(root).read_text())

    def test_check_recurrence_flips_provisional_to_failed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed(root, "2026-06-01")
            self._write_lessons(root, [
                "- 2026-06-04 [build/app] hit the Vite env cache thing again",
                "- 2026-06-07 [build/web] vite env cache strikes twice",
            ])
            out, changed = curate_mode.check_promotions(
                self._ledger(root), self._lessons(root), self.TODAY)
            self.assertEqual(out, ['RECURRED match="vite env cache" n=2 since=2026-06-01 last=2026-06-07'])
            self.assertTrue(changed)
            row = self._ledger(root).read_text().splitlines()[1].split("\t")
            self.assertEqual(row[3], "FAILED")
            self.assertEqual(row[5], "recurred")

    def test_check_same_day_lesson_is_not_recurrence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed(root, "2026-06-08")
            self._write_lessons(root, ["- 2026-06-08 [build/app] vite env cache bit me"])
            out, changed = curate_mode.check_promotions(
                self._ledger(root), self._lessons(root), self.TODAY)
            self.assertEqual(out, ['CLEAN match="vite env cache" days=2'])
            self.assertFalse(changed)

    def test_check_validated_row_recurrence_flips_to_failed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed(root, "2026-05-01", status="VALIDATED", status_date="2026-05-20")
            self._write_lessons(root, ["- 2026-06-09 [build/app] vite env cache returned"])
            out, changed = curate_mode.check_promotions(
                self._ledger(root), self._lessons(root), self.TODAY)
            self.assertEqual(len(out), 1)
            self.assertIn("late=1", out[0])
            self.assertTrue(changed)
            row = self._ledger(root).read_text().splitlines()[1].split("\t")
            self.assertEqual(row[3], "FAILED")
            self.assertEqual(row[5], "recurred after validation")

    def test_check_failed_rows_resurface_every_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed(root, "2026-05-01", status="FAILED", status_date="2026-05-15", note="recurred")
            self._write_lessons(root, [])
            for _ in range(2):
                out, changed = curate_mode.check_promotions(
                    self._ledger(root), self._lessons(root), self.TODAY)
                self.assertEqual(out, ['FAILED match="vite env cache" since=2026-05-15'])
                self.assertFalse(changed)

    # --- malformed input ---

    def test_malformed_lesson_lines_skipped(self):
        self.assertIsNone(curate_mode.parse_lesson_line("undated prose line"))
        self.assertIsNone(curate_mode.parse_lesson_line("- 2026-13-99 impossible date"))
        self.assertIsNone(curate_mode.parse_lesson_line(""))
        parsed = curate_mode.parse_lesson_line("- 2026-06-09 [build/app] real lesson")
        self.assertEqual(parsed[0], date(2026, 6, 9))

    def test_garbage_ledger_row_preserved_verbatim_on_rewrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = self._ledger(root)
            ledger.parent.mkdir(parents=True, exist_ok=True)
            ledger.write_text(
                curate_mode.PROMOTIONS_HEADER + "\n"
                + "totally garbage line\n"
                + "2026-05-20\tvite env cache\tBuild gotchas\tPROVISIONAL\t-\t-\n"
            )
            self._write_lessons(root, [])
            with contextlib.redirect_stderr(io.StringIO()):
                out, changed = curate_mode.check_promotions(
                    ledger, self._lessons(root), self.TODAY)
            self.assertTrue(changed)  # the valid row validated (21 clean days)
            content = ledger.read_text().splitlines()
            self.assertIn("totally garbage line", content)

    def test_missing_lessons_file_counts_as_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed(root, "2026-06-05")
            with contextlib.redirect_stderr(io.StringIO()):
                out, changed = curate_mode.check_promotions(
                    self._ledger(root), self._lessons(root), self.TODAY)
            self.assertEqual(out, ['CLEAN match="vite env cache" days=5'])
            self.assertFalse(changed)


if __name__ == "__main__":
    sys.exit(unittest.main())
