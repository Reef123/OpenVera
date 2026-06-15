#!/usr/bin/env python3
"""Unit tests for the v1.18 gate scripts: artifact-lint, score-gate, gate-scan.

These three turn "the model self-checks" prose into deterministic gates. The
tests pin the behavior the skills now depend on: a missing mandatory section
HARD_FAILs, an inflated composite can't ship a sub-floor build, a regression
loses even when the target improved, and the scout keyword list fires
identically regardless of which entry path calls it.

Pure functions only (no subprocess) — the CLI wrappers are covered in
test_scripts_cli.py. Stdlib unittest, runs on macOS system Python 3.9.6:

    python3 -m unittest discover -s tests
    python3 tests/test_gates.py
"""
import importlib.util
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS_DIR = _REPO_ROOT / "vera-system" / "scripts"


def _load(mod_name, file_name):
    """Load a hyphen-named script as a module (can't `import` it normally)."""
    spec = importlib.util.spec_from_file_location(mod_name, str(_SCRIPTS_DIR / file_name))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


artifact_lint = _load("artifact_lint", "artifact-lint.py")
score_gate = _load("score_gate", "score-gate.py")
gate_scan = _load("gate_scan", "gate-scan.py")


class ArtifactLintTests(unittest.TestCase):
    def _lint(self, profile, body):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "artifact.md"
            path.write_text(body)
            return artifact_lint.lint(profile, path)

    def test_clean_idea_passes(self):
        body = "# Idea\n## The bet\nx\n## Who it's for\ny\n## The problem\nz\n"
        self.assertEqual(self._lint("idea", body), [])

    def test_missing_section_flagged(self):
        body = "# Idea\n## The bet\nx\n## The problem\nz\n"
        problems = self._lint("idea", body)
        self.assertTrue(any("MISSING" in p and "Who it's for" in p for p in problems))

    def test_empty_section_flagged(self):
        body = "# Idea\n## The bet\n\n## Who it's for\ny\n## The problem\nz\n"
        problems = self._lint("idea", body)
        self.assertTrue(any("EMPTY" in p and "The bet" in p for p in problems))

    def test_no_file_is_a_problem(self):
        problems = artifact_lint.lint("handoff", Path("/nonexistent/handoff.md"))
        self.assertEqual(len(problems), 1)
        self.assertIn("NO_FILE", problems[0])

    def test_heading_parenthetical_ignored(self):
        # "## Invariants (DO NOT MODIFY)" must satisfy a required "## Invariants".
        self.assertEqual(
            artifact_lint.heading_key("## Invariants (DO NOT MODIFY without an ADR)"),
            "invariants",
        )

    def test_handoff_requires_did_not_prove(self):
        body = (
            "# Handoff\n## Outcome\na\n## Observable behavior\nb\n"
            "## What V0 proved\nc\n## Open questions\nd\n"
        )  # missing "## What V0 did NOT prove"
        problems = self._lint("handoff", body)
        self.assertTrue(any("did NOT prove" in p for p in problems))

    def test_html_comment_only_section_is_empty(self):
        # A section whose only content is an HTML comment is structurally hollow.
        body = (
            "# Idea\n## The bet\nx\n## Who it's for\n<!-- TODO: fill in -->\n"
            "## The problem\nz\n"
        )
        problems = self._lint("idea", body)
        self.assertTrue(any("EMPTY" in p and "Who it's for" in p for p in problems))

    def test_curly_apostrophe_heading_matches(self):
        # Editors auto-convert apostrophes; "## Who it’s for" must still match.
        body = "# Idea\n## The bet\nx\n## Who it’s for\ny\n## The problem\nz\n"
        self.assertEqual(self._lint("idea", body), [])

    def test_handoff_requires_invariants_and_constraints(self):
        # /build full reads Invariants + Constraints; they're mandatory.
        body = (
            "# Handoff\n## Outcome\na\n## Observable behavior\nb\n"
            "## What V0 proved\nc\n## What V0 did NOT prove\nd\n## Open questions\ne\n"
        )  # missing ## Invariants and ## Constraints
        problems = self._lint("handoff", body)
        self.assertTrue(any("Invariants" in p for p in problems))
        self.assertTrue(any("Constraints" in p for p in problems))

    def test_contract_requires_shall(self):
        body = (
            "# Contract: x\n## What was built\na\n"
            "## Acceptance criteria\n- [ ] it works\n## Out of scope\nb\n"
        )
        problems = self._lint("contract", body)
        self.assertIn("NO_SHALL profile=contract", problems)

    def test_contract_with_shall_passes(self):
        body = (
            "# Contract: x\n## What was built\na\n"
            "## Acceptance criteria (EARS)\n- [ ] When clicked, the system shall save.\n"
            "## Out of scope\nb\n"
        )
        self.assertEqual(self._lint("contract", body), [])

    def test_fenced_heading_does_not_satisfy_requirement(self):
        # A required section that appears ONLY inside a fenced code block (e.g.
        # a pasted template example) must NOT count as present.
        body = (
            "# Idea\n## The bet\nx\n## Who it's for\ny\n"
            "Here is the template to fill in:\n"
            "```markdown\n## The problem\n[describe it]\n```\n"
        )  # the real ## The problem section is absent; only a fenced example exists
        problems = self._lint("idea", body)
        self.assertTrue(any("MISSING" in p and "The problem" in p for p in problems))

    def test_fenced_heading_does_not_steal_body(self):
        # A `##` line inside a python fence must not start a fake section that
        # captures the following real section's body.
        body = (
            "# Idea\n## The bet\n```python\n# config\n## not a heading\nx = 1\n```\n"
            "## Who it's for\ny\n## The problem\nz\n"
        )
        self.assertEqual(self._lint("idea", body), [])

    def test_nested_fence_does_not_reopen(self):
        # An inner ``` inside an outer ```` must not reopen the document and
        # expose a fenced heading as a real section.
        body = (
            "# Idea\n## The bet\nx\n## Who it's for\ny\n"
            "````markdown\n```\n## The problem\n```\n````\n"
        )  # the only ## The problem is buried in a nested fence -> still MISSING
        problems = self._lint("idea", body)
        self.assertTrue(any("MISSING" in p and "The problem" in p for p in problems))

    def test_deeper_heading_does_not_satisfy_required(self):
        # A `### The problem` must NOT satisfy the required `## The problem`.
        body = "# Idea\n## The bet\nx\n## Who it's for\ny\n### The problem\nz\n"
        problems = self._lint("idea", body)
        self.assertTrue(any("MISSING" in p and "The problem" in p for p in problems))

    def test_closing_atx_run_still_matches(self):
        # "## The bet ##" is valid CommonMark and must satisfy "## The bet".
        body = "# Idea\n## The bet ##\nx\n## Who it's for ##\ny\n## The problem ##\nz\n"
        self.assertEqual(self._lint("idea", body), [])

    def test_indented_heading_still_matches(self):
        # Up to 3 spaces of indent is a valid ATX heading.
        body = "# Idea\n  ## The bet\nx\n ## Who it's for\ny\n   ## The problem\nz\n"
        self.assertEqual(self._lint("idea", body), [])

    def test_shall_only_in_fence_fails(self):
        # A `shall` that exists only inside a fenced example does not make the
        # real acceptance criteria verifiable.
        body = (
            "# Contract: x\n## What was built\na\n"
            "## Acceptance criteria\n- [ ] it works\n"
            "```\nWhen clicked, the system shall save.\n```\n"
            "## Out of scope\nb\n"
        )
        self.assertIn("NO_SHALL profile=contract", self._lint("contract", body))

    def test_inner_python_fence_does_not_close_outer(self):
        # A ```python line inside a ``` block is content, not a closer, so a
        # heading after it stays fenced (the only ## The problem is buried).
        body = (
            "# Idea\n## The bet\nx\n## Who it's for\ny\n"
            "```\nsome example:\n```python\n## The problem\n```\n"
        )  # unbalanced-looking but the inner ```python is body until the final ```
        problems = self._lint("idea", body)
        self.assertTrue(any("MISSING" in p and "The problem" in p for p in problems))


