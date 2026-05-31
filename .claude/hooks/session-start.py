#!/usr/bin/env python3
"""
SessionStart hook — boot health check, curate reminder, rotating tips.

Checks: bootstrap state, config validity, curate freshness.
Injects one contextual line + one rotating tip on healthy boot. Loud on errors.
"""
import json
import sys
import hashlib
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]    # .claude/hooks/ → repo root
SYSTEM_DIR = REPO_ROOT / "vera-system"

raw = sys.stdin.read()
try:
    input_data = json.loads(raw) if raw.strip() else {}
except (json.JSONDecodeError, ValueError):
    input_data = {}

errors = []
warnings = []

# --- Tips pool ---
TIPS = [
    "/scout for quick answers → /consult for tradeoffs → /research for evidence.",
    "Have a vague idea? /start-vague. Know what you want? /build new.",
    "/consult is free. Use it before any decision with real stakes.",
    "Patterns go in patterns.md. If it's not in a file, it doesn't exist after reboot.",
    "config.json controls all paths and models. One file, everything changes.",
    "/curate consolidates memory weekly. Boot hook auto-spawns it when overdue.",
    "/improve measures a skill, finds failures, and fixes its own instructions.",
    "Ideas go in two places: ideas.md for depth, your head for excitement.",
]


def pick_tip():
    """Pick a tip based on today's date. Same tip all day, different tomorrow."""
    today = datetime.now().strftime("%Y-%m-%d")
    index = int(hashlib.md5(today.encode()).hexdigest(), 16) % len(TIPS)
    return TIPS[index]


# --- Check 1: Bootstrap ---
bootstrapped = REPO_ROOT / ".claude" / "bootstrapped"
if not bootstrapped.exists():
    print(json.dumps({
        "additionalContext": "FIRST RUN: Read vera-system/first-run.md and follow setup instructions before doing anything else."
    }))
    sys.exit(0)

# --- Check 2: Config ---
config_path = SYSTEM_DIR / "config.json"
if not config_path.exists():
    errors.append("CONFIG MISSING: Run bootstrap.sh or create vera-system/config.json.")
else:
    try:
        json.loads(config_path.read_text())
    except json.JSONDecodeError:
        errors.append("CONFIG BROKEN: vera-system/config.json is invalid JSON. Fix before proceeding.")

# --- Check 3: Curate freshness ---
curate_file = REPO_ROOT / ".claude" / "last-curate-date"
curate_age = None
if curate_file.exists():
    try:
        curate_date = datetime.strptime(curate_file.read_text().strip(), "%Y-%m-%d")
        curate_age = (datetime.now() - curate_date).days
        if curate_age > 7:
            # Imperative directive — earlier "spawn /curate as background agent"
            # was a soft warning. Claude often skipped it on busy boots, so
            # /curate effectively never auto-fired. This injects the exact Agent
            # call template as the first-action instruction. Still soft (Claude
            # can ignore it), but much more reliably acted on than a one-liner.
            warnings.append(
                f"Curate overdue ({curate_age} days). BEFORE responding to the user, "
                f"spawn this as your first action so /curate runs in the background while you work: "
                f"Agent(subagent_type=\"general-purpose\", description=\"weekly curate\", "
                f"prompt=\"Run /curate per .claude/skills/curate/SKILL.md. "
                f"Background mode — do not engage the user.\", run_in_background=true) "
                f"Then continue with the user's request."
            )
    except ValueError:
        pass


def extract_state_summary():
    """Pull STATUS, SPRINT, and Next items from state.md. Return None if unavailable."""
    state_path = SYSTEM_DIR / "state.md"
    if not state_path.exists():
        return None
    try:
        text = state_path.read_text()
    except (OSError, UnicodeDecodeError):
        return None

    lines = text.splitlines()
    summary_parts = []

    # STATUS and SPRINT lines (bold markdown like **STATUS:** ...)
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("**STATUS:**") or stripped.startswith("**SPRINT:**"):
            summary_parts.append(stripped.replace("**", ""))

    # Next section — first 3 bullets
    in_next = False
    next_items = []
    for line in lines:
        if line.strip().startswith("## Next"):
            in_next = True
            continue
        if in_next:
            if line.strip().startswith("## "):  # next heading — done
                break
            if line.strip().startswith("- "):
                next_items.append(line.strip()[2:])
                if len(next_items) >= 3:
                    break

    if next_items:
        summary_parts.append("NEXT:")
        summary_parts.extend(f"  - {item}" for item in next_items)

    return "\n".join(summary_parts) if summary_parts else None


# --- Output ---
tip = pick_tip()
state_summary = extract_state_summary()

if errors:
    output = "\n".join(errors)
    if warnings:
        output += "\n" + "\n".join(warnings)
    print(json.dumps({"additionalContext": output}))
    sys.exit(0)

# Healthy or warning path — assemble full boot context
if warnings:
    header = f"OpenVera online. {' '.join(warnings)}"
else:
    header = f"OpenVera online. Last curate: {curate_age}d ago." if curate_age is not None else "OpenVera online. First session, curate triggers in 7 days."

parts = [header, f"TIP: {tip}"]
if state_summary:
    parts.append("---")
    parts.append(state_summary)

print(json.dumps({"additionalContext": "\n".join(parts)}))
