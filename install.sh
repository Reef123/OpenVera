#!/usr/bin/env bash
# OpenVera one-line installer.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/Reef123/OpenVera/main/install.sh | bash
#   curl -fsSL https://raw.githubusercontent.com/Reef123/OpenVera/main/install.sh | bash -s -- ~/projects/my-harness
#
# What it does:
#   1. Verifies prereqs (git, python3, claude CLI)
#   2. Clones OpenVera into the target dir (default: ./openvera)
#   3. Hands off to ./bootstrap.sh for interactive setup
#
# This script is intentionally tiny — all real setup logic lives in bootstrap.sh
# in the repo, so installer and bootstrap stay in sync.

set -euo pipefail

# OPENVERA_REPO_URL override exists for CI smoke tests (point at a local
# checkout via file://) and forks. Default is the canonical repo.
REPO_URL="${OPENVERA_REPO_URL:-https://github.com/Reef123/OpenVera.git}"

# True if cwd has no entries other than OS junk (Finder writes .DS_Store the moment
# a folder is opened, so a freshly-made folder isn't empty per `ls -A`).
# Subshell body keeps the shopt changes local; glob handles non-alphanumeric names.
dir_is_effectively_empty() (
  shopt -s nullglob dotglob
  for entry in *; do
    case "$entry" in
      .DS_Store|Thumbs.db|.localized|desktop.ini) continue ;;
      *) return 1 ;;
    esac
  done
  return 0
)

# Target directory:
#   explicit arg  -> use it
#   empty cwd     -> install in place (user already made/entered a folder for it)
#   non-empty cwd -> create an ./openvera subfolder
# This avoids the surprise of `mkdir Openvera && cd Openvera && curl…` landing in
# Openvera/openvera.
if [[ $# -ge 1 ]]; then
  TARGET="$1"
elif dir_is_effectively_empty; then
  TARGET="."
else
  TARGET="openvera"
fi

red()   { printf "\033[31m%s\033[0m\n" "$*"; }
green() { printf "\033[32m%s\033[0m\n" "$*"; }
bold()  { printf "\033[1m%s\033[0m\n"  "$*"; }

bold ""
bold "  OpenVera installer"
bold ""

# --- Prereq checks ---
# Just confirm the tools EXIST here; bootstrap.sh does the authoritative
# working-interpreter selection (version + stdlib smoke-test + fallback). Accept
# any of python3/python/py so we don't wrongly reject Windows (Git Bash), which
# often ships only 'python' or 'py'.
have_python() {
  local c
  for c in python3 python py; do
    command -v "$c" >/dev/null 2>&1 && return 0
  done
  return 1
}
missing=()
command -v git      >/dev/null 2>&1 || missing+=("git")
have_python                         || missing+=("python3")
command -v claude   >/dev/null 2>&1 || missing+=("claude (Claude Code CLI)")

if [[ ${#missing[@]} -gt 0 ]]; then
  red "  Missing prereqs: ${missing[*]}"
  echo ""
  echo "  Install them, then re-run:"
  echo "    git:        https://git-scm.com/downloads"
  echo "    python3:    https://www.python.org/downloads/"
  echo "    claude:     https://docs.anthropic.com/en/docs/claude-code"
  exit 1
fi

# --- Target directory ---
if [[ "$TARGET" != "." && -e "$TARGET" ]]; then
  red "  '$TARGET' already exists. Choose a different path:"
  echo "    curl -fsSL https://raw.githubusercontent.com/Reef123/OpenVera/main/install.sh | bash -s -- <path>"
  exit 1
fi

# --- Clone + bootstrap ---
# git clone refuses any non-empty destination, and an "effectively empty" cwd
# still holds OS junk (.DS_Store etc.) — the exact case the Finder-made-folder
# flow hits. So for install-in-place we clone into a temp subdir and move the
# contents up; the subfolder path clones normally.
if [[ "$TARGET" == "." ]]; then
  INSTALL_PATH="$(pwd)"
  echo "  Installing OpenVera into: $INSTALL_PATH"
  TMP_CLONE="$(mktemp -d "$(pwd)/.openvera-clone.XXXXXX")"
  git clone --quiet "$REPO_URL" "$TMP_CLONE"
  (
    shopt -s dotglob nullglob
    mv "$TMP_CLONE"/* .
  )
  rmdir "$TMP_CLONE"
else
  INSTALL_PATH="$(pwd)/$TARGET"
  echo "  Installing OpenVera into: $INSTALL_PATH"
  git clone --quiet "$REPO_URL" "$TARGET"
  cd "$TARGET"
fi

echo "  Handing off to bootstrap.sh..."
echo ""
bash bootstrap.sh

green ""
green "  Installed at: $(pwd)"
green ""

# --- Build modes (Fallout terminal style) ---
if [[ -t 1 ]]; then
  G='\033[32m'; R='\033[0m'
  echo ""
  printf '%b\n' "  ${G}╔═══════════════════════════════════════════════╗${R}"
  printf '%b\n' "  ${G}║  Open Vera                                    ║${R}"
  printf '%b\n' "  ${G}╠═══════════════════════════════════════════════╣${R}"
  printf '%b\n' "  ${G}║                                               ║${R}"
  printf '%b\n' "  ${G}║  > VAGUE IDEA                                 ║${R}"
  printf '%b\n' "  ${G}║    /start-vague                               ║${R}"
  printf '%b\n' "  ${G}║    Guided idea-fleshing. Hands you off to     ║${R}"
  printf '%b\n' "  ${G}║    /build new when ready.                     ║${R}"
  printf '%b\n' "  ${G}║                                               ║${R}"
  printf '%b\n' "  ${G}║  > READY TO SHIP                              ║${R}"
  printf '%b\n' "  ${G}║    /build new <idea>                          ║${R}"
  printf '%b\n' "  ${G}║    Guided. Opinionated options. One stop.     ║${R}"
  printf '%b\n' "  ${G}║    Ship a V0, resumable across sessions.      ║${R}"
  printf '%b\n' "  ${G}║                                               ║${R}"
  printf '%b\n' "  ${G}╚═══════════════════════════════════════════════╝${R}"
  echo ""
fi

# Offer to launch straight into OpenVera. curl|bash users aren't in the folder
# yet, so opening it for them removes the most-missed step. Needs a real
# terminal (test by opening /dev/tty, not [[ -r ]]) and the claude CLI.
if [[ "$TARGET" == "." ]]; then NEXT="claude"; else NEXT="cd $TARGET && claude"; fi

if ( : < /dev/tty ) 2>/dev/null && command -v claude >/dev/null 2>&1; then
  printf "  Open OpenVera now? [Y/n] " > /dev/tty
  read -r REPLY < /dev/tty || REPLY=""
  case "${REPLY:-y}" in
    [nN]*) echo "  When you're ready:  $NEXT   (then run /start-vague)" ;;
    *)     echo "  Launching Claude Code..."; exec claude < /dev/tty ;;
  esac
else
  echo "  Next:  $NEXT   (then run /start-vague)"
fi
