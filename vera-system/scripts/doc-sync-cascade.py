#!/usr/bin/env python3
"""Detect which files need cascade updates based on git changes.

Usage: python3 scripts/doc-sync-cascade.py [vera-system-path]
Output: JSON list of {changed, update} pairs.
"""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]

# Triggers and targets. Path strings starting with ".claude/" are at the
# repo root; everything else is relative to vera-system/.
CASCADE_RULES = {
    ".claude/skills/": [".claude/skills/README.md"],
    ".claude/agents/": [".claude/skills/README.md"],
    ".claude/commands/": [".claude/skills/README.md"],
    "memory/patterns.md": ["state.md"],
    "config.json": ["CLAUDE.md"],
}


def _resolve_target(target: str, base_path: str) -> str:
    """Targets under .claude/ live at repo root; others are relative to base_path."""
    if target.startswith(".claude/"):
        return target
    return f"{base_path}/{target}"


def _run_git(args, warnings):
    """Run a git command from repo root. Returns split stdout lines, or
    [] on failure with a warning appended (instead of silently swallowing)."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True, text=True, timeout=10,
            cwd=str(REPO_ROOT),
        )
    except (subprocess.SubprocessError, OSError) as exc:
        warnings.append(f"git {' '.join(args)} failed to launch: {exc}")
        return []
    if result.returncode != 0:
        warnings.append(
            f"git {' '.join(args)} exited {result.returncode}: "
            f"{result.stderr.strip()[:200]}"
        )
        return []
    if not result.stdout.strip():
        return []
    return result.stdout.strip().split("\n")


def get_changed_files(warnings):
    """Get files changed since last commit (staged + unstaged + untracked).

    Warnings list is mutated with any git errors so the caller can surface
    them — earlier versions silently turned every failure into an empty set,
    which made cron-driven cascades silently no-op when git was unhappy.
    """
    files = set()
    files.update(_run_git(["diff", "--name-only", "HEAD"], warnings))
    files.update(_run_git(["diff", "--name-only", "--cached"], warnings))
    files.update(_run_git(["ls-files", "--others", "--exclude-standard"], warnings))
    return {f for f in files if f}


def detect_cascades(changed_files, base_path="vera-system"):
    """Map changed files to cascade targets."""
    cascades = []
    seen_targets = set()

    for changed in changed_files:
        for trigger, targets in CASCADE_RULES.items():
            if trigger in changed:
                for target in targets:
                    full_target = _resolve_target(target, base_path)
                    if full_target not in seen_targets:
                        cascades.append({
                            "changed": changed,
                            "update": full_target,
                            "reason": f"file in {trigger} changed"
                        })
                        seen_targets.add(full_target)

    # Check for new skill/agent creation (untracked SKILL.md or agent .md)
    for changed in changed_files:
        if "SKILL.md" in changed or ".claude/agents/" in changed:
            target = _resolve_target(".claude/skills/README.md", base_path)
            if target not in seen_targets:
                cascades.append({
                    "changed": changed,
                    "update": target,
                    "reason": "new skill or agent created"
                })
                seen_targets.add(target)

    return cascades


def main():
    warnings = []
    changed = get_changed_files(warnings)
    if not changed:
        payload = {"cascades": [], "message": "No changes detected"}
        if warnings:
            payload["warnings"] = warnings
        print(json.dumps(payload))
        return

    cascades = detect_cascades(changed)
    payload = {
        "changed_files": sorted(changed),
        "cascades": cascades,
        "cascade_count": len(cascades),
    }
    if warnings:
        payload["warnings"] = warnings
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
