#!/usr/bin/env bash
# Vera Bootstrap — First-boot setup
# Run once after cloning to personalize your harness.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$SCRIPT_DIR"
SYSTEM_DIR="$ROOT_DIR/vera-system"

# --- Interactive input source ---
# Under `curl ... | bash` (or when install.sh hands off), stdin is the download
# pipe sitting at EOF — so a plain `read` returns nothing and every prompt fails
# silently. The classic symptom: "Name is required" with no chance to type.
# Read prompts from the controlling terminal (/dev/tty) instead. If there is
# genuinely no terminal (CI / headless), fall back to non-interactive defaults
# rather than quitting.
#
# Note: test by actually OPENING /dev/tty, not `[[ -r /dev/tty ]]` — the device
# node can stat as readable yet fail to open ("Device not configured") in CI and
# sandboxed shells, which would otherwise re-trigger the very quit we're fixing.
if ( : < /dev/tty ) 2>/dev/null; then
  TTY_IN=/dev/tty
  INTERACTIVE=1
else
  TTY_IN=/dev/null
  INTERACTIVE=0
fi

# Detect a WORKING Python 3.8+ interpreter for bootstrap's own use (config
# regen, key checks, doctor). "Exists" is not enough: a broken install — e.g. a
# Homebrew python whose stdlib C-extensions fail to load — passes a bare
# `command -v` and then dies later with a raw traceback. So for each candidate
# we (1) confirm the version and (2) smoke-test that it can import the stdlib
# modules OpenVera actually uses, falling back to the next one if not. We also
# try common absolute paths (e.g. macOS's /usr/bin/python3) because PATH may
# shadow a working interpreter with a broken one of the same name. Windows
# (Git Bash) typically ships 'python' or 'py' rather than 'python3'.
PYTHON_CMD=""
PY_DIAG=""
for cand in python3 python py /usr/bin/python3 /usr/local/bin/python3; do
  command -v "$cand" >/dev/null 2>&1 || continue
  if ! "$cand" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' 2>/dev/null; then
    [[ -z "$PY_DIAG" ]] && PY_DIAG="$cand is too old ($("$cand" --version 2>&1)); OpenVera needs Python 3.8+."
    continue
  fi
  if ! "$cand" -c 'import json, ssl, urllib.request' 2>/dev/null; then
    [[ -z "$PY_DIAG" ]] && PY_DIAG="$cand ($("$cand" --version 2>&1)) can't load its own standard library — likely a broken Python install."
    continue
  fi
  PYTHON_CMD="$cand"
  break
done
if [[ -z "$PYTHON_CMD" ]]; then
  echo "  ✗ No working Python 3.8+ interpreter found (tried: python3, python, py)." >&2
  [[ -n "$PY_DIAG" ]] && echo "    $PY_DIAG" >&2
  echo "    Install Python 3.8+ from https://www.python.org/downloads/ and rerun." >&2
  exit 1
fi

# Record which interpreter won so we can show it to the user (see banner below).
PYTHON_VERSION="$("$PYTHON_CMD" --version 2>&1 | awk '{print $2}')"
PYTHON_PATH="$(command -v "$PYTHON_CMD")"

# ANSI colors (degrade gracefully on non-TTY)
if [[ -t 1 ]]; then
  BOLD=$'\033[1m'
  DIM=$'\033[2m'
  GOLD=$'\033[38;5;214m'
  BROWN=$'\033[38;5;130m'
  RESET=$'\033[0m'
else
  BOLD=""; DIM=""; GOLD=""; BROWN=""; RESET=""
fi

[[ -t 1 && -n ${TERM:-} ]] && clear
echo ""
echo "  ${BROWN}╔══════════════════════════════════════╗${RESET}"
echo "  ${BROWN}║${RESET}       ${GOLD}🐘  OpenVera Bootstrap${RESET}         ${BROWN}║${RESET}"
echo "  ${BROWN}╚══════════════════════════════════════╝${RESET}"
echo ""
echo "  ${DIM}Using Python ${PYTHON_VERSION}  (${PYTHON_PATH})${RESET}"
echo ""

# --- Step 1: Name ---
read -rp "What's your name? " USER_NAME < "$TTY_IN" || USER_NAME=""
if [[ -z "$USER_NAME" ]]; then
  if [[ "$INTERACTIVE" == "1" ]]; then
    echo "Name is required."
    exit 1
  fi
  # No terminal to ask — don't die; use a placeholder the user can edit later.
  USER_NAME="Builder"
  echo "  No terminal detected — defaulting name to '$USER_NAME' (edit vera-system/state.md to change)."
fi
echo ""

