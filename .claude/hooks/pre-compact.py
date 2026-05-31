#!/usr/bin/env python3
"""PreCompact gate. Deterministic — replaces the prompt-based hook that broke
in non-REPL contexts ("Prompt stop hooks are not yet supported outside REPL").

Decision contract (PreCompact command-type hook):
  JSON on stdout is the authoritative signal. Exit code is supplementary.
  - block: emit {"decision":"block","reason":"..."} on stdout, exit 2
           (belt-and-suspenders: JSON gates, nonzero exit reinforces, stderr
            visible to the model)
  - allow: emit nothing, exit 0
  - error: exit 2 with stderr message (fail closed)

The session-dirty marker is set by .claude/hooks/mark-dirty.py on harness
edits and cleared by /doc-sync.
"""
# Required: `Path | None` (PEP 604) needs Python 3.10+ at runtime; the
# future import defers evaluation so this hook stays compatible with the
# system Python on older macOS installs. Do NOT remove without raising
# the minimum Python floor.
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _validate_repo_root(candidate: Path) -> Path | None:
    """A genuine OpenVera repo root contains THIS hook file at the
    expected path. Defends against CLAUDE_PROJECT_DIR poisoning that
    would otherwise silently bypass the gate (env points elsewhere ->
    marker absent -> allow)."""
    try:
        candidate = candidate.resolve()
        expected_self = (candidate / ".claude" / "hooks" / "pre-compact.py").resolve()
        if expected_self == Path(__file__).resolve():
            return candidate
    except OSError:
        pass
    return None


def repo_root() -> Path | None:
    """Resolve and validate the repo root.

    Trust CLAUDE_PROJECT_DIR only if it points at the repo containing this
    hook file. Otherwise fall back to __file__-relative resolution and
    validate that too. Returns None if neither resolves to a valid root
    (caller fails closed)."""
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        validated = _validate_repo_root(Path(env))
        if validated:
            return validated
    fallback = Path(__file__).resolve().parent.parent.parent
    return _validate_repo_root(fallback)


def main() -> int:
    root = repo_root()
    if root is None:
        print("pre-compact: cannot resolve a valid repo root", file=sys.stderr)
        return 2

    marker = root / ".claude" / "session-dirty"
    try:
        # is_file (not exists) — directories don't qualify as dirty markers.
        # Wrap in try/except so permission errors surface as block, not allow.
        dirty = marker.is_file()
    except OSError as exc:
        print(f"pre-compact: marker stat failed: {exc}", file=sys.stderr)
        return 2

    if dirty:
        payload = {
            "decision": "block",
            "reason": (
                "STOP. Run /doc-sync before compact. Session has unsynced "
                "edits — state.md, conversation log, ROADMAP.md need updates."
            ),
        }
        # Single atomic write + flush — no partial output on signal.
        sys.stdout.write(json.dumps(payload) + "\n")
        sys.stdout.flush()
        # Belt-and-suspenders: JSON is authoritative for PreCompact, but
        # nonzero exit reinforces the block signal across hook variants.
        return 2

    # Clean path: emit nothing, exit 0. Claude Code treats this as allow.
    return 0


if __name__ == "__main__":
    sys.exit(main())
