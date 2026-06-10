---
name: curate
description: "Memory consolidation — prune stale, merge duplicates, flag drift. Progressive: light mode for young harnesses, full mode at 10+ memory files. Auto-writes with git safety."
---

# Curate — Memory Consolidation

Review memory files, clean what's stale or duplicated, report what changed.

**Boot hook warns you when > 7 days since last curate.** Run manually with `/curate`.

---

## Safety Rules

0. **Acquire the curate lock FIRST:** `touch .claude/.curate-running`. While it exists (and is under 60 min old), the PostToolUse mark-dirty hook skips — so curate's own writes don't re-arm the doc-sync gates for work curate commits itself. Remove it at the very end (after the timestamp write): `rm -f .claude/.curate-running`.
1. **Git commit BEFORE making changes.** `pre-curate: save current state`. If clean, skip.
2. **Git commit AFTER changes.** `curate: [one-line summary]`.
3. **Never modify curated pattern files.** `patterns.md` is hand-curated. Flag issues in report only. (`lessons.md` and `memory/promotions.tsv` are the machine lane — curate MAY prune lessons.md and the promotions scripts write the ledger, see the Lessons Scan.)
4. **Never delete history.** Conversation files are archival.
5. **Conservative by default.** When in doubt, keep the entry and flag for human review.
6. **Stamp every doc you touch.** After any write, run `python3 vera-system/scripts/stamp.py <file> /curate`. Applies to state.md, MEMORY.md, user.md.

---

## Progressive Depth

Pick the mode with the helper — it counts both memory stores (auto-memory under `~/.claude/projects/` + harness `vera-system/memory/`) and resolves the auto-memory path for you:

```bash
python3 vera-system/scripts/curate-mode.py mode
```

It prints `MODE=LIGHT` (< 10 files → quick cleanup, ~1 min) or `MODE=FULL` (10+ files → deep consolidation, ~5 min), plus the resolved auto-memory dir and per-store counts.

---

## Light Mode

### 1. Doctor

Run `python3 vera-system/scripts/doctor.py`. Note errors and warnings.

### 2. Quick Staleness Check

For each auto-memory file:
- Do referenced file paths still exist?
- Are referenced tools/projects still active?
- If majority of references are dead → delete the file

For MEMORY.md entries:
- Do linked files still exist? Remove dead pointers.

### 3. Update MEMORY.md Index

- Remove lines pointing to deleted files
- Run `python3 vera-system/scripts/curate-mode.py sizes` — if MEMORY.md prints OVER, trim until it passes. **Do not commit a curate that leaves MEMORY.md over its cap** — entries past the cap are silently truncated at load time, which is invisible context loss.

### 4. Git Commit + Timestamp

```
curate: light — pruned [N] stale entries
```

Write current date to `.claude/last-curate-date`.

### 5. Report

Output to console and update `vera-system/state.md`:

```
Curate — YYYY-MM-DD [LIGHT]

CHANGES
  Deleted: [count] — [filenames]

HARNESS HEALTH
  [doctor summary]

HEALTH: [GREEN/AMBER/RED]
```

### 6. Run Bridge Skills (optional)

If bridge skills exist, invoke them. Skip silently if none.

---

## Full Mode

### 1. Doctor

Run `python3 vera-system/scripts/doctor.py`. Note errors and warnings.

### 2. Staleness Scan

For each auto-memory file (NOT curated files):
- Read content
- Check references: do file paths still exist? Tools still in use? Projects still active?
- Mark stale if majority of references are invalid

For MEMORY.md entries:
- Check for entries referencing completed/abandoned work

### 3. Duplicate Detection

Look for overlapping concepts:
- Same topic in both auto-memory and harness memory
- Multiple MEMORY.md entries covering the same subject
- Entries superseded by newer ones

### 4. Contradiction Check

Scan for conflicts:
- Different recommendations for same use case
- Outdated info alongside current
- Reversed decisions where old entry wasn't removed
- **Boundary conflicts:** CLAUDE.md rules vs skill instructions vs patterns.md. If a skill says "do X" but a pattern says "don't do X", flag it. Check agent `.md` files against CLAUDE.md Critical Rules for contradictions.
- **Stale skill references:** Skills listed in `.claude/skills/README.md` or CLAUDE.md that no longer exist in `.claude/skills/`. Skill names that changed but old references remain.

### 5. Capability Scan (optional)

If a `claude-code-guide` agent is configured, spawn it to flag shipped Claude Code features that obsolete documented harness workarounds. Pass it `vera-system/memory/patterns.md` + `.claude/skills/README.md` as the workaround corpus. Require both the release-note line AND the matching workaround line quoted verbatim — reject matches that lack either. Fold supported matches into FLAGGED FOR REVIEW; never auto-edit. If the agent isn't configured, skip silently.

### 6. Build Retro Scan

Check `{paths.projects_dir}/*/retro.md` for patterns across builds:
- Are scope fit scores trending? (always "close but missed" = kickoff needs work)
- Are process scores trending? (always "too slow" = reduce ceremony)
- Same course corrections repeating? → promote to patterns.md
- After 3+ retros, write a one-line pattern summary to MEMORY.md

### 6.5. V0-Graduation Scan

Detect projects that have moved past V0 in real use but whose `status` field hasn't caught up.

Run the scan — it walks `{paths.projects_dir}/*/CLAUDE.md` and, for each `status: shipped` project, computes commit count over the last 30 days plus `build-state.md` staleness:

```bash
python3 vera-system/scripts/curate-mode.py graduation
```

It prints one line per `live`-candidate: projects with `commits ≥ 3` AND `build-state.md ≥ 30 days` stale, the signal that real use is happening outside the build pipeline (without `/build full` running). Fold each printed line into FLAGGED FOR REVIEW as-is.

