#!/usr/bin/env python3
"""UserPromptSubmit hook. Detects session-end phrases, injects a doc-sync
directive, and arms the Stop gate.

Two outputs on an end-pattern match:
  1. hookSpecificOutput.additionalContext — the directive the model sees.
     (The old {"message": ...} shape was NOT a recognized UserPromptSubmit
     field — Claude Code dropped it silently, so the reminder never reached
     the model. additionalContext is the documented injection path.)
  2. .claude/.session-ending sentinel — read by stop-doc-sync-gate.py, which
     blocks the turn-end if harness edits are still unsynced.

Never blocks the prompt; always exits 0.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


def repo_root() -> Path:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        candidate = Path(env)
        try:
            expected_self = (candidate / ".claude" / "hooks" / "session-end-reminder.py").resolve()
            if expected_self == Path(__file__).resolve():
                return candidate.resolve()
        except OSError:
            pass
    return Path(__file__).resolve().parent.parent.parent


END_PATTERNS = [
    # Explicit farewells (low false-positive)
    r"\b(bye|goodbye|good night|gotta go|see you|talk later|signing off)\b",
    # Session-end phrases — anchored to end of message or followed by punctuation/nothing
    # This prevents "i'm done with X" from matching while "i'm done" or "i'm done." still fire
    r"\b(we'?re done|i'?m done|all done|that'?s all|that'?s it|wrap up|call it a day|let'?s stop)\b[\s.!?]*$",
    r"\b(thanks,? that'?s)\b",
    # System triggers
    r"(compact|doc-sync)",
]


def main() -> int:
    raw = sys.stdin.read()
    try:
        input_data = json.loads(raw) if raw.strip() else {}
        user_prompt = input_data.get("prompt", "").lower()
    except (json.JSONDecodeError, ValueError, KeyError):
        user_prompt = ""

    is_ending = any(re.search(pattern, user_prompt) for pattern in END_PATTERNS)

    if not is_ending:
        print("{}")
        return 0

    # Arm the Stop gate. Failure to write the sentinel must not block the
    # prompt — the additionalContext directive still fires.
    try:
        claude_dir = repo_root() / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        (claude_dir / ".session-ending").touch()
    except OSError as exc:
        print(f"session-end-reminder: sentinel write failed: {exc}", file=sys.stderr)

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": (
                "SESSION END DETECTED: Run /doc-sync NOW, before or alongside "
                "your reply. It updates state.md, creates the conversation log, "
                "syncs ROADMAP.md, and captures new patterns. If it's not in a "
                "file, it doesn't exist after reboot. A Stop gate will hold the "
                "turn open if harness edits are still unsynced."
            ),
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