# --- Step 1b: User memory opt-in ---
# Default NO on Enter and in headless (INTERACTIVE=0) runs — the flag only
# turns on when a real human at a real terminal says yes. Same /dev/tty
# pattern as the key retry/skip/quit loops below.
USER_MEMORY="false"
if [[ "$INTERACTIVE" == "1" ]]; then
  read -rp "User memory file? (learns how to work with you — working-style notes only, never personal facts; you can read or edit it anytime) [y/N] " um_choice < "$TTY_IN" || um_choice="n"
  case "${um_choice:-n}" in
    [yY]*) USER_MEMORY="true" ;;
    *)     USER_MEMORY="false" ;;
  esac
fi
echo ""

# --- Pre-flight: Python dependencies ---
# OpenVera runs on the Python standard library alone, so normally there's
# nothing to install here — no pip, no PyPI, no PEP-668 wall, no broken-pip
# surprise. If a future requirements.txt lists real packages we install them
# BEST-EFFORT: a missing optional package degrades one skill, so it must never
# hard-fail the whole install (every other step in this script degrades too).
REQ_FILE="$SYSTEM_DIR/requirements.txt"
REAL_REQS=""
if [[ -f "$REQ_FILE" ]]; then
  REAL_REQS="$(grep -vE '^[[:space:]]*(#|$)' "$REQ_FILE" 2>/dev/null || true)"
fi
if [[ -z "$REAL_REQS" ]]; then
  echo "  ✓ No third-party packages needed — OpenVera uses only the Python standard library."
  echo ""
else
  echo "  Installing Python packages with '$PYTHON_CMD -m pip' (best-effort):"
  echo "        ${REAL_REQS//$'\n'/$'\n        '}"
  # --break-system-packages was added in pip 23 (PEP 668). Older pip rejects it
  # as unknown, so only pass it when supported.
  PIP_FLAGS=(install --user -q)
  PIP_MAJOR="$("$PYTHON_CMD" -m pip --version 2>/dev/null | awk '{print $2}' | cut -d. -f1)"
  if [[ "$PIP_MAJOR" =~ ^[0-9]+$ ]] && [[ "$PIP_MAJOR" -ge 23 ]]; then
    PIP_FLAGS=(install --user --break-system-packages -q)
  fi
  if "$PYTHON_CMD" -m pip "${PIP_FLAGS[@]}" -r "$REQ_FILE" >/dev/null 2>&1; then
    echo "  ✓ Python packages installed"
  else
    echo "  ⚠ Couldn't install some packages — skills that need them will say so when you run them."
    echo "    To try manually:  $PYTHON_CMD -m pip install -r $REQ_FILE"
  fi
  echo ""
fi

# --- Step 2: API Keys (optional) ---
echo "  API keys are optional. OpenVera makes no external calls on its own;"
echo "  keys are only used by scripts you explicitly trigger."
echo ""
echo "  Works without keys:"
echo "    /start-vague, /consult, /frame, /advisor, /curate, /doc-sync"
echo "    /scout (web search; Reddit falls back to lower-fidelity snippets)"
echo "    /build (ships fine, just unscored: the external judge is skipped)"
echo ""
echo "  Keys unlock:"
echo "    OpenRouter (openrouter.ai/keys)  /research, /improve scoring,"
echo "                                     /build's external scoring gate,"
echo "                                     /scout Reddit + YouTube discovery"
echo "    Google AI (aistudio.google.com/apikey, free)"
echo "                                     YouTube video analysis"
echo ""
echo "  ${BOLD}Paste keys below — or press Enter to skip API keys for now.${RESET}"
echo "  ${DIM}You can add them later by editing vera-system/.secrets.${RESET}"
echo ""

# -s suppresses echo so pasted secrets don't end up in terminal scrollback or
# screen recordings. -s also eats the trailing newline from Enter, so we print
# one ourselves after each read. Empty input still skips the key.
read -rsp "  OpenRouter API key (paste or Enter to skip): " OPENROUTER_KEY < "$TTY_IN" || OPENROUTER_KEY=""
echo
read -rsp "  Google AI API key  (paste or Enter to skip): " GOOGLE_KEY < "$TTY_IN" || GOOGLE_KEY=""
echo
echo ""

# --- Step 3: Populate templates ---
echo "Setting up your harness..."

# Personal files ship as *.template and get copied to their working paths on first run.
# Keeps user data (name, state, memory, ideas, roadmap) out of accidental `git add .`
# commits back to the harness upstream. Only copies if the actual file is missing —
# re-running bootstrap won't clobber personalizations.
copy_template_if_missing() {
  local tmpl="$1"
  local dest="${tmpl%.template}"
  if [[ ! -f "$dest" && -f "$tmpl" ]]; then
    cp "$tmpl" "$dest"
  fi
}

