#!/usr/bin/env python3
"""
project-index.py — Generate a machine-readable index of all projects.

Usage:
    python3 vera-system/scripts/project-index.py [--format json|tsv]

Scans all project CLAUDE.md files for YAML frontmatter, merges with
telemetry data (cost rollup per project), and outputs a unified index.

Output: stdout (pipe to file or consume directly)
"""

import json
import csv
import io
import os
import re
import sys
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).resolve().parent
SYSTEM_DIR = SCRIPT_DIR.parent
REPO_ROOT = SYSTEM_DIR.parent

# vera_config.load_config never raises — malformed or partial config.json
# falls back to defaults instead of crashing the index build.
sys.path.insert(0, str(SCRIPT_DIR))
from vera_config import get_path  # noqa: E402

PROJECTS_DIR = REPO_ROOT / get_path("projects_dir")

RUNS_DIR = SYSTEM_DIR / "runs"

# Tiered walk (v1.21, build-spec §8.9 / architecture "Instances" item 2 —
# "why walk roads already paved"). Statuses that are terminal/static get a
# frontmatter-only existence check: no rglob, no source-count, no other
# file-exists calls into the project folder. `parked` in particular is never
# opened at all beyond this — its wake condition lives in the ROADMAP parked
# table, not in this scan. Anything not in this set (building, exploring,
# live, or a missing/unrecognized status) is treated as HOT and gets the
# full walk, same as before this change — unknown defaults to the safe
# (more-checking) side, only known-terminal statuses default to cold.
COLD_STATUSES = {"parked", "shipped", "declined", "deprecated"}


def _is_cold(meta):
    # frontmatter.py writes status with a trailing inline comment
    # ("status: parked   # lifecycle: ..."), and parse_frontmatter() (below)
    # doesn't strip inline comments from any field — strip it here, locally,
    # rather than changing the shared parser's behavior for every caller.
    status = (meta.get("status") or "").split("#", 1)[0].strip().lower()
    return status in COLD_STATUSES


def parse_frontmatter(path):
    """Extract YAML frontmatter from a markdown file."""
    text = path.read_text()
    match = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    if not match:
        return {}

    data = {}
    for line in match.group(1).strip().split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            value = value.strip()
            if value == "null":
                value = None
            data[key.strip()] = value
    return data


def load_telemetry_costs():
    """Roll up cost per project from all telemetry TSV files."""
    costs = {}
    if not RUNS_DIR.exists():
        return costs

    for tsv in RUNS_DIR.glob("*-telemetry.tsv"):
        with open(tsv) as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                project = row.get("project", "-")
                if project and project != "-":
                    cost = row.get("cost_usd", "0")
                    try:
                        costs[project] = costs.get(project, 0) + float(cost)
                    except (ValueError, TypeError):
                        pass
    return costs


def scan_projects():
    """Scan all project directories for CLAUDE.md frontmatter."""
    projects = []
    if not PROJECTS_DIR.exists():
        return projects

    for project_dir in sorted(PROJECTS_DIR.iterdir()):
        if not project_dir.is_dir():
            continue

        claude_md = project_dir / "CLAUDE.md"
        meta = {}

        if claude_md.exists():
            meta = parse_frontmatter(claude_md)

        # Fallback: derive what we can from the directory
        if not meta.get("slug"):
            meta["slug"] = project_dir.name
        if not meta.get("name"):
            meta["name"] = project_dir.name.replace("-", " ").title()

        cold = _is_cold(meta)
        meta["tier"] = "cold" if cold else "hot"

        if cold:
            # Cold/terminal project: frontmatter parse is the whole check.
            # Deliberately no .exists()/.is_dir()/.rglob() calls below this
            # point — that would still be "opening" the folder's contents.
            meta["has_spec"] = None
            meta["has_build_state"] = None
            meta["has_research"] = None
            meta["source_files"] = None
        else:
            # Check for key artifacts
            meta["has_spec"] = (project_dir / "spec.md").exists()
            meta["has_build_state"] = (project_dir / "build-state.md").exists()
            meta["has_research"] = (project_dir / "research").is_dir()

            # Count source files (rough project size signal)
            source_extensions = {".py", ".js", ".ts", ".svelte", ".jsx", ".tsx", ".go", ".rs"}
            source_count = sum(
                1 for f in project_dir.rglob("*")
                if f.suffix in source_extensions and "node_modules" not in str(f)
            )
            meta["source_files"] = source_count

        projects.append(meta)

    return projects


def main():
    fmt = "json"
    if len(sys.argv) > 1 and sys.argv[1] in ("--format",):
        fmt = sys.argv[2] if len(sys.argv) > 2 else "json"
    elif len(sys.argv) > 1:
        fmt = sys.argv[1].lstrip("-")

    projects = scan_projects()
    costs = load_telemetry_costs()

    # Merge cost data
    for p in projects:
        slug = p.get("slug", "")
        p["total_cost_usd"] = round(costs.get(slug, 0), 2)

    if fmt == "json":
        print(json.dumps(projects, indent=2, default=str))
    elif fmt == "tsv":
        if not projects:
            return
        fields = ["slug", "name", "status", "stack", "score", "total_cost_usd",
                  "source_files", "created", "updated", "origin"]
        writer = csv.DictWriter(sys.stdout, fieldnames=fields, delimiter="\t",
                                extrasaction="ignore")
        writer.writeheader()
        for p in projects:
            writer.writerow(p)
    else:
        print(f"Unknown format: {fmt}. Use json or tsv.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
