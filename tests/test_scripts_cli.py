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


class PromotionsCliTests(unittest.TestCase):
    """Runs against the real repo; promotions.tsv is snapshotted around any
    test that could write it."""

    LEDGER = _REPO_ROOT / "vera-system" / "memory" / "promotions.tsv"

    def test_check_runs_clean_against_repo(self):
        result = _run("curate-mode.py", "promotions", "check")
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("Traceback", result.stderr)

    def test_record_missing_args_exit_2(self):
        result = _run("curate-mode.py", "promotions", "record")
        self.assertEqual(result.returncode, 2)  # argparse usage error

    def test_record_empty_match_rejected(self):
        before = self.LEDGER.read_text() if self.LEDGER.exists() else None
        try:
            result = _run("curate-mode.py", "promotions", "record",
                          "--match", "\t\n", "--pattern", "x")
            self.assertEqual(result.returncode, 1)
            self.assertIn("empty after sanitization", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            after = self.LEDGER.read_text() if self.LEDGER.exists() else None
            self.assertEqual(before, after)  # no row written
        finally:
            if before is None and self.LEDGER.exists():
                self.LEDGER.unlink()


class LoopReportTests(unittest.TestCase):
    def test_runs_clean_and_prints_headline(self):
        tsv = _REPO_ROOT / "vera-system" / "runs" / "loop-report.tsv"
        before = tsv.read_text() if tsv.exists() else None
        try:
            result = _run("loop-report.py")
            self.assertEqual(result.returncode, 0)
            self.assertIn("Loop report", result.stdout)
            self.assertNotIn("Traceback", result.stderr)
        finally:
            if before is None:
                if tsv.exists():
                    tsv.unlink()
            else:
                tsv.write_text(before)


class BuildStateResumeTests(unittest.TestCase):
    """status/continue route before argparse; the legacy set form must be
    untouched. Uses a clearly-scratch slug under the real projects_dir and
    removes it afterward."""

    SLUG = "zzz-cli-resume-test"

    def _project_dir(self):
        import sys as _sys
        _sys.path.insert(0, str(_SCRIPTS_DIR))
        import vera_config
        return _REPO_ROOT / vera_config.get_path("projects_dir") / self.SLUG

    def tearDown(self):
        import shutil
        pd = self._project_dir()
        if pd.exists():
            shutil.rmtree(pd)

    def test_set_then_continue_roundtrip(self):
        created = _run("build-state.py", self.SLUG, "V0 Stage 2", "--mode", "new",
                       "--substage", "build loop")
        self.assertEqual(created.returncode, 0)
        cont = _run("build-state.py", "continue", self.SLUG)
        self.assertEqual(cont.returncode, 0)
        self.assertIn(f"SLUG={self.SLUG}", cont.stdout)
        self.assertIn("STAGE=V0 Stage 2", cont.stdout)
        self.assertIn("MODE=new", cont.stdout)
        self.assertIn("WORKTREE=n/a", cont.stdout)  # mode=new uses no worktree

    def test_status_lists_the_project(self):
        _run("build-state.py", self.SLUG, "V0 Stage 0", "--mode", "new")
        result = _run("build-state.py", "status")
        self.assertEqual(result.returncode, 0)
        self.assertIn(self.SLUG, result.stdout)

    def test_continue_unknown_slug_clean_exit(self):
        result = _run("build-state.py", "continue", "definitely-not-a-real-project-xyz")
        self.assertEqual(result.returncode, 1)
        self.assertIn("no build-state.md", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_status_extra_arg_rejected(self):
        result = _run("build-state.py", "status", "extra")
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr)

    def test_corrupt_state_file_does_not_crash_status(self):
        # A non-UTF-8 build-state.md must not traceback the whole status table.
        pd = self._project_dir()
        pd.mkdir(parents=True, exist_ok=True)
        (pd / "build-state.md").write_bytes(b"\xff\xfe**Mode:** new\n")
        result = _run("build-state.py", "status")
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("Traceback", result.stderr)

    def test_unknown_mode_continue_checks_worktree(self):
        # An empty/corrupt Mode must not silently route a build to the no-worktree
        # path; it should warn and attempt worktree detection (fail-safe).
        pd = self._project_dir()
        pd.mkdir(parents=True, exist_ok=True)
        (pd / "build-state.md").write_text(
            "# Build State: x\n**Mode:**\n**Stage:** Phase 5\n**Sub-stage:**\n")
        result = _run("build-state.py", "continue", self.SLUG)
        self.assertEqual(result.returncode, 0)
        self.assertIn("WARN=", result.stdout)
        self.assertNotIn("WORKTREE=n/a", result.stdout)


class ArtifactLintCliTests(unittest.TestCase):
    def test_missing_section_exits_1(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "idea.md"
            path.write_text("# Idea\n## The bet\nx\n")  # missing two sections
            result = _run("artifact-lint.py", "--profile", "idea", str(path))
            self.assertEqual(result.returncode, 1)
            self.assertIn("MISSING", result.stdout)
            self.assertNotIn("Traceback", result.stderr)

    def test_clean_artifact_exits_0(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "idea.md"
            path.write_text("# Idea\n## The bet\nx\n## Who it's for\ny\n## The problem\nz\n")
            result = _run("artifact-lint.py", "--profile", "idea", str(path))
            self.assertEqual(result.returncode, 0)
            self.assertIn("OK", result.stdout)


class ScoreGateCliTests(unittest.TestCase):
    def _stdin(self, payload, *args):
        return subprocess.run(
            [sys.executable, str(_SCRIPTS_DIR / "score-gate.py"), *args],
            input=payload, capture_output=True, text=True, timeout=30,
        )

    def test_build_ships_above_floor(self):
        result = self._stdin(
            '{"dimensions":[{"score":4},{"score":4},{"score":4},{"score":3},{"score":4}]}',
            "build")
        self.assertEqual(result.returncode, 0)
        self.assertIn("VERDICT=SHIP", result.stdout)

    def test_bad_json_clean_exit(self):
        result = self._stdin("not json", "build")
        self.assertEqual(result.returncode, 1)
        self.assertIn("cannot read JSON", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


class GateScanCliTests(unittest.TestCase):
    def test_fires_on_crowded_category(self):
        result = _run("gate-scan.py", "scout", "a better todo app")
        self.assertEqual(result.returncode, 0)
        self.assertIn("RESULT=FIRE", result.stdout)

    def test_passes_on_empty_space(self):
        result = _run("gate-scan.py", "scout", "a RAW to JPEG converter CLI")
        self.assertEqual(result.returncode, 0)
        self.assertIn("RESULT=PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
