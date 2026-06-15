#!/usr/bin/env python3
"""
score-gate.py — deterministic ship / regression decision from judge JSON.

The judge (an LLM via openrouter.py) does the judgment: it scores each dimension
1-5 and writes a reason. This script does the arithmetic and the threshold
comparison — the part where a model doing mental math can quietly flip the
verdict. A judge that returns dimensions [3, 3, 3, 3, 4] with `"composite": 3.6`
should SHIP under a 3.5 floor only if 3.6 is real; the true mean is 3.2, which is
FIX. score-gate recomputes the composite from the dimensions and gates on that,
so a miscount (or a flattering self-rounded composite) can't ship a sub-floor
build or hide a regression.

Modes:

  build  — V0/upgrade Stage 3. Reads one judge JSON. Recomputes composite as the
           mean of dimension scores, compares against the ship floor (default
           3.5). Prints the recomputed composite, the verdict, and a MISCOUNT
           note when the judge's own composite disagrees with the math by more
           than a rounding tolerance. Exits 0 on a valid verdict ("FIX" is a
           normal outcome, not an error); malformed judge JSON exits 1 with a
           clean one-line error.

  improve — /improve GATE step. Reads before/after scores for the originally
           failed test plus any previously-passing tests, and applies the WIN/
           LOSS rule: improvement on the target with NO previously-passing test
           regressing by more than the variance band (default 0.5, ~LLM judge
           noise) is a WIN; any such regression is a LOSS even if the target
           improved. Also reports PLATEAU when the target delta is below the
           band (the skill tracks the 2-consecutive-cycle stop). Exits 0 on a
           valid verdict; malformed input exits 1 with a clean one-line error.

Input is JSON on stdin or via --file.

  build mode expects the judge object:
    {"dimensions": [{"name": "...", "score": N}, ...], "composite": N.N}

  improve mode expects:
    {"target": {"old": N.N, "new": N.N},
     "regressions_band": 0.5,                     (optional, overrides default)
     "previously_passing": [{"name": "...", "old": N.N, "new": N.N}, ...]}

Usage:
    python3 vera-system/scripts/score-gate.py build --file score.json
    python3 vera-system/scripts/score-gate.py build --floor 3.5 < score.json
    python3 vera-system/scripts/score-gate.py improve --file delta.json
"""
from __future__ import annotations

import argparse
import json
import math
import sys

SHIP_FLOOR = 3.5            # v0-stages.md Stage 3: composite >= 3.5 -> ship
COMPOSITE_TOLERANCE = 0.05  # judge composite may differ from mean by rounding
REGRESSION_BAND = 0.5       # improve: a prev-passing drop > this = regression (LLM noise ~0.3)
SCORE_MIN, SCORE_MAX = 1.0, 5.0  # dimension/composite domain (judge prompt: "Score 1-5")


def _read_json(file_arg):
    if file_arg:
        with open(file_arg, encoding="utf-8") as handle:
            raw = handle.read()
    else:
        raw = sys.stdin.read()
    return json.loads(raw)


