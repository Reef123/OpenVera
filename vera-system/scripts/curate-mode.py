#!/usr/bin/env python3
"""
curate-mode.py — deterministic helpers for /curate.

Two subcommands cover the mechanical parts of /curate that the model used to
do freehand (and the path resolution it routinely got wrong):

  mode
      Count memory files across both stores (auto-memory under
      ~/.claude/projects/<this repo>/memory/ + harness memory_dir) and print:
        MODE=LIGHT|FULL
        AUTO_MEMORY=<resolved path or NONE>
        AUTO_FILES=<n>
        HARNESS_FILES=<n>
        TOTAL=<n>
      < 10 files -> LIGHT, 10+ -> FULL.  (Decision unchanged from the prose.)

  graduation
      Walk {projects_dir}/*/CLAUDE.md. For each project with status: shipped,
      count commits in the project dir over the last 30 days and the age of
      build-state.md. Print one FLAGGED line per project where commits >= 3 AND
      build-state.md is >= 30 days stale (the "real use without /build full"
      signal). Read-only — never edits status; the user decides per project.

The judgment in /curate (what to prune, dedupe, promote) stays in the skill.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

from vera_config import repo_root, get_path

GRADUATION_COMMITS = 3
GRADUATION_STALE_DAYS = 30
LIGHT_THRESHOLD = 10


def parse_frontmatter(path: Path) -> dict:
    """Minimal YAML frontmatter reader. Mirrors project-index.py's
    parse_frontmatter (kept inline because that file's hyphenated name can't
    be imported as a module)."""
    text = path.read_text()
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    data = {}
    for line in match.group(1).strip().split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            value = value.split("#", 1)[0].strip()  # drop inline comment
            data[key.strip()] = None if value == "null" else value
    return data


def auto_memory_dir() -> Path | None:
    """Resolve this repo's Claude Code auto-memory dir under ~/.claude/projects/.
    Claude Code encodes the absolute project path by replacing non-alphanumeric
    runs with single dashes. Try that directly, then fall back to matching by
    the repo's leaf directory name. Returns None on a fresh install (no dir)."""
    base = Path.home() / ".claude" / "projects"
    if not base.is_dir():
        return None
    root = repo_root()
    encoded = re.sub(r"[^A-Za-z0-9]+", "-", str(root))
    direct = base / encoded / "memory"
    if direct.is_dir():
        return direct
    leaf = re.sub(r"[^A-Za-z0-9]+", "-", root.name).lower()
    if leaf:
        for d in sorted(base.iterdir()):
            if d.is_dir() and leaf in d.name.lower() and (d / "memory").is_dir():
                return d / "memory"
    return None


def count_md(directory: Path | None) -> int:
    if not directory or not directory.is_dir():
        return 0
    return sum(1 for _ in directory.glob("*.md"))


def cmd_mode(_args) -> None:
    auto = auto_memory_dir()
    auto_n = count_md(auto)
    harness = repo_root() / get_path("memory_dir")
    harness_n = count_md(harness)
    total = auto_n + harness_n
    print(f"MODE={'LIGHT' if total < LIGHT_THRESHOLD else 'FULL'}")
    print(f"AUTO_MEMORY={auto if auto else 'NONE'}")
    print(f"AUTO_FILES={auto_n}")
    print(f"HARNESS_FILES={harness_n}")
    print(f"TOTAL={total}")


def cmd_graduation(_args) -> None:
    projects_dir = repo_root() / get_path("projects_dir")
    if not projects_dir.is_dir():
        return
    now = time.time()
    flagged = 0
    for pd in sorted(projects_dir.iterdir()):
        if not pd.is_dir():
            continue
        claude_md = pd / "CLAUDE.md"
        if not claude_md.exists():
            continue
        if parse_frontmatter(claude_md).get("status") != "shipped":
            continue
        try:
            out = subprocess.run(
                ["git", "log", "--since=30 days ago", "--oneline", "--", str(pd)],
                cwd=str(repo_root()), capture_output=True, text=True, timeout=15,
            )
            commits = sum(1 for line in out.stdout.splitlines() if line.strip())
        except Exception:
            commits = 0
        build_state = pd / "build-state.md"
        age_days = int((now - build_state.stat().st_mtime) // 86400) if build_state.exists() else 0
        if commits >= GRADUATION_COMMITS and age_days >= GRADUATION_STALE_DAYS:
            slug = parse_frontmatter(claude_md).get("slug") or pd.name
            print(
                f"{slug}: status: shipped, {commits} commits in last 30d, "
                f"build-state.md last touched {age_days} days ago. "
                f"Consider /build full {slug} (sets status: live) or edit CLAUDE.md status: live."
            )
            flagged += 1
    if flagged == 0:
        print("No V0-graduation candidates.", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="Deterministic /curate helpers")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("mode", help="count memory files -> LIGHT/FULL").set_defaults(func=cmd_mode)
    sub.add_parser("graduation", help="flag shipped projects in real use").set_defaults(func=cmd_graduation)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
