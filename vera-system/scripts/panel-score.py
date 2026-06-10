#!/usr/bin/env python3
"""
panel-score.py — deterministic scoring / sort / tie-break for /panel Step 4.

The model does ALL the judgment: assigning severity and confidence per finding,
detecting related concerns (cross-panel), contradictions (contested), and
whether a concern is already addressed in idea.md. It tags each finding with
those flags and hands the list here. This script does ONLY the arithmetic,
sort, and deterministic tie-break — the error-prone, token-heavy mechanical
part — so surfacing is reproducible across runs.

Input: a JSON array on stdin (or via --file), each item:
  {"concern": str, "kind": "evidence|gap|assumption",
   "severity": "high|med|low", "confidence": "high|med|low",
   "cross_panel": bool (optional), "contested": bool (optional),
   "addressed": bool (optional)}

Scoring (unchanged from the prose rule):
  severity_score / confidence_score: high=3, med=2, low=1
  base_score = severity_score * confidence_score        (range 1-9)
  cross_panel -> +1   (the cross-panel bump)
  addressed   -> -1   (downweight; the model already did the keyword check)
  contested   -> score unchanged
Tie-break (equal score): severity > confidence > cross-panel-bumped > raw order.

Output: JSON {"top": [...], "rest": [...]}, top N (default 4), each finding
annotated with severity_score / confidence_score / base_score / score.
"""
from __future__ import annotations

import argparse
import json
import sys

RANK = {"high": 3, "med": 2, "medium": 2, "low": 1}


def score_findings(findings):
    scored = []
    for i, f in enumerate(findings):
        sev = RANK.get(str(f.get("severity", "")).lower(), 1)
        conf = RANK.get(str(f.get("confidence", "")).lower(), 1)
        base = sev * conf
        score = base + (1 if f.get("cross_panel") else 0) - (1 if f.get("addressed") else 0)
        item = dict(f)
        item.update({
            "severity_score": sev,
            "confidence_score": conf,
            "base_score": base,
            "score": score,
            "_order": i,
        })
        scored.append(item)

    # Sort descending. Tie-break order: score, severity, confidence,
    # cross-panel-bumped, then earliest raw order (-_order so lower index wins).
    scored.sort(
        key=lambda f: (
            f["score"],
            f["severity_score"],
            f["confidence_score"],
            1 if f.get("cross_panel") else 0,
            -f["_order"],
        ),
        reverse=True,
    )
    for f in scored:
        f.pop("_order", None)
    return scored


def main() -> None:
    ap = argparse.ArgumentParser(description="Deterministic /panel finding scorer")
    ap.add_argument("--file", help="JSON findings file (default: read stdin)")
    ap.add_argument("--top", type=int, default=4, help="how many to surface (default 4)")
    args = ap.parse_args()

    try:
        raw = open(args.file).read() if args.file else sys.stdin.read()
    except OSError as exc:
        print(f"panel-score: cannot read {args.file}: {exc}", file=sys.stderr)
        sys.exit(1)
    try:
        findings = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"panel-score: invalid JSON: {exc}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(findings, list):
        print("panel-score: expected a JSON array of findings", file=sys.stderr)
        sys.exit(1)

    # Findings are model-generated JSON. Missing keys are fine (score_findings
    # defaults them), but non-dict entries (a bare string in the array) would
    # otherwise traceback. Name the problem instead.
    try:
        scored = score_findings(findings)
    except (AttributeError, TypeError, ValueError) as exc:
        print(f"panel-score: malformed finding (every entry must be an object): {exc}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps({"top": scored[: args.top], "rest": scored[args.top:]}, indent=2))


if __name__ == "__main__":
    main()
