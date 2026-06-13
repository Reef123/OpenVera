#!/usr/bin/env python3
"""
build-state.py — Manage build-state.md transitions deterministically.

Usage:
    python3 vera-system/scripts/build-state.py <slug> <stage> [--substage STEP] [--mode MODE] [--artifact KEY=PATH] [--decision TEXT]

Examples:
    python3 vera-system/scripts/build-state.py my-app "V0 Stage 0" --mode new
    python3 vera-system/scripts/build-state.py my-app "V0 Stage 2" --substage "build component 3"
    python3 vera-system/scripts/build-state.py my-app "V0 Stage 3" --artifact "Build score=3.8/5.0"
    python3 vera-system/scripts/build-state.py my-app "complete"

Reads config.json for projects_dir. Creates file if missing. Validates stage transitions.
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

# Resolve paths
SCRIPT_DIR = Path(__file__).resolve().parent
SYSTEM_DIR = SCRIPT_DIR.parent
REPO_ROOT = SYSTEM_DIR.parent

sys.path.insert(0, str(SCRIPT_DIR))
from vera_config import get_path, safe_project_path, validate_slug  # noqa: E402

V0_STAGES = [
    "V0 Stage 0",    # Kickoff + Purpose
    "V0 Stage 1",    # Parallel Sprint
    "V0 Stage 2",    # Build Loop
    "V0 Stage 3",    # Score
    "V0 Stage 4",    # Ship (4a)
    "V0 Stage 4a",   # Ship (explicit alias for the 4a/4b split in v0-stages.md)
    "V0 Stage 4b",   # Handoff codification (writes handoff.md)
    "complete",
]

FULL_STAGES = [
    "Full Stage 0",  # Kickoff
    "Full Stage 1",  # Autonomous Sprint
    "Phase 1",       # PRD
    "Phase 2",       # Tech Design
    "Phase 3",       # Arch Review
    "Phase 4",       # Phase Planning
    "Phase 5",       # Build Phase N
    "Phase 6",       # Code Review N
    "Phase 6.5",     # Simplification
    "Phase 6.7",     # Security Review (OWASP Top 10)
    "Phase 7",       # QA
    "Phase 8",       # Ship
    "complete",
]

ALL_STAGES = set(V0_STAGES + FULL_STAGES)


def state_file_path(slug: str) -> Path:
    return safe_project_path(slug, "build-state.md")


def read_state(path: Path) -> dict:
    """Parse existing build-state.md into a dict."""
    state = {"mode": "", "stage": "", "substage": "", "artifacts": [], "decisions": []}
    if not path.exists():
        return state

    section = None
    for line in path.read_text().splitlines():
        line_stripped = line.strip()
        if line_stripped.startswith("**Mode:**"):
            state["mode"] = line_stripped.split("**Mode:**")[1].strip()
        elif line_stripped.startswith("**Stage:**"):
            state["stage"] = line_stripped.split("**Stage:**")[1].strip()
        elif line_stripped.startswith("**Sub-stage:**"):
            state["substage"] = line_stripped.split("**Sub-stage:**")[1].strip()
        elif line_stripped == "## Artifacts":
            section = "artifacts"
        elif line_stripped == "## Decision Log":
            section = "decisions"
        elif line_stripped.startswith("## "):
            section = None
        elif section == "artifacts" and line_stripped.startswith("- "):
            state["artifacts"].append(line_stripped[2:])
        elif section == "decisions" and line_stripped.startswith("- "):
            state["decisions"].append(line_stripped[2:])

    return state


def write_state(path: Path, state: dict, slug: str):
    """Write build-state.md from state dict."""
    path.parent.mkdir(parents=True, exist_ok=True)

    artifacts_lines = "\n".join(f"- {a}" for a in state["artifacts"]) if state["artifacts"] else "- (none yet)"
    decisions_lines = "\n".join(f"- {d}" for d in state["decisions"]) if state["decisions"] else ""

    content = f"""# Build State: {slug}

**Mode:** {state['mode']}
**Stage:** {state['stage']}
**Sub-stage:** {state['substage']}
**Last updated:** {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}

## Artifacts
{artifacts_lines}

## Decision Log
{decisions_lines}
"""
    path.write_text(content.strip() + "\n")


def main():
    parser = argparse.ArgumentParser(description="Manage build-state.md transitions")
    parser.add_argument("slug", help="Project slug (kebab-case)")
    parser.add_argument("stage", help="Target stage (e.g., 'V0 Stage 2', 'Phase 5', 'complete')")
    parser.add_argument("--substage", default="", help="Sub-stage description")
    parser.add_argument("--mode", choices=["new", "full"], help="Build mode (required on first call)")
    parser.add_argument("--artifact", action="append", default=[], help="Add artifact (KEY=PATH)")
    parser.add_argument("--decision", action="append", default=[], help="Add decision log entry")
    args = parser.parse_args()

    try:
        validate_slug(args.slug)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    # Accept short stage names ("Stage 0") when --mode is set; infer the prefix.
    # SKILL.md naturally writes "Stage 0" without remembering which mode it's in;
    # this lets the script meet that ergonomic instead of crashing on it.
    if args.stage not in ALL_STAGES and args.mode:
        prefix = "V0" if args.mode == "new" else "Full"
        candidate = f"{prefix} {args.stage}"
        if candidate in ALL_STAGES:
            args.stage = candidate

    if args.stage not in ALL_STAGES:
        print(f"ERROR: Unknown stage '{args.stage}'", file=sys.stderr)
        print(f"Valid V0 stages: {', '.join(V0_STAGES)}", file=sys.stderr)
        print(f"Valid Full stages: {', '.join(FULL_STAGES)}", file=sys.stderr)
        sys.exit(1)

    path = state_file_path(args.slug)
    state = read_state(path)

    # Set or validate mode
    if args.mode:
        state["mode"] = args.mode
    elif not state["mode"]:
        # Infer from stage name
        if args.stage.startswith("V0"):
            state["mode"] = "new"
        elif args.stage.startswith(("Full", "Phase")):
            state["mode"] = "full"
        else:
            print("ERROR: No mode set. Use --mode on first call.", file=sys.stderr)
            sys.exit(1)

    # Update stage
    old_stage = state["stage"]
    state["stage"] = args.stage
    state["substage"] = args.substage

    # Add artifacts
    for artifact in args.artifact:
        state["artifacts"].append(artifact)

    # Add decisions with timestamp
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    for decision in args.decision:
        state["decisions"].append(f"[{ts}] {decision}")

    write_state(path, state, args.slug)

    # Report
    if old_stage:
        print(f"Transition: {old_stage} → {args.stage}")
    else:
        print(f"Created: {args.stage} (mode={state['mode']})")
    print(f"State file: {path}")


if __name__ == "__main__":
    main()