copy_template_if_missing "$SYSTEM_DIR/relationships/user.md.template"
copy_template_if_missing "$SYSTEM_DIR/state.md.template"
copy_template_if_missing "$SYSTEM_DIR/memory/MEMORY.md.template"
copy_template_if_missing "$SYSTEM_DIR/memory/lessons.md.template"
copy_template_if_missing "$SYSTEM_DIR/ideas.md.template"
copy_template_if_missing "$SYSTEM_DIR/ROADMAP.md.template"
copy_template_if_missing "$SYSTEM_DIR/inbox.md.template"
copy_template_if_missing "$SYSTEM_DIR/cockpit.md.template"

# User relationship file — safe replacement without sed escaping issues
USER_FILE="$SYSTEM_DIR/relationships/user.md"
CONTENT=$(cat "$USER_FILE")
printf '%s\n' "${CONTENT//\{\{USER_NAME\}\}/$USER_NAME}" > "$USER_FILE"

# State file — set today's date
TODAY=$(date +%Y-%m-%d)
STATE_FILE="$SYSTEM_DIR/state.md"
CONTENT=$(cat "$STATE_FILE")
printf '%s\n' "${CONTENT//YYYY-MM-DD/$TODAY}" > "$STATE_FILE"

# Secrets file — write directly, no sed
SECRETS_FILE="$SYSTEM_DIR/.secrets"
# Verify keys BEFORE writing .secrets so a re-prompted key actually lands in the
# file. Pass keys via env var (not string interpolation) so quotes/newlines can't
# break the inline Python.

# OpenRouter — loop until verified, network error, or user skips.
while [[ -n "$OPENROUTER_KEY" ]]; do
  echo "  Verifying OpenRouter key..."
  HTTP_STATUS=$(OPENROUTER_KEY="$OPENROUTER_KEY" SYSTEM_DIR="$SYSTEM_DIR" "$PYTHON_CMD" -c "
import os, sys
sys.path.insert(0, os.path.join(os.environ['SYSTEM_DIR'], 'scripts'))
try:
    import http_util
    key = os.environ['OPENROUTER_KEY']
    r = http_util.get('https://openrouter.ai/api/v1/auth/key',
        headers={'Authorization': 'Bearer ' + key}, timeout=10)
    print(r.status_code)
except Exception:
    print('0')
" 2>/dev/null)
  if [[ "$HTTP_STATUS" == "200" ]]; then
    echo "  ✓ OpenRouter key verified"
    break
  elif [[ "$HTTP_STATUS" == "0" ]]; then
    echo "  ⚠ Could not reach OpenRouter (network issue). Saving anyway — verify later."
    break
  else
    echo "  ✗ OpenRouter key returned HTTP $HTTP_STATUS (likely 401 invalid)."
    read -rp "    [r]etry, [s]kip, [q]uit? " or_choice < "$TTY_IN" || or_choice="s"
    case "${or_choice:-s}" in
      [rR]) read -rsp "    OpenRouter API key: " OPENROUTER_KEY < "$TTY_IN" || OPENROUTER_KEY=""; echo ;;
      [sS]) OPENROUTER_KEY=""; echo "    Skipped — features needing OpenRouter will degrade gracefully."; break ;;
      [qQ]) echo "  Bootstrap aborted."; exit 1 ;;
      *)    echo "    Choose r, s, or q." ;;
    esac
  fi
done

# Google AI — same retry pattern. Hits /v1beta/models which is free and 200-on-valid.
while [[ -n "$GOOGLE_KEY" ]]; do
  echo "  Verifying Google AI key..."
  HTTP_STATUS=$(GOOGLE_KEY="$GOOGLE_KEY" SYSTEM_DIR="$SYSTEM_DIR" "$PYTHON_CMD" -c "
import os, sys
sys.path.insert(0, os.path.join(os.environ['SYSTEM_DIR'], 'scripts'))
try:
    import http_util
    key = os.environ['GOOGLE_KEY']
    r = http_util.get('https://generativelanguage.googleapis.com/v1beta/models',
        params={'key': key}, timeout=10)
    print(r.status_code)
except Exception:
    print('0')
" 2>/dev/null)
  if [[ "$HTTP_STATUS" == "200" ]]; then
    echo "  ✓ Google AI key verified"
    break
  elif [[ "$HTTP_STATUS" == "0" ]]; then
    echo "  ⚠ Could not reach Google AI (network issue). Saving anyway — verify later."
    break
  else
    echo "  ✗ Google AI key returned HTTP $HTTP_STATUS (likely invalid)."
    read -rp "    [r]etry, [s]kip, [q]uit? " ga_choice < "$TTY_IN" || ga_choice="s"
    case "${ga_choice:-s}" in
      [rR]) read -rsp "    Google AI API key: " GOOGLE_KEY < "$TTY_IN" || GOOGLE_KEY=""; echo ;;
      [sS]) GOOGLE_KEY=""; echo "    Skipped — YouTube video analysis will be unavailable."; break ;;
      [qQ]) echo "  Bootstrap aborted."; exit 1 ;;
      *)    echo "    Choose r, s, or q." ;;
    esac
  fi