class ScoreGateBuildTests(unittest.TestCase):
    def _dims(self, *scores):
        return {"dimensions": [{"name": f"d{i}", "score": s} for i, s in enumerate(scores)]}

    def test_ship_at_floor(self):
        out = score_gate.gate_build(self._dims(4, 4, 3, 4, 3), 3.5)  # mean 3.6
        self.assertIn("VERDICT=SHIP", out)

    def test_fix_below_floor(self):
        out = score_gate.gate_build(self._dims(3, 3, 3, 3, 3), 3.5)  # mean 3.0
        self.assertIn("VERDICT=FIX", out)

    def test_inflated_composite_cannot_ship(self):
        # Judge claims 3.6 (would ship) but the dimensions mean 3.2 -> FIX.
        data = self._dims(3, 3, 3, 3, 4)
        data["composite"] = 3.6
        out = score_gate.gate_build(data, 3.5)
        self.assertIn("VERDICT=FIX", out)
        self.assertTrue(any(line.startswith("MISCOUNT") for line in out))

    def test_matching_composite_no_miscount(self):
        data = self._dims(4, 4, 4, 4, 4)
        data["composite"] = 4.0
        out = score_gate.gate_build(data, 3.5)
        self.assertFalse(any(line.startswith("MISCOUNT") for line in out))

    def test_no_dimensions_raises(self):
        with self.assertRaises(ValueError):
            score_gate.gate_build({"dimensions": []}, 3.5)

    def test_boolean_score_rejected(self):
        # float(True)==1.0 would silently count a stray `true` as a score.
        with self.assertRaises(ValueError):
            score_gate.gate_build({"dimensions": [{"score": True}]}, 3.5)

    def test_out_of_range_score_rejected(self):
        # A judge that emits 6 must not inflate the composite past the floor.
        with self.assertRaises(ValueError):
            score_gate.gate_build({"dimensions": [{"score": 6}]}, 3.5)

    def test_scoreless_dimension_fails_closed(self):
        # A score-less entry must not let a partial high subset ship.
        with self.assertRaises(ValueError):
            score_gate.gate_build({"dimensions": [{"score": 5}, {"name": "no score"}]}, 3.5)

    def test_expect_dims_mismatch_fails_closed(self):
        # A truncated judge response (1 of 5) must not average a high subset.
        with self.assertRaises(ValueError):
            score_gate.gate_build({"dimensions": [{"score": 5}]}, 3.5, expect=5)

    _FIVE = ("Functionality", "Architecture", "UI/Design", "Completeness", "Polish")

    def test_expect_dims_match_passes(self):
        dims = [{"name": n, "score": s} for n, s in zip(self._FIVE, (4, 4, 4, 3, 4))]
        out = score_gate.gate_build({"dimensions": dims}, 3.5, expect=5)
        self.assertIn("VERDICT=SHIP", out)

    def test_expect_dims_duplicate_names_fails_closed(self):
        # Five "Functionality" entries must not ship while real dims are absent.
        dims = [{"name": "Functionality", "score": 5} for _ in range(5)]
        with self.assertRaises(ValueError):
            score_gate.gate_build({"dimensions": dims}, 3.5, expect=5)

    def test_quoted_numeric_score_accepted(self):
        dims = [{"name": n, "score": str(s)} for n, s in zip(self._FIVE, (4, 4, 4, 3, 4))]
        out = score_gate.gate_build({"dimensions": dims}, 3.5, expect=5)
        self.assertIn("VERDICT=SHIP", out)


