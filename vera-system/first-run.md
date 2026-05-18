# First Run — Manual Fallback (if you skipped `bootstrap.sh`)

The recommended setup path is to run `./bootstrap.sh` from the repo root once after cloning. It does the same steps below, plus key validation and a health check.

This file is the in-session fallback: if you cloned and went straight to `claude` without running the script, the boot sequence loads this and walks Claude through setup. After setup completes, `.claude/bootstrapped` exists and this file is never loaded again.

---

## What to Do

Welcome the user, then set up their harness:

> "Welcome to Vera! Let me set things up real quick."

Ask their name (plain text, not AskUserQuestion — keep it casual):

> "What's your name?"

Then:

1. **Copy templates → working files** (only if missing — don't overwrite personalizations):
   ```bash
   for tmpl in \
     vera-system/relationships/user.md.template \
     vera-system/state.md.template \
     vera-system/memory/MEMORY.md.template \
     vera-system/ideas.md.template \
     vera-system/ROADMAP.md.template; do
     [ ! -f "${tmpl%.template}" ] && cp "$tmpl" "${tmpl%.template}"
   done
   ```
2. **Replace `{{USER_NAME}}`** in `relationships/user.md` with their name
3. **Replace `YYYY-MM-DD`** in `state.md` with today's date
4. **Create output directories** if missing:
   ```bash
   mkdir -p vera-projects/projects vera-projects/research-output
   ```
5. **Write curate timestamp:**
   ```bash
   mkdir -p .claude && echo "YYYY-MM-DD" > .claude/last-curate-date  # use today's actual date
   ```
6. **Write the bootstrap marker:**
   ```bash
   echo "bootstrapped" > .claude/bootstrapped
   ```
7. **Tell them about API keys** (optional, don't push):
   > "You're set up. If you want multi-model research later, copy `vera-system/.secrets.template` to `vera-system/.secrets` and add your OpenRouter key."

8. **Welcome message:**
   > "Vera is ready. Try `/start-here` — it'll help you figure out what to build and show you around. Or if you already know what you want: `/build new <your idea>`."

---

## After This Runs

The `.claude/bootstrapped` marker file exists. CLAUDE.md skips step 4. This file is never loaded again.
