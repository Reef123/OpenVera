#!/usr/bin/env python3
"""Remind to update docs when user signals session end."""
import json
import sys
import re

raw_input = sys.stdin.read()

try:
    input_data = json.loads(raw_input) if raw_input.strip() else {}
    user_prompt = input_data.get("prompt", "").lower()
except (json.JSONDecodeError, ValueError, KeyError):
    user_prompt = ""

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

is_ending = any(re.search(pattern, user_prompt) for pattern in END_PATTERNS)

if is_ending:
    print(json.dumps({
        "message": "SESSION END: Run /doc-sync now. This updates state.md, creates a conversation log, syncs ROADMAP.md, and captures any new patterns. If it's not in a file, it doesn't exist after reboot."
    }))
else:
    print("{}")