class ScoreGateImproveTests(unittest.TestCase):
    def test_win_no_regression(self):
        out = score_gate.gate_improve(
            {"target": {"old": 2.5, "new": 3.8},
             "previously_passing": [{"name": "t", "old": 4.0, "new": 4.0}]}, 0.5)
        self.assertIn("VERDICT=WIN", out)

    def test_regression_loses_despite_target_gain(self):
        out = score_gate.gate_improve(
            {"target": {"old": 2.5, "new": 3.8},
             "previously_passing": [{"name": "t", "old": 4.5, "new": 3.8}]}, 0.5)  # drop 0.7 > band
        self.assertIn("VERDICT=LOSS", out)
        self.assertTrue(any(line.startswith("REGRESSION") for line in out))

    def test_small_drop_within_band_not_regression(self):
        out = score_gate.gate_improve(
            {"target": {"old": 2.5, "new": 3.8},
             "previously_passing": [{"name": "t", "old": 4.0, "new": 3.7}]}, 0.5)  # drop 0.3 <= band
        self.assertIn("VERDICT=WIN", out)
        self.assertFalse(any(line.startswith("REGRESSION") for line in out))

    def test_no_improvement_is_loss(self):
        out = score_gate.gate_improve({"target": {"old": 3.5, "new": 3.5}}, 0.5)
        self.assertIn("VERDICT=LOSS", out)

    def test_plateau_flagged(self):
        out = score_gate.gate_improve({"target": {"old": 3.5, "new": 3.7}}, 0.5)  # delta 0.2 < band
        self.assertIn("PLATEAU=1", out)

    def test_missing_target_raises(self):
        with self.assertRaises(ValueError):
            score_gate.gate_improve({}, 0.5)

    def test_malformed_previously_passing_fails_closed(self):
        # A malformed regression entry could hide a real drop -> must raise.
        with self.assertRaises(ValueError):
            score_gate.gate_improve(
                {"target": {"old": 2.5, "new": 3.8},
                 "previously_passing": [{"name": "t", "old": 4.0}]}, 0.5)

    def test_band_override_from_json(self):
        # A stricter band in the payload must be honored over the default.
        out = score_gate.gate_improve(
            {"target": {"old": 3.0, "new": 4.0},
             "regressions_band": 0.2,
             "previously_passing": [{"name": "t", "old": 4.0, "new": 3.7}]}, 0.5)  # drop 0.3 > 0.2
        self.assertIn("VERDICT=LOSS", out)
        self.assertTrue(any(line.startswith("REGRESSION") for line in out))

    def test_band_override_cannot_widen_past_ceiling(self):
        # regressions_band=5 would let a 4-point drop pass as noise -> reject.
        with self.assertRaises(ValueError):
            score_gate.gate_improve(
                {"target": {"old": 3.0, "new": 4.0}, "regressions_band": 5}, 0.5)

    def test_plateau_suppressed_on_regression(self):
        # A regression is a decisive LOSS, not a plateau tick.
        out = score_gate.gate_improve(
            {"target": {"old": 3.5, "new": 3.6},  # small delta would otherwise plateau
             "previously_passing": [{"name": "t", "old": 4.5, "new": 3.5}]}, 0.5)  # drop 1.0
        self.assertIn("VERDICT=LOSS", out)
        self.assertNotIn("PLATEAU=1", out)


