---
name: doc-sync
description: "Session documentation sync — update state, log conversation, check alignment, surface missed TODOs. Run at session end or before context compression. If it's not in a file, it doesn't exist after reboot."
allowed-tools: Bash(python3 vera-system/scripts/*) Bash(git *) Bash(touch .claude/.doc-sync-running) Bash(rm -f .claude/session-dirty .claude/.doc-sync-running .claude/.session-ending) Bash(echo * > .claude/last-doc-sync)
---

# Doc-Sync

Update docs based on session changes. Delta-based — only touch what changed.

---

## Runtime marker contract (read first)

This skill participates in the PreCompact and Stop safety gates. Four markers in `.claude/`:

| Marker | Set by | Cleared on success | Cleared on crash/staleness |
|---|---|---|---|
| `session-dirty` | `mark-dirty.py` (PostToolUse, harness writes) | doc-sync Step 11 | Never auto-cleared — unsynced edits stay flagged across reboots |
| `.doc-sync-running` | doc-sync Step 0 | doc-sync Step 11 | `mark-dirty.py` ignores + removes when older than 60 min; `session-start.py` removes at boot |
| `.session-ending` | `session-end-reminder.py` (UserPromptSubmit end-pattern) | Stop gate when it blocks (one-nag rule), or doc-sync Step 11 | `session-start.py` removes at boot |
| `.curate-running` | /curate at start | /curate at end | Same 60-min TTL + boot cleanup as `.doc-sync-running` |

While a fresh lockfile (`.doc-sync-running` / `.curate-running`) is present, `mark-dirty.py` skips so the skill's own writes don't re-dirty the marker it's about to clear. The Stop gate (`stop-doc-sync-gate.py`) blocks the turn end when `.session-ending` AND `session-dirty` are both present — that's what makes running this skill enforced rather than suggested.

The lockfile MUST be touched BEFORE the first Write/Edit in this skill (Step 0 below) and removed only at Step 11. Solo-user assumption: one Claude Code session per repo at a time.

---

## Step 0: Detect What Changed

Acquire the doc-sync lock first — every subsequent Write/Edit in this skill relies on it:

```bash
touch .claude/.doc-sync-running
```

Then detect changes:

```bash
python3 vera-system/scripts/doc-sync-cascade.py
```

Returns JSON: changed files and which docs need cascade updates. Use this output to drive Step 7.

## Step 1: Check for Gap

```bash
python3 vera-system/scripts/doc-sync-gap.py vera-system/conversations/
```

- `NO_GAP` → normal session, continue
- `SHORT_GAP` / `MEDIUM_GAP` → read state.md NEXT, verify it still makes sense
- `LONG_GAP` → read state.md + ROADMAP.md Sprint + last 2 conversation logs. Fix drift before proceeding.

Output includes the next session number.

---

## Always Update

### 2. state.md

- Bump "Done This Session" → "Done Previous Session"
- Write new session's work
- Update STATUS, SPRINT, NEXT

**Block contract — keep each session's write lean.** A session's "Done" entry is: 1-3 sentences of what shipped (facts + artifact paths) · **NEXT (you)** · **NEXT (Vera)** · blockers, if any · a pointer to the conversation log (`conversations/NNN-YYYY-MM-DD.md`), never a paste of it. If a line is describing something at length, that's the conversation log's job — link it instead of duplicating it.

- **Target:** whole file ~100 lines (mechanical cap: `vera-system/state.md` in `vera_config.py`'s `SIZE_THRESHOLDS`, checked by both `doctor.py` and `curate-mode.py sizes`). It's a boot-tier file read every session — size is a tax on every boot.
- **Trim-to-archive rule.** When "Done Previous Session" content is about to be overwritten (this step, after bumping), don't just drop it — append the outgoing block verbatim to `vera-system/conversations/ARCHIVE-state.md` (create it, with a one-line header, if it doesn't exist yet) before it's gone from state.md. Never delete a block that has no backup; the archive append IS the backup.
- **Organic migration for existing installs.** No migration script, no breaking change. If state.md is already over cap, `doctor.py` / `curate-mode.py sizes` will flag it (`OVER` line, per Step 9 below) on the next doc-sync — that run trims it down using this same block contract and archive rule, one session at a time.

### 2b. cockpit.md (the boot cockpit)

Regenerate `vera-system/cockpit.md` — the derived at-a-glance view the boot sequence's Step 0 renders as the session opener. The user acts on what Vera shows, not files they'd have to go read separately.

- **Derived, never truth.** Rebuild it from what you just synced (state.md, ROADMAP.md Sprint, any project build-states touched). On disagreement, the files win — fix the cockpit, not the other way round.
- **Momentum:** roll "last 5 done" — this session's shipped increments go on top (one line, project-tagged, dated), trim to 5, oldest rows fall off.
- **Next:** ONE action per active thread + Owner (You / Vera / You → Vera). No honest next action for a thread → flag it, don't invent one.
- **Top projects:** ≤5 rows, Stage + Pulse (🟢 moved <7 days / 🟡 blocked-on-you / 🔴 stale 14+ days and not parked).
- **Blocked on you:** ≤3 items, same three classes as the Needs You report below, each verified against primary evidence — never repeat a stale number from an old file. If more than 3 exist, add "+N waiting" so the overflow is a visible count, never an invisible queue. **Rotation:** track a surfacing count per item (e.g. "· 3rd surfacing"); any item surfaced 3 times unacted forces a park-or-kill decision at the next session's start — give it a wake condition or call it dead. No permanent riders.
- **Honest empty state.** On a fresh install (or any section with nothing to show), the cockpit says so plainly — "nothing yet" rows explaining what will appear once there's something to report. Never fabricate a row to make the cockpit look populated; a fake "done" or fake "next" is worse than an empty table.
- Bump the **Updated:** stamp (date + session, if session numbers are in use).
- Stamp the file (see Step 9) and include it in the boot-tier size check — it shares `vera_config.py`'s `SIZE_THRESHOLDS` table with state.md/ROADMAP.md, capped at 60 lines.

### 3. Conversation Log

**Logs stay high-level, always.** Decisions, what shipped, corrections and their fix — never personal disclosures, never a blow-by-blow of what was said. If something personal came up in the session, the log records at most the work implication ("prefers short blocks" — never the reason). This applies whether or not user-memory is enabled; it's a log-quality rule, not a memory-feature rule.

For every Course Corrections row marked "Yes", append a one-line dated lesson to `vera-system/memory/lessons.md` (shape: `- YYYY-MM-DD [context] lesson`). That file is the machine-appendable capture lane; /curate promotes lessons that recur 3+ times to patterns.md with human review. Without this write, corrections evaporate at reboot.

**Curate-flag lane (user-memory feeder — only if `python3 vera-system/scripts/vera_config.py user_memory` prints `true`; an absent config key means enabled and that command is the only check that handles it).** If a candidate working-style observation surfaced this session (a stated preference, an inferred pattern, a correction that implies how to work with the user) — and only if it fits the shape rule (assistant-behavior, not user-attribute) and clears the NEVER list (no health/family/employer/finances/location) — add ONE line at the bottom of the conversation log:

```
Curate-flag: <Told|Observed> — <one-line, shape-rule-compliant observation>
```

This is the only handoff lane into `/curate`'s User Profile step (curate/SKILL.md §8) — curate reads `Curate-flag:` lines from the last 3 logs rather than re-mining full conversation prose, which keeps the NEVER-list surface small. Skip this line entirely (don't add an empty one) if nothing candidate-worthy came up, or if user-memory is disabled.

If `patterns.md` gained an entry this session (the user approved a promotion in conversation), record it now so /curate can verify the pattern actually works:

```bash
python3 vera-system/scripts/curate-mode.py promotions record --match "<2-4 word phrase from the recurring lessons>" --pattern "<patterns.md heading>"
```

Skip for pattern entries that did not come from recurring lessons (nothing to verify against). An unrecorded promotion is invisible to validation: the ledger never learns it exists, so it can silently fail.

Create `conversations/NNN-YYYY-MM-DD.md` (session number from Step 1):

```markdown
# Session NNN — YYYY-MM-DD

## Summary
[1-2 sentence summary]

## What Happened
- [Key action 1]

## Course Corrections
| What Went Wrong | What Changed | Generalizable? |
|----------------|-------------|----------------|
| [wrong assumption] | [correction] | Yes → lessons.md / No |

## Files Changed
| File | Action |
|------|--------|
| path/to/file | Created/Updated |

## State at End
[Current state summary]

Curate-flag: [optional — see "Curate-flag lane" above; omit if nothing candidate-worthy came up]
```

Continuing after compact: update existing file with "Continuation" subsection.

### 4. ROADMAP.md

Move completed items to Done. Update Sprint if work shifted. Add new items discovered.

### 5. Project Version Check

Continued sessions (post-compact) often resume project work directly, without `/build continue` — so the version bump that lives inside the build flow never fires. Doc-sync is the net. **The version trigger is the work, not the command.**

If this session shipped a meaningful increment to any project under `{paths.projects_dir}/<slug>/` (new feature, behavior change, public ship — not typo fixes):

1. Bump the version in the project's build-state:
   ```bash
   python3 vera-system/scripts/build-state.py <slug> "<current stage>" --substage "V1.4 shipped — <one-line description>"
   ```
2. App `package.json` (if one exists) — keep `version` in step with build-state.
3. Project changelog, if the project keeps one.

Ask: "If `/build continue` were running, would it have bumped the version here?" If yes, bump it now. Cosmetic-only sessions skip this step.

### 6. Missed TODO Scan

Pipe a summary of this session's work into the scanner:

```bash
echo "<session summary — paste key actions, decisions, and promises>" | python3 vera-system/scripts/doc-sync-todos.py vera-system/state.md
```

The script greps for action patterns ("need to", "blocked on", "I'll create..."), checks referenced files exist, and cross-references against state.md NEXT. Surface anything it finds.

### 7. Cascade Updates

Apply every cascade from Step 0's output. Read the target file, find the section, edit.

### 8. Task Tracker Sync (if configured)

If a task tracker is configured (Todoist, Linear, etc.), sync follow-ups from Step 6. **Check existing tasks before creating** — search for keywords from each TODO. Don't duplicate. Report: "Tasks: closed N, created N, already tracked N."

### 9. Stamp Touched Docs

After every write, stamp the file so its freshness + source are visible:

```bash
python3 vera-system/scripts/stamp.py <file> /doc-sync
```

Apply to every file you wrote in steps 2-7: state.md, cockpit.md, ROADMAP.md, the new conversation log, and any cascade targets. Idempotent — safe to run.

Then check boot-tier file sizes:

```bash
python3 vera-system/scripts/curate-mode.py sizes
```

If any `OVER` line prints, surface it to the user with the remediation (state.md: archive completed items; MEMORY.md/patterns.md: consolidate or promote to secondary files; ROADMAP.md: archive done milestones). MEMORY.md over its cap is urgent — entries past the cap are silently truncated at load time.

### 10. Bridge Skills (optional)

If bridge skills exist in `.claude/skills/`, invoke them. Skip silently if none.

### 11. Clear Runtime Markers (Bash only)

```bash
echo "$(date -u +%FT%T)" > .claude/last-doc-sync
rm -f .claude/session-dirty .claude/.doc-sync-running .claude/.session-ending
```

Use Bash redirection (`>`) and `rm`, NOT Write/Edit, for these two operations. Write/Edit would re-fire PostToolUse and re-dirty the marker after we just cleared it. The lockfile prevents the same re-dirty during Steps 1-10; this step releases it last. `.session-ending` may already be gone (the Stop gate deletes it when it fires) — the `rm -f` is harmless either way.

Order matters: write `last-doc-sync` BEFORE removing the markers, so a crash between commands leaves the system in a recoverable state (timestamp present, marker still set = next session knows to retry).

### 12. Curate Trigger (after markers are clear)

```bash
python3 vera-system/scripts/curate-mode.py age
```

If `AGE_DAYS` is greater than 7 (or -1 with a populated memory dir), spawn curate in the background — do not run it inline and do not block the user:

```
Agent(subagent_type="general-purpose", description="weekly curate",
      prompt="Run /curate per .claude/skills/curate/SKILL.md. Background mode — do not engage the user.",
      run_in_background=true)
```

This runs AFTER Step 11 on purpose: curate makes its own git commits, and spawning it before doc-sync's writes finish would race them. If the session closes before the background curate completes, `last-curate-date` stays old and the boot-time directive catches it next session.

---

## Quick Alignment Check

Do these agree? Fix drift if not:
- ROADMAP.md Sprint — what's primary?
- state.md STATUS — matches sprint?
- state.md NEXT — matches both?

## Expiry & Deadline Scan

Proactively flag time-sensitive items before writing the Needs You report below:

1. Scan ROADMAP.md and any project build-states for dates (key expirations, deadlines, milestones).
2. Check `.secrets` for key rotation dates if any are noted there.
3. Flag anything within 7 days of expiry as "Heads up."
4. Flag already-expired items as urgent.

## Needs You (closing report)

The user acts on what Vera mentions, not on lists they'd have to go review themselves — so every doc-sync ends with a **Needs You** list, max ~3 items, drawn from exactly three classes:

1. **Keys/expiries** due or overdue (from the scan above)
2. **Blocked-on-you** — work stalled on a decision, access, or a manual action only the user can do
3. **Woken parked items** — a wake condition from ROADMAP.md's Backlog/parked notes that fired

Nothing outside these three classes gets proactive mention. **Verify before listing** — check every item against primary evidence (the actual file, a live check, git) rather than repeating a number from old state.md text; a stale claim in the Needs You list is worse than an empty one. If the list is non-empty, also write it into state.md NEXT — the next session's boot reads state.md, so the reminder survives to session start for free. Empty list → say "Needs you: nothing" and move on.

## Summary Tables (final output — always)

After the lock is released (Step 11), close every doc-sync with **two markdown tables** — they scan faster than prose and this is the last thing in the turn, after all files (and any task tracker) are written.

**Table 1 — What we did:**

| Area | What | Status |
|------|------|--------|

One row per meaningful thing shipped this session. `Status` = done / partial / blocked. Keep `What` to one line. Group by project/area, not chronological order.

**Table 2 — What's next:**

| Item | Owner |
|------|-------|

Every actionable next step, including the Needs You items. `Owner` = You (blocked on the user) / Vera (can proceed) / Either. **This table must agree with state.md NEXT** — no next-step lives in prose only; if it's real, it also has a durable home in a file.

**Rules:**
- Tables reflect what's actually in the files (and task tracker, if configured) — don't list a next step you didn't also give a durable home.
- Lead with the "blocked on you" items (they're the Needs You set); everything else follows.
- Voice: plain, one idea per cell, no padding rows to look thorough.
- This is additive to Needs You, not a replacement — Needs You still gets written into state.md NEXT; the tables are the on-screen closing report.

---

## When NOT to Run

Skip if nothing happened — no state change, no files touched, no decisions made.

---

*Author: Shareef Ellis · [@shareefatwork](https://x.com/shareefatwork)*