done

# Now write .secrets with verified keys (if any remain).
if [[ -n "$OPENROUTER_KEY" ]] || [[ -n "$GOOGLE_KEY" ]]; then
  # umask 077 in a subshell so the file is created mode 600 from inception.
  # Without it, `> file` creates with the default umask (often 644 — world
  # readable) and chmod tightens AFTER, leaving a brief window where another
  # local user could read the freshly-pasted secret.
  (
    umask 077
    printf '%s\n' \
      "# Vera Secrets — generated by bootstrap.sh" \
      "# This file is gitignored. Never commit it." \
      "" \
      "OPENROUTER_API_KEY=$OPENROUTER_KEY" \
      "GOOGLE_AI_API_KEY=$GOOGLE_KEY" \
      > "$SECRETS_FILE"
  )
  # Defense-in-depth: re-tighten if the file already existed with looser perms.
  # chmod is a no-op on NTFS under Git Bash, absent on pure Windows; guard so
  # bootstrap doesn't crash on platforms where it isn't available.
  if command -v chmod >/dev/null 2>&1; then
    chmod 600 "$SECRETS_FILE" 2>/dev/null || true
  fi
  echo "  Created .secrets (gitignored)"
fi

# Create output directories (defaults — overridable in vera-system/config.json)
mkdir -p "$ROOT_DIR/vera-projects"/{projects,research-output}

# Ensure config.json exists. Ships with defaults; never overwrite user customizations.
# If missing (e.g., partial clone), regenerate from vera_config.py defaults.
# Pass paths via environment, NOT string interpolation, so they survive spaces and quotes.
CONFIG_FILE="$SYSTEM_DIR/config.json"
if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "  config.json missing — regenerating from defaults..."
  SYSTEM_DIR="$SYSTEM_DIR" CONFIG_FILE="$CONFIG_FILE" "$PYTHON_CMD" << 'PYEOF' || echo "  WARNING: could not regenerate config.json. Check vera-system/scripts/vera_config.py manually."
import os, sys, json, pathlib
sys.path.insert(0, os.path.join(os.environ['SYSTEM_DIR'], 'scripts'))
from vera_config import DEFAULTS
target = pathlib.Path(os.environ['CONFIG_FILE'])
target.write_text(json.dumps(DEFAULTS, indent=2) + '\n')
print(f"  Wrote {target}")
PYEOF
fi

# Write the user-memory opt-in into config.json explicitly, every bootstrap
# run — fresh installs must never rely on the grandfathered "key absent"
# default (that fallback exists for installs that predate this flag, not
# for new ones). Preserves every other key already in the file.
USER_MEMORY="$USER_MEMORY" CONFIG_FILE="$CONFIG_FILE" "$PYTHON_CMD" << 'PYEOF' || echo "  WARNING: could not write user_memory flag to config.json."
import json, os, pathlib
target = pathlib.Path(os.environ['CONFIG_FILE'])
value = os.environ['USER_MEMORY'] == 'true'
try:
    data = json.loads(target.read_text())
except (OSError, json.JSONDecodeError):
    data = {}
data['user_memory'] = value
target.write_text(json.dumps(data, indent=2) + '\n')
print(f"  user_memory: {value}")
PYEOF

# Create conversations directory marker
touch "$SYSTEM_DIR/conversations/.gitkeep"

# Curate timestamp — seed to today so first curate triggers in 7 days
mkdir -p "$ROOT_DIR/.claude"
echo "$TODAY" > "$ROOT_DIR/.claude/last-curate-date"

# Bootstrap marker — tells CLAUDE.md to skip first-run.md
echo "bootstrapped" > "$ROOT_DIR/.claude/bootstrapped"

