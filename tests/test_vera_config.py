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


if __name__ == "__main__":
    unittest.main()
