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
     vera-system/ROADMAP.md.template \
     vera-system/cockpit.md.template \
     vera-system/inbox.md.template; do
     [ ! -f "${tmpl%.template}" ] && cp "$tmpl" "${tmpl%.template}"
   done
   ```
2. **No Python packages to install.** OpenVera runs on the Python standard library alone (no `requests`, no pip step, nothing in `vera-system/requirements.txt`). Just confirm a working Python 3.8+ is available, the same way `bootstrap.sh` does: existence is not enough, since a broken install (e.g. a Homebrew python whose stdlib C-extensions fail to load) can be present yet unusable.
   ```bash
   PY=""
   for cand in python3 python py /usr/bin/python3 /usr/local/bin/python3; do
     command -v "$cand" >/dev/null 2>&1 || continue
     "$cand" -c 'import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)' 2>/dev/null || continue
     "$cand" -c 'import json, ssl, urllib.request' 2>/dev/null || continue
     PY="$cand"; break
   done
   [ -n "$PY" ] && echo "Python OK: $PY" || echo "No working Python 3.8+ found"
   ```
   If nothing prints "Python OK", the user needs a working Python 3.8+ (install from python.org; on macOS the system `/usr/bin/python3` works) before `/scout`, `/research`, or scored builds will run. The rest of setup can still proceed.
3. **Replace `{{USER_NAME}}`** in `vera-system/relationships/user.md` with their name
4. **Replace `YYYY-MM-DD`** in `vera-system/state.md` and `vera-system/cockpit.md` with today's date
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
8. **Ask about the user memory file** (working-style notes only, never personal facts):
   > "Want me to keep a small `relationships/user.md` file that learns how to work with you — bullet points vs prose, that kind of thing? Never health, family, employer, finances, or location. You can read or edit it anytime, and toggle it off later by editing `vera-system/config.json` and setting `"user_memory": false` (or `true` to turn it back on)."

   Write their answer explicitly into `vera-system/config.json` (add or set the `user_memory` key to `true`/`false`) — don't leave it unset, since an unset key is read as "on" for legacy installs and that ambiguity should never apply to a fresh setup that just asked.

9. **Tell them about API keys** (optional, don't push):
   > "You're set up. Everything works without keys: /build just ships unscored and /scout's Reddit angle falls back to lower-fidelity snippets. If you want the scoring gate or multi-model research later, copy `vera-system/.secrets.template` to `vera-system/.secrets` and add your OpenRouter key."

10. **Welcome message:**
   > "Vera is ready. Try `/start-vague`. It'll help you figure out what to build and show you around. Or if you already know what you want: `/build new <your idea>`."

---

## After This Runs

The `.claude/bootstrapped` marker file exists. CLAUDE.md skips step 4. This file is never loaded again.
