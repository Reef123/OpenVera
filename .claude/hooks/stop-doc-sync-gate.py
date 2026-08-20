#!/usr/bin/env python3
"""Stop-hook gate. Enforces /doc-sync when a session ends with unsynced
harness edits — the deterministic teeth behind the session-end reminder.

Block decision (all three must hold):
  1. .claude/.session-ending exists  — the user signaled an ending this turn
     (set by session-end-reminder.py on UserPromptSubmit pattern match)
  2. .claude/session-dirty exists    — harness edits not yet doc-synced
     (set by mark-dirty.py, cleared by /doc-sync Step 11)
  3. stop_hook_active is false       — not already continuing from this gate
     (Claude Code's loop-prevention flag; it also force-overrides after 8
     consecutive blocks as a backstop)

One-nag rule: the sentinel is DELETED at the moment the gate blocks. Without
this, a user who says "done" but keeps chatting would be blocked at every
subsequent turn end (stop_hook_active resets each user turn). One ending
signal = at most one forced doc-sync; a later ending signal re-arms cleanly.
PreCompact and the boot directive remain the backstops.

Fail-open by design — the opposite of pre-compact.py. Stop fires at EVERY
turn end, so a broken gate that fails closed would trap the user in every
conversation. A missed nag costs one reminder; PreCompact still guards the
actual data-loss event (compaction).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _validate_repo_root(candidate: Path) -> Path | None:
    """A genuine OpenVera repo root contains THIS hook file at the expected
    path. Defends against CLAUDE_PROJECT_DIR poisoning (same pattern as
    pre-compact.py)."""
    try:
        candidate = candidate.resolve()
        expected_self = (candidate / ".claude" / "hooks" / "stop-doc-sync-gate.py").resolve()
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


def should_block(ending: bool, dirty: bool, stop_hook_active: bool) -> bool:
    """Pure decision function — unit-tested in vera-system/tests/test_stop_gate.py."""
    return ending and dirty and not stop_hook_active


def main() -> int:
    raw = sys.stdin.read()
    try:
        event = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        event = {}
    stop_hook_active = bool(event.get("stop_hook_active"))

    root = repo_root()
    if root is None:
        # Fail open — see module docstring.
        print("stop-doc-sync-gate: cannot resolve repo root, allowing stop", file=sys.stderr)
        return 0

    sentinel = root / ".claude" / ".session-ending"
    marker = root / ".claude" / "session-dirty"
    try:
        ending = sentinel.is_file()
        dirty = marker.is_file()
    except OSError as exc:
        print(f"stop-doc-sync-gate: marker stat failed: {exc}, allowing stop", file=sys.stderr)
        return 0

    if not should_block(ending, dirty, stop_hook_active):
        return 0

    # One-nag rule: disarm before blocking so the gate cannot trap the turn
    # loop. Failure to delete = do NOT block (fail open), or the gate would
    # fire every turn until the filesystem recovers.
    try:
        sentinel.unlink()
    except OSError as exc:
        print(f"stop-doc-sync-gate: sentinel unlink failed: {exc}, allowing stop", file=sys.stderr)
        return 0

    payload = {
        "decision": "block",
        "reason": (
            "Session is ending with unsynced harness edits. Run /doc-sync now "
            "(state.md, conversation log, ROADMAP.md, patterns), then finish "
            "your reply. If /doc-sync already ran this turn, its marker "
            "cleanup may have failed — check .claude/session-dirty."
        ),
    }
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
