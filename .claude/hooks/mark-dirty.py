#!/usr/bin/env python3
"""PostToolUse hook. Touches .claude/session-dirty when a harness file is written.

Fires on Write|Edit|MultiEdit|NotebookEdit (per matcher in settings.json).
Skips silently when:
  - A FRESH skill lockfile exists (.claude/.doc-sync-running or
    .claude/.curate-running) — those skills own their writes and commit or
    clear markers themselves. Fresh = mtime under LOCK_TTL_SECONDS. A stale
    lockfile (crashed skill) is ignored AND removed, otherwise one crash
    would silently disable this hook — and with it the PreCompact gate —
    forever.
  - The written path is outside the harness allow-list (vera-projects/ etc.)

Always exits 0 — failure here MUST NOT block the user's edit. Any exception
is logged to stderr (visible in Claude Code's hook diagnostics) and swallowed.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

HARNESS_PREFIXES = (".claude", "vera-system")
HARNESS_ROOT_FILES = {"CLAUDE.md", "README.md", "ROADMAP.md"}
LOCKFILES = (".doc-sync-running", ".curate-running")
LOCK_TTL_SECONDS = 3600  # doc-sync and curate finish in minutes; 1h = crashed


def _validate_repo_root(candidate: Path) -> Path | None:
    """A genuine OpenVera repo root contains THIS hook file at the expected
    path. Without this, a poisoned CLAUDE_PROJECT_DIR writes the dirty marker
    to a different root than the PreCompact/Stop gates read (same pattern as
    pre-compact.py)."""
    try:
        candidate = candidate.resolve()
        expected_self = (candidate / ".claude" / "hooks" / "mark-dirty.py").resolve()
        if expected_self == Path(__file__).resolve():
            return candidate
    except OSError:
        pass
    return None


def repo_root() -> Path | None:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        validated = _validate_repo_root(Path(env))
        if validated:
            return validated
    fallback = Path(__file__).resolve().parent.parent.parent
    return _validate_repo_root(fallback)


def lock_is_fresh(lock: Path, now: float, ttl: float = LOCK_TTL_SECONDS) -> bool:
    """Pure-ish check, unit-tested: honor a lockfile only while it's fresh.
    Missing file → False. Stat errors → False (treat as no lock)."""
    try:
        return (now - lock.stat().st_mtime) < ttl
    except OSError:
        return False


def skill_lock_active(repo: Path) -> bool:
    """True if any skill lockfile is fresh. Stale lockfiles are removed."""
    now = time.time()
    for name in LOCKFILES:
        lock = repo / ".claude" / name
        if not lock.exists():
            continue
        if lock_is_fresh(lock, now):
            return True
        try:
            lock.unlink()
            print(f"mark-dirty: removed stale lockfile {name}", file=sys.stderr)
        except OSError:
            pass
    return False


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
        if repo is None:
            print("mark-dirty: cannot resolve a valid repo root, skipping", file=sys.stderr)
            return 0
        if skill_lock_active(repo):
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
