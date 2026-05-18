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

REPO_URL="https://github.com/Reef123/OpenVera.git"
TARGET="${1:-openvera}"

red()   { printf "\033[31m%s\033[0m\n" "$*"; }
green() { printf "\033[32m%s\033[0m\n" "$*"; }
bold()  { printf "\033[1m%s\033[0m\n"  "$*"; }

bold ""
bold "  OpenVera installer"
bold ""

# --- Prereq checks ---
missing=()
command -v git      >/dev/null 2>&1 || missing+=("git")
command -v python3  >/dev/null 2>&1 || missing+=("python3")
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
if [[ -e "$TARGET" ]]; then
  red "  '$TARGET' already exists. Choose a different path:"
  echo "    curl -fsSL https://raw.githubusercontent.com/Reef123/OpenVera/main/install.sh | bash -s -- <path>"
  exit 1
fi

# --- Clone + bootstrap ---
echo "  Cloning OpenVera into $TARGET..."
git clone --quiet "$REPO_URL" "$TARGET"
cd "$TARGET"

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
  printf '%b\n' "  ${G}║    /start-here                                ║${R}"
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

echo "  Next:  cd $TARGET && claude"
echo "         then run /start-here"