# Migration: earlier bootstraps wrote a settings.local.json duplicating every
# hook with the detected interpreter. Claude Code MERGES hooks across the two
# settings files (no override mechanism), so keeping the old file would run
# every hook twice now that settings.json carries its own interpreter-fallback
# chain. If the file looks bootstrap-generated (only touches our hooks dir),
# park it as .bak instead of deleting — reversible, and user-authored settings
# survive untouched.
LOCAL_SETTINGS="$ROOT_DIR/.claude/settings.local.json"
if [[ -f "$LOCAL_SETTINGS" ]] && grep -q '\.claude/hooks/' "$LOCAL_SETTINGS"; then
  mv "$LOCAL_SETTINGS" "$LOCAL_SETTINGS.bak"
  echo "  Retired legacy settings.local.json (hooks now self-select an interpreter); saved as settings.local.json.bak"
fi

# --- Health check ---
echo ""
echo "  Running health check..."
# Capture the exit code without aborting bootstrap (doctor: 0 = clean, 2 = warnings only).
DOCTOR_RC=0
"$PYTHON_CMD" "$SYSTEM_DIR/scripts/doctor.py" || DOCTOR_RC=$?

if [[ "$DOCTOR_RC" -eq 0 || "$DOCTOR_RC" -eq 2 ]]; then
  # Healthy (or warnings only): clear to the clean "ready" screen.
  sleep 1
  [[ -t 1 && -n ${TERM:-} ]] && clear
else
  # Real failure: keep the doctor output on screen so the user can act on it.
  echo ""
  echo "  Health check reported a problem (exit $DOCTOR_RC). Review the output above before continuing."
  echo ""
fi
echo ""
echo "  ${GOLD}🐘  Your harness is ready, $USER_NAME.${RESET}"
echo ""
echo "  ┌─────────────────────────────────────────────────────┐"
echo "  │  Core Tools                                         │"
echo "  ├──────────────────┬──────────────────────────────────┤"
echo "  │ /build new       │ Ship a V0 (resumable sessions)   │"
echo "  │ /build full      │ Full SDLC — PRD to production    │"
echo "  │ /scout           │ Quick answers (2-3 min, default) │"
echo "  │ /research        │ Deep multi-model research        │"
echo "  │ /improve         │ Measure and improve any skill    │"
echo "  │ /curate          │ Consolidate memory (weekly)      │"
echo "  │ /doc-sync        │ Save session state (run at end)  │"
echo "  ├──────────────────┼──────────────────────────────────┤"
echo "  │ doctor.py        │ Self-audit harness health        │"
echo "  └──────────────────┴──────────────────────────────────┘"
echo ""
echo "  ${BROWN}──────────────────────────────────────────────────────${RESET}"
# If user is already inside the project dir (most common — they ran bootstrap
# from inside it), skip the redundant cd. Otherwise print absolute path.
if [[ "$PWD" == "$ROOT_DIR" ]]; then
  echo "  ${BOLD}NEXT:${RESET}  claude"
else
  echo "  ${BOLD}NEXT:${RESET}  cd \"$ROOT_DIR\" && claude"
fi
echo ""
echo "         Then run:  ${GOLD}${BOLD}/start-vague${RESET}"
echo ""
echo "         ${DIM}That's the front door. It figures out what you${RESET}"
echo "         ${DIM}actually need and routes you to the right skill.${RESET}"
echo "  ${BROWN}──────────────────────────────────────────────────────${RESET}"
echo ""
echo "  ${GOLD}${BOLD}Recommended MCPs${RESET} (run each once, any order):"
echo "    claude mcp add playwright -- npx @playwright/mcp@latest    ${DIM}# /build browser tests${RESET}"
echo "    claude mcp add context7   -- npx -y @upstash/context7-mcp  ${DIM}# /research, /build docs${RESET}"
echo "    ${DIM}# UI design? Use Claude Design (claude.ai, Pro+) — exports handoff for /build${RESET}"
echo ""

# Remind about skipped keys (only if at least one is missing)
if [[ -z "$OPENROUTER_KEY" || -z "$GOOGLE_KEY" ]]; then
  if [[ -z "$OPENROUTER_KEY" && -z "$GOOGLE_KEY" ]]; then
    skipped="OpenRouter + Google AI"
  elif [[ -z "$OPENROUTER_KEY" ]]; then
    skipped="OpenRouter"
  else
    skipped="Google AI"
  fi
  echo "  ${DIM}Skipped keys:${RESET} $skipped. Add later by editing"
  echo "    ${DIM}vera-system/.secrets${RESET}"
  echo ""
fi

echo "  ${DIM}Customize later:${RESET}"
echo "    vera-system/who-i-am/voice.md       ${DIM}(communication style)${RESET}"
echo "    vera-system/relationships/user.md   ${DIM}(your context)${RESET}"
echo "    vera-system/memory/patterns.md      ${DIM}(patterns from real use)${RESET}"
echo ""
