---
name: curate
description: "Memory consolidation — prune stale, merge duplicates, flag drift. Progressive: light mode for young harnesses, full mode at 10+ memory files. Auto-writes with git safety. Flags land in the memory/curate-flags.md ledger (reconcile-and-age); telemetry row per run via telemetry.py."
---

# Curate — Memory Consolidation

Review memory files, clean what's stale or duplicated, report what changed.

**Boot hook warns you when > 7 days since last curate.** Run manually with `/curate`.

### Optional: schedule weekly runs

You MAY additionally set up a Claude Code `/schedule` routine (cloud-side) to fire `/curate` on a weekly cadence, e.g. `/schedule weekly curate per .claude/skills/curate/SKILL.md`. This is purely additive — it's a second way to *trigger* a run, not a replacement for local tracking. The boot tripwire (stale-lock crash detection) and the `> 7 days` cadence check in `session-start.py` / `vera-system/CLAUDE.md` remain the source of truth for "did curate actually run": a scheduled cloud-side run still has to satisfy the same completion contract (Safety Rule 0 — no lock file, fresh `.claude/last-curate-date`, same-date `curate:` commit) before the next boot will consider it done. If a scheduled run can't reach the repo to commit and stamp the date, don't rely on it silently — the local check will (correctly) still flag it as overdue.

---

## Safety Rules

0. **Acquire the curate lock FIRST — content matters, not a bare touch:**

   ```bash
   echo "RUNNING $(date -u +%Y-%m-%dT%H:%M:%S)" > .claude/.curate-running
   ```

   While it exists (and is under 60 min old), the PostToolUse mark-dirty hook skips — so curate's own writes don't re-arm the doc-sync gates for work curate commits itself. The `RUNNING <ts>` content is the dead-run tripwire: if this run dies mid-way, the lock survives to the next boot, and `session-start.py` reads the timestamp and surfaces "last curate crashed, started <ts>" before removing it. A bare `touch` loses that timestamp — never use it.

   **Completion contract:** a curate run COMPLETED = no lock file AND a fresh `.claude/last-curate-date` AND a same-date `curate:` commit. Any other combination reads as crashed or in-flight. This is why the lock is removed LAST (see the Git Commit + Timestamp step in each mode below) — commit, then date-stamp, then `rm -f .claude/.curate-running`, strictly in that order. Never remove the lock before the commit lands.
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

### 3b. Reconcile the Flag Ledger (if this run produced any flags)

