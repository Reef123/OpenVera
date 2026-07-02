---
description: Post-change sweep — after any harness change (new skill, hook, agent, or behavior), check every public surface for drift and fix it. Run before a release commit.
argument-hint: "[optional: a diff range or file list to scope the sweep to]"
---

# Update OpenVera

A harness change is only real once every surface that describes the harness agrees with it. This command is the mechanical check that catches the drift — a new skill that never made it into the index, a README that still says "no user memory," a public doc with a model name leaked into it.

## When to run

- Before any release commit that touches `.claude/`, `vera-system/`, `bootstrap.sh`, or `README.md`.
- After adding a skill, agent, hook, or config flag.
- Any time `git diff --stat` shows harness files changed and you're not sure every doc caught up.

## Steps

1. **Read the diff.** `git status --short` + `git diff --stat` (or the range in `$ARGUMENTS` if given) — this is the ground truth for what changed. Read the full diff for any file that adds a new capability (new skill, new flag, new hook, new agent), not just the stat summary.

2. **Check each public surface for drift against that diff:**
   - `README.md` — does it mention every user-facing capability that shipped? Skills table (`## Skills`), "Why It's Built This Way," "What OpenVera Won't Do," "Keys are Optional," repo structure tree. A new skill with no row, a new default behavior with no line, is drift.
   - `.claude/skills/README.md` — every skill folder under `.claude/skills/` has exactly one row in the Index table (or is explicitly listed as internal-only). No skill dir with zero mentions; no stale row for a skill dir that no longer exists.
   - `vera-system/CLAUDE.md` — boot sequence, tiers, primitives table, folder structure tree all match what's actually on disk (new boot-tier files, new top-level dirs).
   - `bootstrap.sh` / `vera-system/first-run.md` — the template-copy list matches every `*.template` file that actually exists in the repo; any new opt-in prompt (config flag) is asked and written; the "what you get" summary text mentions new default behaviors.
   - `vera-system/memory/patterns.md` (or `CLAUDE.md` under `memory/`) — new cross-cutting behavioral rules from the diff are captured here, not just buried in a skill file.
   - `.claude/agents/` — every agent file matches something that actually spawns it (no orphan agent defs, no spawn site pointing at a non-existent agent).

3. **Fix drift found in step 2.** Small, surgical edits — match each file's existing voice and structure. Don't restructure a file to fit a change; fit the change into the file's existing shape. If a new capability is genuinely internal/mechanical (no user-facing behavior change), it's fine for it to NOT appear in README — use judgment, don't pad.

4. **Run the public-copy audit:**
   - `grep -rn -i "sonnet\|opus\|haiku\|claude-[0-9]" README.md vera-system/` — model IDs live in `.claude/agents/*.md` frontmatter and skill bodies only, never in a public-facing doc. Any hit outside `.claude/` is a violation — replace with generic tier language ("cheap tier" / "capable tier" / "the model").
   - `grep -n "—" README.md` — no em dashes in public copy (LLM tell). Rewrite with a period, comma, or parenthetical.
   - Benefit-first check: skim any new README line for mechanism-first phrasing ("uses a promotions.tsv ledger to...") vs. benefit-first ("nothing gets promoted until it's proven twice..."). Public copy leads with WIIFM, mechanism is a supporting clause at most.

5. **Run tests + doctor:**
   ```bash
   python3 -m unittest discover -s tests
   python3 vera-system/scripts/doctor.py
   ```
   Tests must pass. Doctor exit 0 or 2 (warnings) is fine; exit 1 (error) is not — check `KNOWN_SCRIPTS` in `doctor.py` if a new script under `vera-system/scripts/` gets flagged as unexpected.

6. **Report.** One line per surface checked: clean or fixed-what. If something couldn't be resolved (a genuine judgment call, a missing decision), name it instead of guessing.

## Boundaries

This command edits documentation and public-copy surfaces only. It does not change skill logic, hook behavior, or test files (beyond what step 5 requires to pass). It never commits or pushes — that's a separate, explicit step.
