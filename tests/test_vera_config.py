#!/usr/bin/env python3
"""Tests for vera-system/scripts/vera_config.py.

vera_config is the shared config + path-safety layer that most harness
scripts import. validate_slug / slugify / safe_project_path guard against
path traversal from user-supplied slugs (CLI args, /start-vague input), so
a regression here could let a tainted slug escape projects_dir. These tests
pin that boundary.

Stdlib unittest (no third-party dep) so it runs in CI and on the macOS
system Python (3.9.6) without an install step. Run:

    python3 -m unittest discover -s tests
    python3 tests/test_vera_config.py
"""
import sys
import unittest
from pathlib import Path

# vera_config lives in vera-system/scripts; this file is in tests/.
_SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "vera-system" / "scripts"
sys.path.insert(0, str(_SCRIPTS_DIR))

import vera_config  # noqa: E402


class ValidateSlugTests(unittest.TestCase):
    def test_accepts_good_slug(self):
        self.assertEqual(vera_config.validate_slug("good-slug"), "good-slug")

    def test_accepts_single_alphanumeric(self):
        self.assertEqual(vera_config.validate_slug("a"), "a")
        self.assertEqual(vera_config.validate_slug("7"), "7")

    def test_accepts_max_length_64(self):
        slug = "a" * 64
        self.assertEqual(vera_config.validate_slug(slug), slug)

    def test_rejects_traversal(self):
        with self.assertRaises(ValueError):
            vera_config.validate_slug("../../x")

    def test_rejects_path_separator(self):
        for bad in ("a/b", "a\\b", "/abs"):
            with self.assertRaises(ValueError):
                vera_config.validate_slug(bad)

    def test_rejects_empty(self):
        with self.assertRaises(ValueError):
            vera_config.validate_slug("")

    def test_rejects_leading_hyphen(self):
        with self.assertRaises(ValueError):
            vera_config.validate_slug("-leading")

    def test_rejects_uppercase_and_spaces(self):
        for bad in ("Upper", "has space", "dots.here"):
            with self.assertRaises(ValueError):
                vera_config.validate_slug(bad)

    def test_rejects_over_max_length(self):
        with self.assertRaises(ValueError):
            vera_config.validate_slug("a" * 65)

    def test_rejects_non_string(self):
        with self.assertRaises(ValueError):
            vera_config.validate_slug(None)


class SlugifyTests(unittest.TestCase):
    def test_basic_kebab(self):
        self.assertEqual(vera_config.slugify("My Cool Tool!"), "my-cool-tool")

    def test_collapses_runs_of_separators(self):
        self.assertEqual(vera_config.slugify("a   --  b___c"), "a-b-c")

    def test_trims_leading_trailing(self):
        self.assertEqual(vera_config.slugify("  !Hello!  "), "hello")

    def test_truncates_to_64(self):
        out = vera_config.slugify("x" * 200)
        self.assertEqual(len(out), 64)
        self.assertEqual(out, "x" * 64)

    def test_raises_on_all_punctuation(self):
        with self.assertRaises(ValueError):
            vera_config.slugify("!!!")

    def test_raises_on_empty(self):
        with self.assertRaises(ValueError):
            vera_config.slugify("")

    def test_raises_on_non_string(self):
        with self.assertRaises(ValueError):
            vera_config.slugify(None)

    def test_output_always_passes_validation(self):
        # Round-trip property: any slug slugify produces must validate.
        for text in ("My Cool Tool!", "Foo___Bar", "  weird--input  ", "123 abc"):
            self.assertEqual(
                vera_config.validate_slug(vera_config.slugify(text)),
                vera_config.slugify(text),
            )


class SafeProjectPathTests(unittest.TestCase):
    def setUp(self):
        self.projects_dir = (
            vera_config.repo_root() / vera_config.get_path("projects_dir")
        ).resolve()

    def test_happy_path_stays_under_projects_dir(self):
        p = vera_config.safe_project_path("myproj")
        self.assertEqual(p, self.projects_dir / "myproj")
        # Must not raise — confirms it's relative to projects_dir.
        p.relative_to(self.projects_dir)

    def test_happy_path_with_subparts(self):
        p = vera_config.safe_project_path("myproj", "idea.md")
        self.assertEqual(p, self.projects_dir / "myproj" / "idea.md")
        p.relative_to(self.projects_dir)

    def test_bad_slug_rejected_before_path_build(self):
        # First line of defense: validate_slug blocks traversal slugs.
        with self.assertRaises(ValueError):
            vera_config.safe_project_path("../../etc")

    def test_escape_via_parts_rejected(self):
        # Defense in depth: even with a valid slug, malicious *parts* that
        # resolve outside projects_dir must be caught by the resolve() check.
        with self.assertRaises(ValueError):
            vera_config.safe_project_path("myproj", "..", "..", "..", "etc", "passwd")


