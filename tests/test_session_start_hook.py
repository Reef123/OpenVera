#!/usr/bin/env python3
"""Tests for the SessionStart hook's curate-crash-tripwire helpers.

session-start.py Check 0 is the ONLY place the crash tripwire lives (see
openvera-v1.21-review-2026-07-03.md §8.1/§8.7): any leftover `.curate-running`
lock at boot means the prior /curate run crashed (new session = nothing
legitimately still running), so the message fires with no age gate — but
removal of the lock stays unconditional either way. These tests pin the two
pure helpers; the full crash drill (lock file -> hook run -> notice +
unconditional removal) is exercised via subprocess against the real repo
tree, matching the module's own REPO_ROOT resolution.

Stdlib unittest, runs on macOS system Python 3.9.6:

    python3 -m unittest discover -s tests
    python3 tests/test_session_start_hook.py
"""
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_HOOKS_DIR = _REPO_ROOT / ".claude" / "hooks"
_HOOK_PATH = _HOOKS_DIR / "session-start.py"


def _load(name, filename):
    """Import a hyphenated hook file as a module. Safe here because
    session-start.py's side effects now live in main(), not module scope."""
    spec = importlib.util.spec_from_file_location(name, _HOOKS_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


session_start = _load("session_start", "session-start.py")


class ParseRunningTimestampTests(unittest.TestCase):
    def test_extracts_timestamp(self):
        self.assertEqual(
            session_start.parse_running_timestamp("RUNNING 2026-07-03T10:00:00"),
            "2026-07-03T10:00:00",
        )

    def test_empty_content_returns_none(self):
        # Bare-touch leftover (pre-content convention) has no timestamp to report.
        self.assertIsNone(session_start.parse_running_timestamp(""))

    def test_unrelated_content_returns_none(self):
        self.assertIsNone(session_start.parse_running_timestamp("not a lock line"))

    def test_tolerates_leading_whitespace(self):
        self.assertEqual(
            session_start.parse_running_timestamp("  RUNNING 2026-07-04T09:15:30\n"),
            "2026-07-04T09:15:30",
        )


class BuildCurateCrashNoticeTests(unittest.TestCase):
    def test_includes_timestamp_when_present(self):
        notice = session_start.build_curate_crash_notice("2026-07-03T10:00:00")
        self.assertIn("CURATE CRASHED", notice)
        self.assertIn("2026-07-03T10:00:00", notice)
        self.assertIn("git diff vera-system/memory/", notice)
        self.assertIn("re-run /curate", notice)

    def test_omits_timestamp_clause_when_absent(self):
        # A bare-touch leftover (no RUNNING line) still fires the notice —
        # any leftover lock is a crash — it just can't name when it started.
        notice = session_start.build_curate_crash_notice(None)
        self.assertIn("CURATE CRASHED", notice)
        self.assertNotIn("(started", notice)


class CrashDrillSubprocessTests(unittest.TestCase):
    """Full integration drill against the real repo tree (matches the
    contract's manual verify step): plant a stale lock, run the hook, assert
    the notice fires and the lock is gone afterward — unconditionally."""

    def setUp(self):
        self.lock_path = _REPO_ROOT / ".claude" / ".curate-running"
        self._had_lock = self.lock_path.exists()
        self._prior_content = self.lock_path.read_text() if self._had_lock else None

    def tearDown(self):
        # Restore whatever was there before (should be nothing in a clean tree).
        if self._had_lock:
            self.lock_path.write_text(self._prior_content)
        else:
            try:
                self.lock_path.unlink()
            except FileNotFoundError:
                pass

    def test_stale_lock_surfaces_notice_and_is_removed(self):
        self.lock_path.write_text("RUNNING 2026-07-03T10:00:00")
        result = subprocess.run(
            [sys.executable, str(_HOOK_PATH)],
            input="{}",
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout.strip())
        self.assertIn("CURATE CRASHED", payload["additionalContext"])
        self.assertIn("2026-07-03T10:00:00", payload["additionalContext"])
        self.assertFalse(self.lock_path.exists(), "lock must be removed unconditionally after the notice")

    def test_no_lock_means_no_notice(self):
        try:
            self.lock_path.unlink()
        except FileNotFoundError:
            pass
        result = subprocess.run(
            [sys.executable, str(_HOOK_PATH)],
            input="{}",
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout.strip())
        self.assertNotIn("CURATE CRASHED", payload["additionalContext"])


if __name__ == "__main__":
    unittest.main()
