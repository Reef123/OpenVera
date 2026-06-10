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
| `session-dirty` | `mark-dirty.py` (PostToolUse, harness writes) | doc-sync Step 10 | Never auto-cleared — unsynced edits stay flagged across reboots |
| `.doc-sync-running` | doc-sync Step 0 | doc-sync Step 10 | `mark-dirty.py` ignores + removes when older than 60 min; `session-start.py` removes at boot |
| `.session-ending` | `session-end-reminder.py` (UserPromptSubmit end-pattern) | Stop gate when it blocks (one-nag rule), or doc-sync Step 10 | `session-start.py` removes at boot |
| `.curate-running` | /curate at start | /curate at end | Same 60-min TTL + boot cleanup as `.doc-sync-running` |

While a fresh lockfile (`.doc-sync-running` / `.curate-running`) is present, `mark-dirty.py` skips so the skill's own writes don't re-dirty the marker it's about to clear. The Stop gate (`stop-doc-sync-gate.py`) blocks the turn end when `.session-ending` AND `session-dirty` are both present — that's what makes running this skill enforced rather than suggested.

The lockfile MUST be touched BEFORE the first Write/Edit in this skill (Step 0 below) and removed only at Step 10. Solo-user assumption: one Claude Code session per repo at a time.

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

Returns JSON: changed files and which docs need cascade updates. Use this output to drive Step 5.

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

### 3. Conversation Log

For every Course Corrections row marked "Yes", append a one-line dated lesson to `vera-system/memory/lessons.md` (shape: `- YYYY-MM-DD [context] lesson`). That file is the machine-appendable capture lane; /curate promotes lessons that recur 3+ times to patterns.md with human review. Without this write, corrections evaporate at reboot.

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
```

Continuing after compact: update existing file with "Continuation" subsection.

### 4. ROADMAP.md

Move completed items to Done. Update Sprint if work shifted. Add new items discovered.

### 5. Missed TODO Scan

Pipe a summary of this session's work into the scanner:

```bash
echo "<session summary — paste key actions, decisions, and promises>" | python3 vera-system/scripts/doc-sync-todos.py vera-system/state.md
```

The script greps for action patterns ("need to", "blocked on", "I'll create..."), checks referenced files exist, and cross-references against state.md NEXT. Surface anything it finds.

### 6. Cascade Updates

Apply every cascade from Step 0's output. Read the target file, find the section, edit.

### 7. Task Tracker Sync (if configured)

If a task tracker is configured (Todoist, Linear, etc.), sync follow-ups from Step 5. **Check existing tasks before creating** — search for keywords from each TODO. Don't duplicate. Report: "Tasks: closed N, created N, already tracked N."

### 8. Stamp Touched Docs

After every write, stamp the file so its freshness + source are visible:

```bash
python3 vera-system/scripts/stamp.py <file> /doc-sync
```

Apply to every file you wrote in steps 2-6: state.md, ROADMAP.md, the new conversation log, and any cascade targets. Idempotent — safe to run.

Then check boot-tier file sizes:

```bash
python3 vera-system/scripts/curate-mode.py sizes
```

If any `OVER` line prints, surface it to the user with the remediation (state.md: archive completed items; MEMORY.md/patterns.md: consolidate or promote to secondary files; ROADMAP.md: archive done milestones). MEMORY.md over its cap is urgent — entries past the cap are silently truncated at load time.

### 9. Bridge Skills (optional)

If bridge skills exist in `.claude/skills/`, invoke them. Skip silently if none.

### 10. Clear Runtime Markers (Bash only)

```bash
echo "$(date -u +%FT%T)" > .claude/last-doc-sync
rm -f .claude/session-dirty .claude/.doc-sync-running .claude/.session-ending
```

Use Bash redirection (`>`) and `rm`, NOT Write/Edit, for these two operations. Write/Edit would re-fire PostToolUse and re-dirty the marker after we just cleared it. The lockfile prevents the same re-dirty during Steps 1-9; this step releases it last. `.session-ending` may already be gone (the Stop gate deletes it when it fires) — the `rm -f` is harmless either way.

Order matters: write `last-doc-sync` BEFORE removing the markers, so a crash between commands leaves the system in a recoverable state (timestamp present, marker still set = next session knows to retry).

### 11. Curate Trigger (after markers are clear)

```bash
python3 vera-system/scripts/curate-mode.py age
```

If `AGE_DAYS` is greater than 7 (or -1 with a populated memory dir), spawn curate in the background — do not run it inline and do not block the user:

```
Agent(subagent_type="general-purpose", description="weekly curate",
      prompt="Run /curate per .claude/skills/curate/SKILL.md. Background mode — do not engage the user.",
      run_in_background=true)
```

This runs AFTER Step 10 on purpose: curate makes its own git commits, and spawning it before doc-sync's writes finish would race them. If the session closes before the background curate completes, `last-curate-date` stays old and the boot-time directive catches it next session.

---

## Quick Alignment Check

Do these agree? Fix drift if not:
- ROADMAP.md Sprint — what's primary?
- state.md STATUS — matches sprint?
- state.md NEXT — matches both?

---

## When NOT to Run

Skip if nothing happened — no state change, no files touched, no decisions made.

---

*Author: Shareef Ellis · [@shareefatwork](https://x.com/shareefatwork)*
