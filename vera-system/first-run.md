# First Run: Manual Fallback (if you skipped `bootstrap.sh`)

The recommended setup path is to run `./bootstrap.sh` from the repo root once after cloning. It does the same steps below, plus key validation and a health check.

This file is the in-session fallback: if you cloned and went straight to `claude` without running the script, the boot sequence loads this and walks Claude through setup. After setup completes, `.claude/bootstrapped` exists and this file is never loaded again.

---

## What to Do

Welcome the user, then set up their harness:

> "Welcome to Vera! Let me set things up real quick."

Ask their name (plain text, not AskUserQuestion; keep it casual):

> "What's your name?"

Then:

1. **Copy templates → working files** (only if missing; don't overwrite personalizations):
   ```bash
   for tmpl in \
     vera-system/relationships/user.md.template \
     vera-system/state.md.template \
     vera-system/memory/MEMORY.md.template \
     vera-system/memory/lessons.md.template \
     vera-system/ideas.md.template \
     vera-system/ROADMAP.md.template; do
     [ ! -f "${tmpl%.template}" ] && cp "$tmpl" "${tmpl%.template}"
   done
   ```
2. **Install Python dependencies.** `/scout`, `/research`, YouTube analysis, and OpenRouter key verification all import `requests` (from `vera-system/requirements.txt`). `bootstrap.sh` does this step; the manual path must too, or those skills fail later with `ModuleNotFoundError`.
   ```bash
   PIP_BIN="$(command -v pip3 || command -v pip || true)"
   if [[ -z "$PIP_BIN" ]]; then
     echo "pip not found — install Python 3 + pip (macOS: brew install python3), then rerun this step"
   else
     PIP_VERSION=$("$PIP_BIN" --version 2>/dev/null | awk '{print $2}' | cut -d. -f1)
     if [[ "$PIP_VERSION" =~ ^[0-9]+$ && "$PIP_VERSION" -ge 23 ]]; then
       "$PIP_BIN" install --user --break-system-packages -q -r vera-system/requirements.txt
     else
       "$PIP_BIN" install --user -q -r vera-system/requirements.txt
     fi
     python3 -c "import requests" && echo "deps OK"
   fi
   ```
   If `pip` is missing or the import still fails, tell the user their Python environment needs attention (install Python 3 + pip, or on macOS `brew install python3`) before `/scout`, `/research`, or scored builds will work. The rest of setup can still proceed.
3. **Replace `{{USER_NAME}}`** in `vera-system/relationships/user.md` with their name
4. **Replace `YYYY-MM-DD`** in `vera-system/state.md` with today's date
5. **Create output directories** if missing:
   ```bash
   mkdir -p vera-projects/projects vera-projects/research-output
   ```
6. **Write curate timestamp:**
   ```bash
   mkdir -p .claude && echo "YYYY-MM-DD" > .claude/last-curate-date  # use today's actual date
   ```
7. **Write the bootstrap marker:**
   ```bash
   echo "bootstrapped" > .claude/bootstrapped
   ```
8. **Tell them about API keys** (optional, don't push):
   > "You're set up. Everything works without keys: /build just ships unscored and /scout's Reddit angle falls back to lower-fidelity snippets. If you want the scoring gate or multi-model research later, copy `vera-system/.secrets.template` to `vera-system/.secrets` and add your OpenRouter key."

9. **Welcome message:**
   > "Vera is ready. Try `/start-vague`. It'll help you figure out what to build and show you around. Or if you already know what you want: `/build new <your idea>`."

---

## After This Runs

The `.claude/bootstrapped` marker file exists. CLAUDE.md skips step 4. This file is never loaded again.