Light mode rarely produces flags (it's a quick prune, not a drift scan), but if a doctor error or dead pointer is worth a human decision, it goes in `vera-system/memory/curate-flags.md` — same reconcile-and-age rules as Full Mode's ledger step below. Most Light runs touch nothing here; skip silently if there's nothing to add.

### 4. Git Commit + Timestamp — order is the contract

Strictly in this order (completion contract, Safety Rule 0):

```
curate: light — pruned [N] stale entries
```

1. Commit the change above.
2. Write current date to `.claude/last-curate-date`.
3. Log the run: `python3 vera-system/scripts/telemetry.py curate PASS --note "light — [N] stale pruned"` (use `SOFT_FAIL`/`HARD_FAIL` if doctor found errors this run — soft-fail, never blocks the run).
4. Remove the lock LAST: `rm -f .claude/.curate-running`.

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

### 6.7. Project Registry Sweep (census — tiered walk)

Curate is the ONE place a full project census runs — doc-sync stays delta-only every other session (see `doc-sync/SKILL.md` §2b). Weekly is cheap enough for a full walk; every session is not.

```bash
python3 vera-system/scripts/project-index.py --format json
```

Each row carries `tier: "hot"` or `"cold"` (project-index.py's own tiered-walk gate — see its header comment). Handle the two tiers differently, on purpose:

- **Hot** (`status: building/exploring/live`, or a missing/unrecognized status): the real check. Confirm frontmatter parses (name/slug/status present) and that ROADMAP.md / `vera-system/cockpit.md`'s Top-projects row for this slug matches what the index reports (status, not stale by more than this run). Mismatch → drift.
- **Cold** (`status: parked/shipped/declined/deprecated`): the script already did the only check that's allowed — CLAUDE.md exists and its frontmatter parses. Do nothing further with the folder itself.
- **Parked folders are NEVER opened, full stop** — not by this step, not by any other. A parked project's wake condition lives in the ROADMAP.md parked table, not in the project folder. This step's parked-side check is a **table cross-check only**: every `status: parked` slug from the index should appear in ROADMAP's parked table (with a wake condition), and vice versa. A parked slug missing from the table (no wake condition recorded anywhere) → drift row — that project can never wake on its own.

**Backfill.** A `{projects_dir}/<slug>/` directory with no `CLAUDE.md` (index row derived name/slug from the dirname alone, `has_*` fields all null with no status): look for `spec.md` or `idea.md` in that folder for a name/summary to seed from, then:

```bash
python3 vera-system/scripts/frontmatter.py create --slug <slug> --name "<derived name>" \
  --status exploring --origin "/curate backfill" --summary "<one line from spec/idea, or the dirname if nothing better>"
```

If neither `spec.md` nor `idea.md` exists and the dirname alone isn't a reasonable name (e.g. build cruft, a stray dir) — do NOT guess a backfill. Add a drift row to `curate-flags.md` instead (`Consequence`: "project untracked — invisible to registry/cockpit/dashboard until backfilled or removed"). Never silently omit an un-backfillable project from the report.

**Drift → the ledger.** Every mismatch this step finds (hot drift, parked-table cross-check miss, un-backfillable project) becomes a row in `curate-flags.md`, same reconcile-and-age mechanics as step 10.5 below — don't write a separate ledger, feed these into the same reconcile pass. Fill `Consequence` honestly: real drift costs something concrete (e.g. "cockpit shows wrong project state" or "project can never wake — no table entry"); genuinely cosmetic drift (e.g. a stale `updated:` date on an otherwise-correct row) gets `Consequence: none — cosmetic` and never escalates, per the consequence-gate.

### 7. Skill-from-Experience

Read the last 5 conversation logs. Look for multi-step patterns that appeared 3+ times:
- Same sequence of tool calls across sessions
- Same workaround applied repeatedly
- Same type of research/build/fix pattern

If found, note in report under FLAGGED FOR REVIEW: "Pattern: [description] — appeared in sessions [N, N, N]. Worth extracting as a skill?"

Don't auto-create skills. Flag for the user.

### 8. User Profile

Check the opt-in first — run `python3 vera-system/scripts/vera_config.py user_memory`; it prints `true` or `false` (an absent config key means enabled — legacy installs are grandfathered on, and this command is the only check that handles that; never infer the flag from the full config dump). If `false`, skip this entire section silently: no reads, no writes, no report line.

**Shape rule + NEVER list apply to every write in this section, no exceptions.** Every entry's subject is the ASSISTANT's behavior, never the user — "User is/has X" is a forbidden shape; rewrite as an instruction or drop it. Never write anything traceable to health/diagnoses, family, employer, finances, or location, even as an aside — implications may be stored, the category itself may not. Enforce the hard caps in the template header (≤5 sentences per section, "What I Don't Know Yet" ≤2 sentences) — over cap means tighten existing entries or evict the weakest one, not add without pruning.

**Promotion gates — two lanes, reusing the v1.16.1 promotions machinery (curate-mode.py, `memory/promotions.tsv`) as the second lane. No new organs.**

- **Told** (the user explicitly states a preference, in-session): promote to the right section (`How We Work` / `What They Value` / `Context`) same-session, marked provisional. Record it: `python3 vera-system/scripts/curate-mode.py promotions record --match "<2-4 word phrase>" --pattern "user.md:<section>"`.
- **Observed** (inferred from behavior, not stated): requires 2 recurrences **across different sessions** before promotion — down from the old 3-session bar. Check `What I've Learned` for a same-theme entry from an earlier session; on the 2nd recurrence, promote and record via the same `curate-mode.py promotions record` call.
- **Provisional → validated:** handled automatically by the existing no-contradiction window — run `python3 vera-system/scripts/curate-mode.py promotions check` (same call already used for lessons.md promotions) and read its output for any `user.md:` pattern_ref rows.

**Removal is asymmetric — instant, no gate.** "Stop doing X" is a fact, not an inference: the moment it's said, delete the entry it contradicts immediately. No recurrence requirement, no waiting on promotions check, no relitigating in a future session.

**Pass A — Pattern detection inside user.md.** Read `What I've Learned`. Apply the Observed gate (2 recurrences, different sessions) to cluster candidates; promote per the rules above and delete the source entries the promotion now covers.

**Pass B — Delta from conversation logs.** Read the last 3 conversation logs for candidate signals — but only via each log's `Curate-flag:` line (doc-sync's handoff lane; see `doc-sync/SKILL.md`). Don't re-mine full conversation prose for personal signal — that's exactly the surface the NEVER list exists to keep curate off. Told signals in a `Curate-flag:` line promote same-session; Observed signals get appended as a dated one-liner to `What I've Learned` (shape-rule-compliant) and wait for the 2nd recurrence.

**Report every add/remove — nothing lands silently.** Add one line per change to the curate report's CHANGES section, e.g. "added 1 working-style note (Observed, 2nd recurrence)" or "removed 1 entry (Told: stop doing X)".

user.md is gitignored — safe for personal observations, subject to the NEVER list above regardless.

### 9. Consolidate

**Stale:** Delete if entirely stale, update if partially stale.
**Duplicates:** Keep the more detailed/recent version, merge if both add value.
**Contradictions:** Keep most recent/accurate, remove the contradicted entry.

### 10. Update MEMORY.md Index

- Remove lines pointing to deleted files
- Update descriptions for modified files
- Reorder by relevance
- Run `python3 vera-system/scripts/curate-mode.py sizes` — if MEMORY.md prints OVER, trim until it passes. **Do not commit a curate that leaves MEMORY.md over its cap** (silent truncation at load time). Other OVER files go in FLAGGED FOR REVIEW.

### 10.5. Reconcile the Flag Ledger

Every flag surfaced this run (staleness, duplicates, contradictions, retro/graduation drift, parked-rot, leaked commitments, etc.) lands in `vera-system/memory/curate-flags.md` — the durable home. The FLAGGED FOR REVIEW section of the console/state.md report still prints in full (human-readable summary for this run), but the ledger is what survives to the next run.

1. Read the ledger. For every flag this run produced, match against existing rows first — **reconcile, never re-derive from scratch.** Same underlying issue, even reworded, is the same row: increment `Runs survived`, update Notes if the situation changed.
2. Genuinely new flags → new row, `Runs survived: 1`. Fill `Consequence` honestly — what it costs the user if left unaddressed. If there's no real consequence (cosmetic/tidiness only), say so explicitly (`Consequence: none — cosmetic`); do NOT leave the cell blank to dodge the question, and do NOT invent a consequence to make a flag look important.
3. Flags verified fixed → `Status: resolved: <one-line proof>`. A resolved row stays one more run for visibility, then delete it (row number retires, never reused).
4. Recurring HALTs (a safety check that fired identically before) → ONE named escalating row (`HALT recurred Nx: <reason>`), never a fresh unlinked flag per run.
5. Any row reaching `Runs survived ≥ 3` with a non-empty `Consequence` claims a boot slot as a park-or-kill ask (boot reads the ledger — see `vera-system/CLAUDE.md`). A row at age ≥3 with no real consequence stays visible in the ledger but does NOT interrupt boot — note both cases in the report.
6. Run `python3 vera-system/scripts/ledger-lint.py vera-system/memory/curate-flags.md` after editing. Fix any lint error before committing (an escalating row with an empty `Consequence` is the most likely one).

### 11. Git Commit + Timestamp — order is the contract

Strictly in this order (completion contract, Safety Rule 0):

```
curate: pruned [N] stale, merged [N] dupes, flagged [N] for review
```

1. Commit the change above.
2. Write current date to `.claude/last-curate-date`.
3. Log the run: `python3 vera-system/scripts/telemetry.py curate PASS --note "full — [N] stale, [N] merged, [N] flags open"` (use `SOFT_FAIL` if doctor found warnings, `HARD_FAIL` if a safety rule halted the run). This is the run-happened row telemetry.py already supports — no new tsv, no schema change. Flag counts themselves are NOT telemetry fields; the doc-sync cockpit computes them by counting `curate-flags.md` rows at read time.
4. Remove the lock LAST: `rm -f .claude/.curate-running`. If the run dies at any earlier point, the leftover lock is what tells the next boot the truth.

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

- Don't create new memory files (only consolidate existing) — exception: `vera-system/memory/curate-flags.md`, the ledger, which is curate's own output surface
- Don't add comments like "removed by curate" — just remove cleanly
- Don't auto-create skills or auto-edit skills/patterns — flag for human review only

---

*Author: Shareef Ellis · [@shareefatwork](https://x.com/shareefatwork)*