class GateScanScoutTests(unittest.TestCase):
    def _signals(self, text):
        return {sig for sig, _ in gate_scan.scan_scout(text)}

    def test_crowded_category_fires(self):
        self.assertIn("crowded_category", self._signals("a better todo list"))

    def test_named_platform_fires(self):
        self.assertIn("named_platform", self._signals("like Notion but for teams"))

    def test_alternative_pattern_fires(self):
        self.assertIn("alternative_pattern", self._signals("an alternative to Trello"))

    def test_drift_keyword_now_canonical(self):
        # "bookmark manager" lived only in /start-vague's copy; the union list
        # makes it fire from every entry path.
        self.assertIn("crowded_category", self._signals("a smarter bookmark manager"))

    def test_no_false_hit_on_substring(self):
        # "notes" must not match inside "footnotes".
        self.assertEqual(self._signals("manage footnotes in papers"), set())

    def test_phrase_pattern_is_boundary_guarded(self):
        # "but better" must not fire inside "rebut better".
        self.assertEqual(self._signals("rebut better arguments in debate"), set())

    def test_empty_space_passes(self):
        self.assertEqual(gate_scan.scan_scout("a CLI to convert RAW photos to JPEG"), [])

    def test_multiple_signals_all_reported(self):
        fires = gate_scan.scan_scout("an alternative to Notion for my todo list")
        self.assertEqual(len(fires), 3)

    def test_collision_platform_is_case_sensitive(self):
        # "Linear" the product fires; "linear" the adjective does not.
        self.assertIn("named_platform", self._signals("like Linear for issues"))
        self.assertNotIn("named_platform", self._signals("a linear algebra practice tool"))

    def test_collision_free_platform_matches_lowercase(self):
        # GitHub/Notion have no common-word meaning, so lowercase mentions fire.
        self.assertIn("named_platform", self._signals("build a github clone"))
        self.assertIn("named_platform", self._signals("a notion competitor"))

    def test_todo_aliases_fire(self):
        self.assertIn("crowded_category", self._signals("a to-do list for parents"))
        self.assertIn("crowded_category", self._signals("yet another task manager"))

    def test_to_do_two_words_does_not_overfire(self):
        # "to do" as ordinary English must not fire (too common).
        self.assertEqual(self._signals("a tool to do my taxes faster"), set())


if __name__ == "__main__":
    unittest.main()
