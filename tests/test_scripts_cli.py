#!/usr/bin/env python3
"""CLI-level tests for the helper scripts' failure paths.

Skills auto-approve Bash(scripts/*), so these scripts run with model-supplied
arguments. The contract under test: bad input produces a clean one-line error
and a deliberate exit code, never a traceback; telemetry never writes outside
runs/ and never hard-fails the caller on I/O problems.

Stdlib unittest, runs on macOS system Python 3.9.6:

    python3 -m unittest discover -s tests
    python3 tests/test_scripts_cli.py
"""
import subprocess
import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS_DIR = _REPO_ROOT / "vera-system" / "scripts"


def _run(script, *args):
    return subprocess.run(
        [sys.executable, str(_SCRIPTS_DIR / script), *args],
        capture_output=True, text=True, timeout=30,
    )


class PanelScoreTests(unittest.TestCase):
    def test_missing_file_clean_exit(self):
        result = _run("panel-score.py", "--file", "/nonexistent/findings.json")
        self.assertEqual(result.returncode, 1)
        self.assertIn("cannot read", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_missing_keys_are_valid_input(self):
        # score_findings defaults absent severity/confidence to low — a dict
        # with no score keys is legitimate model output, not an error.
        result = subprocess.run(
            [sys.executable, str(_SCRIPTS_DIR / "panel-score.py")],
            input='[{"concern": "no scores here"}]',
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0)

    def test_non_dict_entry_clean_exit(self):
        result = subprocess.run(
            [sys.executable, str(_SCRIPTS_DIR / "panel-score.py")],
            input='["just a string, not an object"]',
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("malformed finding", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


class TelemetryTests(unittest.TestCase):
    def test_traversal_skill_name_rejected(self):
        result = _run("telemetry.py", "../evil", "PASS")
        self.assertEqual(result.returncode, 1)
        self.assertIn("bad skill name", result.stderr)
        self.assertFalse((_REPO_ROOT / "vera-system" / "evil-telemetry.tsv").exists())

    def test_happy_path_appends_row(self):
        tsv = _REPO_ROOT / "vera-system" / "runs" / "ci-smoke-telemetry.tsv"
        try:
            result = _run("telemetry.py", "ci-smoke", "SKIP", "--note", "cli test")
            self.assertEqual(result.returncode, 0)
            self.assertTrue(tsv.exists())
            lines = tsv.read_text().strip().splitlines()
            self.assertEqual(len(lines), 2)  # header + one row
            self.assertIn("\tci-smoke\t", lines[1])
            self.assertIn("\tSKIP\t", lines[1])
        finally:
            if tsv.exists():
                tsv.unlink()

    def test_bad_outcome_rejected(self):
        result = _run("telemetry.py", "ci-smoke", "NOT_AN_OUTCOME")
        self.assertEqual(result.returncode, 1)
        self.assertIn("outcome must be", result.stderr)


if __name__ == "__main__":
    unittest.main()