Do NOT auto-edit `status`. The user decides per project.

### 6.6. Lessons Promotion Scan

Read `vera-system/memory/lessons.md` (machine-appended by /build failures and doc-sync course corrections). Run the sub-steps IN THIS ORDER. The order is load-bearing: sub-step (d) deletes the lines that (a) and (b) need as evidence. Never run (d) first.

**(a) Check past promotions.** Run:

```bash
python3 vera-system/scripts/curate-mode.py promotions check
```

Fold every RECURRED and FAILED line into FLAGGED FOR REVIEW as: "Promotion FAILED: '<match>' recurred <n> times since <date>. The pattern text is not preventing recurrence; candidate for mechanical enforcement (hook, doctor check, or script gate)." CLEAN and VALIDATED lines need no action. NO_PROMOTIONS means nothing has been promoted yet; continue.

**(b) Record new promotions.** For each lesson group this skill previously flagged for promotion, check whether patterns.md now covers it (the human promoted it since last run). For each one it does, run:

```bash
python3 vera-system/scripts/curate-mode.py promotions record --match "<keyword>" --pattern "<patterns.md heading>"
```

Pick the keyword with judgment: a short literal phrase (2 to 4 words) that appears verbatim in each line of the recurring group and is unlikely to appear in unrelated lessons. Avoid generic single words like "build" or "error". The script does deterministic case-insensitive substring matching from here on. If record exits nonzero, do NOT prune that group in sub-step (d); leave the lines as evidence for next run and note the failure in the report.

**(c) Flag new recurrences.** 3+ lines describing the same lesson: add to FLAGGED FOR REVIEW: "Recurring lesson: [summary], appeared [N] times. Promote to patterns.md?" Never auto-edit patterns.md (Safety Rule 3).

**(d) Prune, evidence-aware.** Delete lines already promoted to patterns.md ONLY if dated on or before their promotion date in promotions.tsv, and one-off lines older than ~10 sessions that never recurred. NEVER delete a line that matches a promotion keyword and is dated after the promotion date: those lines are active recurrence evidence that `promotions check` reads next run, and deleting them silently converts a FAILED promotion into a fake VALIDATED one. lessons.md is a capture lane, not an archive; keep it under its line cap.

### 7. Skill-from-Experience

Read the last 5 conversation logs. Look for multi-step patterns that appeared 3+ times:
- Same sequence of tool calls across sessions
- Same workaround applied repeatedly
- Same type of research/build/fix pattern

If found, note in report under FLAGGED FOR REVIEW: "Pattern: [description] — appeared in sessions [N, N, N]. Worth extracting as a skill?"

Don't auto-create skills. Flag for the user.

### 8. User Profile

Two passes on `relationships/user.md`:

**Pass A — Pattern detection inside user.md.** Read the `What I've Learned` section. Look for clusters of 3+ entries pointing at the same theme (tone preference, decision style, value, recurring constraint). For each cluster:
- Promote a one-line summary into the right section (`How We Work` / `What They Value` / `Context`)
- Delete the source entries it now covers
- If a single entry has been confirmed across 3+ separate sessions and isn't covered upstairs, promote it too

**Pass B — Delta from conversation logs.** Read the last 3 conversation logs. Surface signals not yet captured anywhere in user.md:
- Preferences revealed (e.g., always picks Sonnet for light tasks)
- Corrections that imply a working style
- Anything in the profile contradicted by recent behavior

Append dated one-liners to `What I've Learned`. Don't promote one-shot signals — Pass A handles promotion once 3 instances exist.

**Conservative bar:** "User prefers X" from one session isn't a pattern. Three independent confirmations is.

user.md is gitignored — safe for personal observations.

### 9. Consolidate

**Stale:** Delete if entirely stale, update if partially stale.
**Duplicates:** Keep the more detailed/recent version, merge if both add value.
**Contradictions:** Keep most recent/accurate, remove the contradicted entry.

### 10. Update MEMORY.md Index

- Remove lines pointing to deleted files
- Update descriptions for modified files
- Reorder by relevance
- Run `python3 vera-system/scripts/curate-mode.py sizes` — if MEMORY.md prints OVER, trim until it passes. **Do not commit a curate that leaves MEMORY.md over its cap** (silent truncation at load time). Other OVER files go in FLAGGED FOR REVIEW.

### 11. Git Commit + Timestamp

```
curate: pruned [N] stale, merged [N] dupes, flagged [N] for review
```

Write current date to `.claude/last-curate-date`.

### 12. Report

Run `python3 vera-system/scripts/loop-report.py` and paste its output under the LOOP heading. It appends a trend row to `vera-system/runs/loop-report.tsv` on its own.

Output to console and update `vera-system/state.md`:

```
Curate — YYYY-MM-DD [FULL]

CHANGES
  Deleted: [count] — [filenames]
  Updated: [count] — [filenames]
  Merged: [count] — [what into what]

FLAGGED FOR REVIEW
  - [items curate won't auto-fix]
  - [capability scan matches — feature X obsoletes workaround Y, both quoted]
  - [recurring patterns worth extracting as skills]
  - [user profile updates suggested]

LOOP
  [loop-report.py output: headline plus sections]

HARNESS HEALTH
  [doctor summary]

HEALTH: [GREEN/AMBER/RED]
```

### 13. Run Bridge Skills (optional)

If bridge skills exist, invoke them. Skip silently if none.

---

## What NOT to Do

- Don't create new memory files (only consolidate existing)
- Don't add comments like "removed by curate" — just remove cleanly
- Don't auto-create skills or auto-edit skills/patterns — flag for human review only

---

*Author: Shareef Ellis · [@shareefatwork](https://x.com/shareefatwork)*
