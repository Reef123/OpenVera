#!/usr/bin/env python3
"""
PostCompact hook — re-inject core context after context compression.

Injects the three Core tier files:
  - state.md (where you are)
  - patterns.md (how to think)
  - user.md (who you're helping — name, relationship context)
"""
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]    # .claude/hooks/ → repo root
SYSTEM_DIR = REPO_ROOT / "vera-system"

# Pull projects_dir from config.json so this hook stays in sync if the
# user moves project output to a non-default location.
sys.path.insert(0, str(SYSTEM_DIR / "scripts"))
try:
    from vera_config import get_path  # noqa: E402
    PROJECTS_DIR = REPO_ROOT / get_path("projects_dir")
except Exception:
    # Hook must never crash the session — fall back to default layout.
    PROJECTS_DIR = REPO_ROOT / "vera-projects" / "projects"

raw = sys.stdin.read()
try:
    input_data = json.loads(raw) if raw.strip() else {}
except (json.JSONDecodeError, ValueError):
    input_data = {}

sections = []

# --- State: where you are ---
state_file = SYSTEM_DIR / "state.md"
if state_file.exists():
    sections.append(state_file.read_text().strip())

# --- Patterns: how to think ---
patterns_file = SYSTEM_DIR / "memory" / "patterns.md"
if patterns_file.exists():
    sections.append(patterns_file.read_text().strip())

# --- User: who you're helping ---
user_file = SYSTEM_DIR / "relationships" / "user.md"
if user_file.exists():
    sections.append(user_file.read_text().strip())

# --- Active build state (pointer only) ---
if PROJECTS_DIR.exists():
    build_states = sorted(
        PROJECTS_DIR.glob("*/build-state.md"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    if build_states:
        latest = build_states[0]
        # Only mention if modified in the last 24 hours (likely active)
        from datetime import datetime
        age_hours = (datetime.now() - datetime.fromtimestamp(latest.stat().st_mtime)).total_seconds() / 3600
        if age_hours < 24:
            sections.append(f"ACTIVE BUILD: {latest} — read this to resume.")

if sections:
    print(json.dumps({"additionalContext": "\n\n---\n\n".join(sections)}))
else:
    print("{}")
