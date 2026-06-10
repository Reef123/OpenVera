#!/usr/bin/env python3
"""
telemetry.py — Shared telemetry logger for all Vera skills.

Usage:
    python3 vera-system/scripts/telemetry.py <skill> <outcome> [options]

Examples:
    python3 vera-system/scripts/telemetry.py scout PASS --sources reddit+web --latency 45 --cost 0.00 --note "claude code gotchas"
    python3 vera-system/scripts/telemetry.py research PASS --project my-app --latency 300 --cost 0.42 --note "copilot studio deep dive"
    python3 vera-system/scripts/telemetry.py build PASS --project my-app --score 3.8 --latency 1200 --cost 0.15 --note "invoice tracker V0"
    python3 vera-system/scripts/telemetry.py improve WIN --score 4.2 --latency 180 --cost 0.35 --note "research Step 3"

Appends one row to runs/<skill>-telemetry.tsv. Creates file with header if missing.

TSV columns: timestamp, session, skill, project, sources, outcome, score, latency_s, cost_usd, failure_mode, note
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SYSTEM_DIR = SCRIPT_DIR.parent
REPO_ROOT = SYSTEM_DIR.parent

sys.path.insert(0, str(SCRIPT_DIR))
from vera_config import validate_slug  # noqa: E402

# Runs directory at repo root (not inside vera-system)
RUNS_DIR = REPO_ROOT / "vera-system" / "runs"

VALID_OUTCOMES = {"PASS", "SOFT_FAIL", "HARD_FAIL", "WIN", "LOSS", "SKIP"}

HEADER = "timestamp\tsession\tskill\tproject\tsources\toutcome\tscore\tlatency_s\tcost_usd\tfailure_mode\tnote"


def main():
    parser = argparse.ArgumentParser(description="Log telemetry for a skill run")
    parser.add_argument("skill", help="Skill name (scout, research, build, improve)")
    parser.add_argument("outcome", help=f"Run outcome: {', '.join(sorted(VALID_OUTCOMES))}")
    parser.add_argument("--session", default="-", help="Session identifier")
    parser.add_argument("--project", default="-", help="Project slug (links cost to project)")
    parser.add_argument("--sources", default="-", help="Sources used (e.g., reddit+web+youtube)")
    parser.add_argument("--score", default="-", help="Score if applicable")
    parser.add_argument("--latency", default="-", help="Latency in seconds")
    parser.add_argument("--cost", default="-", help="Cost in USD")
    parser.add_argument("--failure", default="-", help="Failure mode (e.g., tool_error, timeout, hallucination)")
    parser.add_argument("--note", default="-", help="Brief description of what was run")
    args = parser.parse_args()

    if args.outcome not in VALID_OUTCOMES:
        print(f"ERROR: outcome must be one of {VALID_OUTCOMES}", file=sys.stderr)
        sys.exit(1)

    # The skill name lands in a filename (runs/<skill>-telemetry.tsv) and
    # skills auto-approve Bash(scripts/*) — validate it like any slug so a
    # tainted value can't write outside runs/.
    try:
        validate_slug(args.skill)
    except ValueError as exc:
        print(f"ERROR: bad skill name: {exc}", file=sys.stderr)
        sys.exit(1)

    tsv_path = RUNS_DIR / f"{args.skill}-telemetry.tsv"
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    row = "\t".join([
        timestamp,
        args.session,
        args.skill,
        args.project,
        args.sources,
        args.outcome,
        str(args.score),
        str(args.latency),
        str(args.cost),
        args.failure,
        args.note,
    ])

    # Telemetry is optional — an unwritable runs/ must never abort the skill
    # that called us (e.g. a build's ship step). Warn and exit 0.
    try:
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        if not tsv_path.exists():
            tsv_path.write_text(HEADER + "\n")
        with open(tsv_path, "a") as f:
            f.write(row + "\n")
    except OSError as exc:
        print(f"WARNING: telemetry not logged ({exc}) — continuing", file=sys.stderr)
        sys.exit(0)

    print(f"Logged: {args.skill} {args.outcome} → {tsv_path.name}")


if __name__ == "__main__":
    main()
