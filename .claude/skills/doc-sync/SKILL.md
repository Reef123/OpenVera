---
name: doc-sync
description: "Session documentation sync — update state, log conversation, check alignment, surface missed TODOs. Run at session end or before context compression. If it's not in a file, it doesn't exist after reboot."
allowed-tools: Bash(python3 vera-system/scripts/*) Bash(git *)
---

# Doc-Sync

Update docs based on session changes. Delta-based — only touch what changed.

---

## Step 0: Detect What Changed

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
| [wrong assumption] | [correction] | Yes → patterns.md / No |

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

### 9. Bridge Skills (optional)

If bridge skills exist in `.claude/skills/`, invoke them. Skip silently if none.

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