def _check_band(value, label):
    """A band/floor must be finite. A regression band must also stay within the
    judge-noise ceiling: widening it past the default would let real regressions
    pass as noise, so cap it at REGRESSION_BAND."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number, got {value!r}")
    if not (0 <= value <= REGRESSION_BAND):
        raise ValueError(f"{label} must be in [0, {REGRESSION_BAND}], got {value!r}")
    return float(value)


def _score(value) -> float:
    """Coerce a JSON score to float and fail closed on anything a judge should
    never emit: booleans (float(True)==1.0 would count a stray `true` as 1),
    non-finite values, and scores outside the 1-5 domain (a `6` must not inflate
    the composite past the ship floor). A quoted numeric ("4") IS accepted —
    LLM judges routinely emit string numbers, and rejecting one would HARD_FAIL
    a legitimate ship."""
    if isinstance(value, bool):
        raise ValueError(f"score must be a number in [1, 5], got {value!r}")
    if isinstance(value, str):
        try:
            value = float(value.strip())
        except ValueError:
            raise ValueError(f"score must be a number in [1, 5], got {value!r}")
    elif not isinstance(value, (int, float)):
        raise ValueError(f"score must be a number in [1, 5], got {value!r}")
    f = float(value)
    if not math.isfinite(f) or not (SCORE_MIN <= f <= SCORE_MAX):
        raise ValueError(f"score out of range [1, 5]: {value!r}")
    return f


def compute_composite(dimensions: list, expect: int = None) -> float:
    """Mean of dimension scores. Fail closed: every entry must be a dict with a
    valid score (a score-less or malformed entry could otherwise let a partial
    high-scoring subset ship). When `expect` is set, the count must match it
    exactly (a truncated judge response with only the high dimensions must not
    average above the floor). Raises ValueError on an empty or malformed list."""
    if not dimensions:
        raise ValueError("no dimension scores found")
    scores = []
    names = []
    for d in dimensions:
        if not isinstance(d, dict) or "score" not in d:
            raise ValueError(f"each dimension must be an object with a score: {d!r}")
        scores.append(_score(d["score"]))
        names.append(str(d.get("name", "")).strip().lower())
    if expect is not None:
        if len(scores) != expect:
            raise ValueError(f"expected {expect} dimensions, got {len(scores)}")
        # Distinct, named dimensions — a padded set of duplicate names (five
        # "Functionality" entries) must not ship while real dimensions are absent.
        if "" in names or len(set(names)) != len(names):
            raise ValueError(f"expected {expect} distinct named dimensions, got {names!r}")
    return sum(scores) / len(scores)


def gate_build(data: dict, floor: float, expect: int = None) -> list:
    dims = data.get("dimensions")
    if not isinstance(dims, list):
        raise ValueError("build mode expects a 'dimensions' array")
    computed = compute_composite(dims, expect)
    out = [
        f"COMPOSITE={computed:.2f}",
        f"FLOOR={floor:.2f}",
        f"VERDICT={'SHIP' if computed >= floor else 'FIX'}",
    ]
    reported = data.get("composite")
    if isinstance(reported, (int, float)) and abs(float(reported) - computed) > COMPOSITE_TOLERANCE:
        # The judge's own composite disagreed with the math. Gating on `computed`
        # already used the right number; this line surfaces the discrepancy so
        # the skill can note an unreliable judge.
        out.append(f"MISCOUNT reported={float(reported):.2f} computed={computed:.2f}")
    return out


def gate_improve(data: dict, band: float) -> list:
    # A JSON `regressions_band` overrides the CLI/default band (documented).
    # It may tighten the band but not widen it past the noise ceiling.
    if "regressions_band" in data:
        band = _check_band(data["regressions_band"], "regressions_band")

    target = data.get("target") or {}
    try:
        delta = _score(target["new"]) - _score(target["old"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"improve mode expects numeric target.old and target.new in [1, 5]: {exc}")

    # Fail closed: a malformed previously-passing entry could hide a regression
    # and falsely return WIN, so reject it rather than skipping it.
    regressions = []
    for t in data.get("previously_passing") or []:
        if not isinstance(t, dict) or "old" not in t or "new" not in t:
            raise ValueError(f"each previously_passing entry needs old + new: {t!r}")
        drop = _score(t["old"]) - _score(t["new"])
        if drop > band:
            regressions.append((t.get("name", "?"), drop))

    out = [f"TARGET_DELTA={delta:+.2f}", f"BAND={band:.2f}"]
    for name, drop in regressions:
        out.append(f'REGRESSION test="{name}" drop={drop:.2f}')
    # Regression loses even when the target improved (improve/SKILL.md Step 8/9).
    if regressions:
        out.append("VERDICT=LOSS")
    elif delta > 0:
        out.append("VERDICT=WIN")
    else:
        out.append("VERDICT=LOSS")  # no improvement -> revert
    # Plateau is the "no meaningful movement" signal for the batch stop. A
    # regression is a decisive LOSS, not a plateau — don't muddy the counter.
    if not regressions and abs(delta) < band:
        out.append("PLATEAU=1")  # skill stops after 2 consecutive plateau cycles
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Deterministic ship/regression gate")
    sub = ap.add_subparsers(dest="mode", required=True)
    b = sub.add_parser("build", help="V0/upgrade ship floor from judge JSON")
    b.add_argument("--file", help="JSON file (default stdin)")
    b.add_argument("--floor", type=float, default=SHIP_FLOOR, help=f"ship floor (default {SHIP_FLOOR})")
    b.add_argument("--expect-dims", type=int, default=None, help="require exactly N dimensions (build judge prompts 5)")
    i = sub.add_parser("improve", help="WIN/LOSS from before/after scores")
    i.add_argument("--file", help="JSON file (default stdin)")
    i.add_argument("--band", type=float, default=REGRESSION_BAND, help=f"regression/plateau band (default {REGRESSION_BAND})")
    args = ap.parse_args()

    try:
        data = _read_json(args.file)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"score-gate: cannot read JSON: {exc}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(data, dict):
        print("score-gate: expected a JSON object", file=sys.stderr)
        sys.exit(1)

    try:
        if args.mode == "build":
            if not math.isfinite(args.floor) or not (SCORE_MIN <= args.floor <= SCORE_MAX):
                raise ValueError(f"--floor must be a finite number in [1, 5], got {args.floor!r}")
            lines = gate_build(data, args.floor, args.expect_dims)
        else:
            lines = gate_improve(data, _check_band(args.band, "--band"))
    except ValueError as exc:
        print(f"score-gate: {exc}", file=sys.stderr)
        sys.exit(1)
    for line in lines:
        print(line)


if __name__ == "__main__":
    main()
