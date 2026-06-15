#!/usr/bin/env python3
"""
gate-scan.py — deterministic keyword-gate firing for the scout gate.

The scout gate (recommend `/scout` when the idea lands in a crowded space the
user didn't anticipate) was prose in three places — `/start-vague` Step 1.5,
`/build new` v0-stages Step 1.5, and the `/scout` framing. The three copies
drifted: `/start-vague` had grown extra categories ("reading list", "bookmark
manager"), extra platforms ("Obsidian", "Roam"), and an extra pattern, so the
SAME idea could fire the gate in one entry path and not the other. This script
holds the one canonical (union) list, so every consumer fires identically.

It reports which signals fire; it does NOT decide whether to recommend scout.
That stays in the skill, which combines this with the user's research choice
(picked "Quick scout"/"Full research" already -> gate is moot; picked "No" AND
>=1 signal fires -> recommend). So this is informational: exit 0 always.

The model still applies judgment for the open-ended cases the list can't
enumerate ("any named SaaS or API"): a hit here is sufficient to fire, but a
miss is not proof the space is empty.

Usage:
    python3 vera-system/scripts/gate-scan.py scout "<the spark, or Job + Pain text>"
    python3 vera-system/scripts/gate-scan.py scout --file idea-fragment.txt
    echo "an alternative to Notion for notes" | python3 vera-system/scripts/gate-scan.py scout

Output (one line per signal that fires, then a RESULT line):
    FIRE signal=crowded_category match="todo"
    FIRE signal=named_platform match="Notion"
    FIRE signal=alternative_pattern match="alternative to"
    RESULT=FIRE
  or:
    RESULT=PASS
"""
from __future__ import annotations

import argparse
import re
import sys

# Canonical scout-gate signals — the UNION of the previously-drifted prose
# copies. Keep this list as the single source of truth; the skills cite it
# instead of re-listing keywords.
CROWDED_CATEGORIES = [
    "todo", "to-do", "task manager", "notes", "dashboard",
    "habit tracker", "journal", "kanban", "note-taking", "reading list",
    "bookmark manager",
]
# Product names split by collision risk. Case-insensitive ones have no common
# English-word meaning, so lowercase mentions ("a github clone", "a notion
# competitor") still fire. Case-sensitive ones double as everyday words
# ("linear algebra", "pick up the slack", "let users roam"), so only the
# capitalized product form fires.
PLATFORMS_CI = ["Notion", "Obsidian", "GitHub", "Stripe"]
PLATFORMS_CS = ["Linear", "Slack", "Roam"]
NAMED_PLATFORMS = PLATFORMS_CI + PLATFORMS_CS  # for docs/tests that want the full set
# Looser intent patterns. The old `/start-vague` prose also listed
# "<tool> for <use case>", but that is deliberately NOT a deterministic pattern
# here: matching "X for Y" without a tool list false-fires on ordinary phrasing
# ("a journal for runners"). The concrete cases (a named tool + "for") are
# caught by NAMED_PLATFORMS; anything else is the model's judgment call, which
# the wired skill prose names explicitly. So the CATEGORY + PLATFORM lists are
# the canonical deterministic union; this list is the deterministic subset of
# the intent patterns.
ALTERNATIVE_PATTERNS = ["alternative to", "but better"]


def _bounded(kw: str) -> str:
    """A regex matching kw bounded by non-alphanumerics, so 'notes' does not
    match 'footnotes' and 'but better' does not match 'rebut better'."""
    return r"(?<![A-Za-z0-9])" + re.escape(kw) + r"(?![A-Za-z0-9])"


def _token_hits(text: str, keywords: list, case_sensitive: bool = False) -> list:
    """Keywords that appear as bounded tokens (multi-word phrases like
    'habit tracker' and hyphenated 'note-taking' match literally)."""
    flags = 0 if case_sensitive else re.IGNORECASE
    return [kw for kw in keywords if re.search(_bounded(kw), text, flags)]


def scan_scout(text: str) -> list:
    """Return (signal, match) tuples for every scout-gate signal that fires."""
    fires = []
    for kw in _token_hits(text, CROWDED_CATEGORIES):
        fires.append(("crowded_category", kw))
    for kw in _token_hits(text, PLATFORMS_CI):
        fires.append(("named_platform", kw))
    for kw in _token_hits(text, PLATFORMS_CS, case_sensitive=True):
        fires.append(("named_platform", kw))
    for pat in ALTERNATIVE_PATTERNS:
        if re.search(_bounded(pat), text, re.IGNORECASE):
            fires.append(("alternative_pattern", pat))
    return fires


def main() -> None:
    ap = argparse.ArgumentParser(description="Deterministic keyword-gate scan")
    ap.add_argument("gate", choices=["scout"], help="which gate to evaluate")
    ap.add_argument("text", nargs="?", help="text to scan (default: --file or stdin)")
    ap.add_argument("--file", help="read text from a file instead")
    args = ap.parse_args()

    if args.text is not None:
        text = args.text
    elif args.file:
        try:
            with open(args.file, encoding="utf-8") as handle:
                text = handle.read()
        except (OSError, UnicodeDecodeError) as exc:
            print(f"gate-scan: cannot read {args.file}: {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        text = sys.stdin.read()

    fires = scan_scout(text)
    for signal, match in fires:
        print(f'FIRE signal={signal} match="{match}"')
    print(f"RESULT={'FIRE' if fires else 'PASS'}")


if __name__ == "__main__":
    main()
