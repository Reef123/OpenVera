#!/usr/bin/env python3
"""
SessionStart hook — boot health check, curate reminder, rotating tips.

Checks: bootstrap state, config validity, curate freshness.
Injects one contextual line + one rotating tip on healthy boot. Loud on errors.

All side-effecting logic lives in main() (only runs under __main__) so the
pure helpers below can be imported and unit-tested without touching the real
repo's .claude/ lockfiles or blocking on stdin — see vera-system/tests/test_session_start.py.
"""
import json
import re
import sys
import hashlib
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]    # .claude/hooks/ → repo root
SYSTEM_DIR = REPO_ROOT / "vera-system"

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


def parse_running_timestamp(text):
    """Extract the ISO timestamp from a `.curate-running` lock's `RUNNING <ts>`
    content. Returns the raw timestamp string, or None if the file predates
    the RUNNING-content convention (empty, or a bare-touch leftover)."""
    match = re.search(r"RUNNING\s+(\S+)", text)
    return match.group(1) if match else None


def build_curate_crash_notice(ts):
    """ANY leftover `.curate-running` at boot is a crash — a new session means
    nothing from a prior session is legitimately still running, so there is
    no age gate on the message (contrast: private-tree curate reads this same
    lock with a >=1h gate; that gate does NOT apply to this cross-session
    boot path). Removal (Check 0 in main(), below) stays unconditional
    regardless — only this message is conditional on the lock having existed."""
    when = f" (started {ts})" if ts else ""
    return (
        f"CURATE CRASHED: the last /curate run did not complete{when} — "
        f"review `git diff vera-system/memory/` before committing over any "
        f"half-applied edits, then re-run /curate."
    )


def extract_state_summary(system_dir):
    """Pull STATUS, SPRINT, and Next items from state.md. Return None if unavailable."""
    state_path = system_dir / "state.md"
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


def main():
    raw = sys.stdin.read()
    try:
        json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        pass

    errors = []
    warnings = []

    # --- Check 0: Clear stale runtime markers from a prior session ---
    # Solo-user assumption: nothing from a previous session is legitimately
    # still running at boot. A crashed doc-sync/curate leaves lockfiles that
    # would make mark-dirty.py skip; a leftover .session-ending would mis-arm
    # the Stop gate on the first turn. session-dirty is intentionally NOT
    # cleared — unsynced edits stay unsynced across reboots until /doc-sync
    # runs.
    #
    # .curate-running gets special handling: before it's removed, read its
    # `RUNNING <ts>` content (if any) and build a crash notice. Removal itself
    # stays UNCONDITIONAL — making it conditional on age would let a <1h-old
    # crashed lock survive boot, which silently disables mark-dirty.py's
    # dirty-tracking (LOCK_TTL_SECONDS honors any lock under 60 min as "in
    # progress") and the PreCompact/Stop gates behind it until the lock ages out.
    crash_notice = None
    curate_lock = REPO_ROOT / ".claude" / ".curate-running"
    if curate_lock.exists():
        try:
            lock_text = curate_lock.read_text()
        except OSError:
            lock_text = ""
        crash_notice = build_curate_crash_notice(parse_running_timestamp(lock_text))

    for stale in (".session-ending", ".doc-sync-running", ".curate-running"):
        try:
            (REPO_ROOT / ".claude" / stale).unlink()
        except FileNotFoundError:
            pass
        except OSError:
            pass

    # --- Check 1: Bootstrap ---
    bootstrapped = REPO_ROOT / ".claude" / "bootstrapped"
    if not bootstrapped.exists():
        first_run_msg = "FIRST RUN: Read vera-system/first-run.md and follow setup instructions before doing anything else."
        if crash_notice:
            first_run_msg = crash_notice + "\n" + first_run_msg
        print(json.dumps({"additionalContext": first_run_msg}))
        return 0

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

    # --- Output ---
    tip = pick_tip()
    state_summary = extract_state_summary(SYSTEM_DIR)

    if errors:
        output = "\n".join(errors)
        if warnings:
            output += "\n" + "\n".join(warnings)
        output += "\nTell the user: fixes for common breakage are in RECOVERY.md at the repo root."
        if crash_notice:
            output = crash_notice + "\n" + output
        print(json.dumps({"additionalContext": output}))
        return 0

    # Healthy or warning path — assemble full boot context
    if warnings:
        header = f"OpenVera online. {' '.join(warnings)}"
    else:
        header = f"OpenVera online. Last curate: {curate_age}d ago." if curate_age is not None else "OpenVera online. First session, curate triggers in 7 days."

    parts = ([crash_notice] if crash_notice else []) + [header, f"TIP: {tip}"]

    # First real session (bootstrapped, but no session logs yet) — one clear
    # next action beats the rotating tip for someone who just installed.
    conversations_dir = SYSTEM_DIR / "conversations"
    has_logs = conversations_dir.is_dir() and any(conversations_dir.glob("[0-9]*.md"))
    if not has_logs:
        parts.append(
            "FIRST BUILD: suggest /start-vague (vague idea) or /build new <idea> (clear one) "
            "if the user seems unsure where to start."
        )

    if state_summary:
        parts.append("---")
        parts.append(state_summary)

    print(json.dumps({"additionalContext": "\n".join(parts)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