class ConfigIOTests(unittest.TestCase):
    """load_config's contract is 'never raises, always falls back to DEFAULTS'.
    Scripts (project-index, hooks) lean on that — a regression here turns a
    typo in config.json into a crash everywhere at once."""

    def _with_config(self, content):
        """Run load_config against a temp config file (or a missing one)."""
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            if content is not None:
                path.write_text(content)
            with mock.patch.object(vera_config, "config_path", return_value=path):
                return vera_config.load_config()

    def test_missing_file_returns_defaults(self):
        cfg = self._with_config(None)
        self.assertEqual(cfg, vera_config.DEFAULTS)
        self.assertIsNot(cfg, vera_config.DEFAULTS)  # a copy, not the shared dict

    def test_malformed_json_returns_defaults(self):
        cfg = self._with_config("{not json")
        self.assertEqual(cfg, vera_config.DEFAULTS)

    def test_partial_config_merges_over_defaults(self):
        cfg = self._with_config('{"llm": {"default_model": "custom/model"}}')
        # Override wins...
        self.assertEqual(cfg["llm"]["default_model"], "custom/model")
        # ...sibling defaults survive the nested merge...
        self.assertEqual(cfg["llm"]["provider"], vera_config.DEFAULTS["llm"]["provider"])
        # ...and untouched sections are intact.
        self.assertEqual(cfg["paths"], vera_config.DEFAULTS["paths"])

    def test_unknown_top_level_keys_pass_through(self):
        cfg = self._with_config('{"integrations": {"firecrawl": true}}')
        self.assertEqual(cfg["integrations"], {"firecrawl": True})

    def test_get_path_unknown_key_raises_keyerror(self):
        with self.assertRaises(KeyError):
            vera_config.get_path("not_a_real_path_key")

    def test_get_llm_model_unknown_key_raises_keyerror(self):
        with self.assertRaises(KeyError):
            vera_config.get_llm_model("not_a_real_model_key")

    def test_get_llm_model_falls_back_to_default(self):
        # Against the real repo config — must return a non-empty string either way.
        model = vera_config.get_llm_model("default_model")
        self.assertTrue(isinstance(model, str) and model)

    def test_cockpit_size_threshold_registered(self):
        # cockpit.md is a boot-tier derived view (v1.20) — must share the same
        # mechanical cap enforcement as state.md/ROADMAP.md/etc, or doctor.py
        # and curate-mode.py silently skip checking it.
        self.assertIn("vera-system/cockpit.md", vera_config.SIZE_THRESHOLDS)
        self.assertEqual(vera_config.SIZE_THRESHOLDS["vera-system/cockpit.md"], 60)

    def test_user_md_size_threshold_registered(self):
        # relationships/user.md (v1.20 user-memory lane) gets the same
        # mechanical cap enforcement as the other boot-tier files.
        self.assertIn("vera-system/relationships/user.md", vera_config.SIZE_THRESHOLDS)
        self.assertEqual(vera_config.SIZE_THRESHOLDS["vera-system/relationships/user.md"], 60)


class UserMemoryEnabledTests(unittest.TestCase):
    """user_memory_enabled() is a three-state read of the RAW config.json —
    key absent (legacy/grandfathered) vs present-true vs present-false. It
    must read differently from load_config()'s DEFAULTS-merged view, or the
    three states collapse into two."""

    def _with_config(self, content):
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            if content is not None:
                path.write_text(content)
            with mock.patch.object(vera_config, "config_path", return_value=path):
                return vera_config.user_memory_enabled()

    def test_key_absent_is_grandfathered_enabled(self):
        self.assertTrue(self._with_config('{"version": 1}'))

    def test_key_present_true(self):
        self.assertTrue(self._with_config('{"user_memory": true}'))

    def test_key_present_false(self):
        self.assertFalse(self._with_config('{"user_memory": false}'))

    def test_missing_file_is_grandfathered_enabled(self):
        self.assertTrue(self._with_config(None))

    def test_malformed_json_is_grandfathered_enabled(self):
        self.assertTrue(self._with_config("{not json"))

    def test_user_memory_not_in_defaults(self):
        # Load-bearing: if this key were added to DEFAULTS, load_config()
        # would always inject it and "absent" would become undetectable.
        self.assertNotIn("user_memory", vera_config.DEFAULTS)


class UserMemoryCliTests(unittest.TestCase):
    """`python3 vera_config.py user_memory` is the check the doc-sync and
    curate skills prescribe. It must route through user_memory_enabled()
    (raw-file read), because the generic key lookup on the merged config
    cannot represent the absent-key = grandfathered-enabled state."""

    def _cli_supported(self):
        # Runs the real script against the dev checkout's own config.json
        # (which has no user_memory key) — exactly the state a legacy
        # install is in.
        import subprocess
        script = Path(vera_config.__file__).resolve()
        return subprocess.run(
            [sys.executable, str(script), "user_memory"],
            capture_output=True, text=True,
        )

    def test_cli_prints_bare_boolean(self):
        result = self._cli_supported()
        self.assertEqual(result.returncode, 0)
        self.assertIn(result.stdout.strip(), ("true", "false"))

    def test_cli_absent_key_reports_enabled(self):
        # The dev checkout's config.json has no user_memory key — the CLI
        # must report the grandfathered-enabled state, not "unknown key".
        result = self._cli_supported()
        self.assertEqual(result.stdout.strip(), "true")
        self.assertNotIn("Unknown top-level key", result.stderr)


if __name__ == "__main__":
    unittest.main()
