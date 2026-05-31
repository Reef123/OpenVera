#!/usr/bin/env python3
"""PostToolUse hook. Touches .claude/session-dirty when a harness file is written.

Fires on Write|Edit|MultiEdit|NotebookEdit (per matcher in settings.json).
Skips silently when:
  - .claude/.doc-sync-running exists (doc-sync owns its own writes)
  - The written path is outside the harness allow-list (vera-projects/ etc.)

Always exits 0 — failure here MUST NOT block the user's edit. Any exception
is logged to stderr (visible in Claude Code's hook diagnostics) and swallowed.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HARNESS_PREFIXES = (".claude", "vera-system")
HARNESS_ROOT_FILES = {"CLAUDE.md", "README.md", "ROADMAP.md"}


def repo_root() -> Path:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parent.parent.parent


def is_harness_path(file_path: str, repo: Path, event_cwd: Path) -> bool:
    """Path matches the harness allow-list under repo root.

    Relative paths are resolved against event_cwd (the tool's CWD per the
    hook payload), NOT the hook process CWD which is unspecified.
    """
    raw = Path(file_path)
    target = raw if raw.is_absolute() else (event_cwd / raw)
    try:
        rel = target.resolve().relative_to(repo)
    except (ValueError, OSError):
        return False
    parts = rel.parts
    if not parts:
        return False
    if parts[0] in HARNESS_PREFIXES:
        return True
    if len(parts) == 1 and parts[0] in HARNESS_ROOT_FILES:
        return True
    return False


def main() -> int:
    try:
        repo = repo_root()
        if (repo / ".claude" / ".doc-sync-running").exists():
            return 0

        raw = sys.stdin.read()
        if not raw.strip():
            return 0
        event = json.loads(raw)
        tool_input = event.get("tool_input") or {}
        file_path = tool_input.get("file_path") or tool_input.get("notebook_path")
        if not file_path:
            return 0

        # Resolve relative paths against the event's cwd (tool CWD), not ours.
        event_cwd = Path(event.get("cwd") or os.getcwd()).resolve()

        if not is_harness_path(file_path, repo, event_cwd):
            return 0

        claude_dir = repo / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        (claude_dir / "session-dirty").touch()
    except Exception as exc:
        # Log to stderr (visible in Claude Code hook diagnostics) but never
        # block the user's edit by exiting nonzero.
        print(f"mark-dirty: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
