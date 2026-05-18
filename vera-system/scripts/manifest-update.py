#!/usr/bin/env python3
"""
manifest-update.py — Manage MANIFEST.md state transitions for /build full.

Usage:
    python3 vera-system/scripts/manifest-update.py <project-slug> <action> [options]

Actions:
    init            Create MANIFEST from template
    phase-start     Mark a phase as in-progress
    phase-complete  Mark a phase as complete, record artifact
    build-phase     Update current build phase N of M
    complete        Mark project as complete

Examples:
    python3 vera-system/scripts/manifest-update.py my-app init --tier structured
    python3 vera-system/scripts/manifest-update.py my-app phase-start --phase "Phase 1: PRD"
    python3 vera-system/scripts/manifest-update.py my-app phase-complete --phase "Phase 1: PRD" --artifact plans/01-PRD.md
    python3 vera-system/scripts/manifest-update.py my-app build-phase --current 2 --total 3
    python3 vera-system/scripts/manifest-update.py my-app complete

Reads config.json for projects_dir. Validates transitions.
"""

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SYSTEM_DIR = SCRIPT_DIR.parent
REPO_ROOT = SYSTEM_DIR.parent

sys.path.insert(0, str(SCRIPT_DIR))
from vera_config import get_path, safe_project_path, validate_slug  # noqa: E402


def manifest_path(slug: str) -> Path:
    return safe_project_path(slug, "plans", "MANIFEST.md")


def validate_artifact_path(path_str: str) -> str:
    """Reject path traversal so a tainted --artifact arg can't write
    arbitrary paths (e.g. ../../.ssh/id_rsa) into shared MANIFEST state."""
    p = Path(path_str)
    if p.is_absolute():
        raise ValueError(f"Artifact path must be relative: {path_str}")
    if ".." in p.parts:
        raise ValueError(f"Artifact path cannot contain '..': {path_str}")
    return path_str


def now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def read_manifest(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text()


def update_field(content: str, field: str, value: str) -> str:
    """Update a **Field:** value in the manifest."""
    pattern = rf"\*\*{re.escape(field)}:\*\*\s*.*"
    if not re.search(pattern, content):
        # Field not found — append
        content += f"\n**{field}:** {value}\n"
        return content
    return re.sub(pattern, f"**{field}:** {value}", content, count=1)


def init_manifest(slug: str, tier: str) -> str:
    """Create initial MANIFEST content."""
    return f"""# MANIFEST — {slug}

**Status:** in-progress
**Tier:** {tier}
**Created:** {now_str()}
**Current Phase:** Phase 1: PRD
**Phase Status:** pending
**Build Phase:** —
**Last Updated:** {now_str()}

## Phase History

| Phase | Status | Started | Completed | Artifact |
|-------|--------|---------|-----------|----------|
| Phase 1: PRD | pending | — | — | — |
| Phase 2: Tech Design | pending | — | — | — |
| Phase 3: Arch Review | pending | — | — | — |
| Phase 4: Phase Planning | pending | — | — | — |
| Phase 5: Build | pending | — | — | — |
| Phase 6: Code Review | pending | — | — | — |
| Phase 6.5: Simplification | pending | — | — | — |
| Phase 6.7: Security Review | pending | — | — | — |
| Phase 7: QA | pending | — | — | — |
| Phase 8: Ship | pending | — | — | — |

## Project Summary

(filled on completion)
"""


def update_phase_in_table(content: str, phase: str, status: str,
                          started: str = None, completed: str = None,
                          artifact: str = None) -> str:
    """Update a phase row in the Phase History table."""
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if f"| {phase}" in line:
            parts = [p.strip() for p in line.split("|")]
            # parts: ['', phase, status, started, completed, artifact, '']
            if len(parts) >= 7:
                parts[2] = status
                if started:
                    parts[3] = started
                if completed:
                    parts[4] = completed
                if artifact:
                    parts[5] = artifact
                lines[i] = "| " + " | ".join(parts[1:-1]) + " |"
            break
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Manage MANIFEST.md")
    parser.add_argument("slug", help="Project slug")
    parser.add_argument("action", choices=["init", "phase-start", "phase-complete", "build-phase", "complete"])
    parser.add_argument("--phase", help="Phase name (e.g., 'Phase 1: PRD')")
    parser.add_argument("--artifact", help="Artifact path")
    parser.add_argument("--tier", default="structured", help="SDLC tier for init")
    parser.add_argument("--current", type=int, help="Current build phase number")
    parser.add_argument("--total", type=int, help="Total build phases")
    args = parser.parse_args()

    try:
        validate_slug(args.slug)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    path = manifest_path(args.slug)

    if args.action == "init":
        path.parent.mkdir(parents=True, exist_ok=True)
        content = init_manifest(args.slug, args.tier)
        path.write_text(content)
        print(f"Created: {path}")
        return

    if not path.exists():
        print(f"ERROR: MANIFEST not found at {path}. Run 'init' first.", file=sys.stderr)
        sys.exit(1)

    content = read_manifest(path)

    if args.action == "phase-start":
        if not args.phase:
            print("ERROR: --phase required", file=sys.stderr)
            sys.exit(1)
        content = update_field(content, "Current Phase", args.phase)
        content = update_field(content, "Phase Status", "in-progress")
        content = update_field(content, "Last Updated", now_str())
        content = update_phase_in_table(content, args.phase, "in-progress", started=now_str()[:10])

    elif args.action == "phase-complete":
        if not args.phase:
            print("ERROR: --phase required", file=sys.stderr)
            sys.exit(1)
        content = update_field(content, "Phase Status", "complete")
        content = update_field(content, "Last Updated", now_str())
        try:
            artifact_str = validate_artifact_path(args.artifact) if args.artifact else "—"
        except ValueError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)
        content = update_phase_in_table(content, args.phase, "complete",
                                        completed=now_str()[:10], artifact=artifact_str)

    elif args.action == "build-phase":
        if not args.current or not args.total:
            print("ERROR: --current and --total required", file=sys.stderr)
            sys.exit(1)
        content = update_field(content, "Build Phase", f"{args.current} of {args.total}")
        content = update_field(content, "Last Updated", now_str())

    elif args.action == "complete":
        content = update_field(content, "Status", "complete")
        content = update_field(content, "Last Updated", now_str())

    path.write_text(content)
    print(f"Updated: {path} ({args.action})")


if __name__ == "__main__":
    main()
