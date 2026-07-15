# Memory

Persistent knowledge across sessions. Signal only — no noise.

**Key files:**
- `patterns.md` — Core operating patterns, anti-patterns (LOADED ON BOOT). Hand-curated — never machine-appended.
- `lessons.md` — Machine-appendable capture lane. /build failures and doc-sync course corrections append one dated line each; /curate flags 3+ recurrences for promotion to patterns.md and prunes the rest.
- `promotions.tsv` — Machine ledger of lessons promoted to patterns.md. `curate-mode.py promotions` records each promotion and verifies the lesson stopped recurring (statuses: PROVISIONAL, VALIDATED, FAILED).
- `MEMORY.md` — Auto-memory index (grows over time)
- `delegation-policy.md` - How orchestrating skills spawn subagents: fresh-default/fork-rare/worktree-for-parallel-writes, tier-per-task (cheap tier for plumbing, capable tier for judgment gates), MAX 3 concurrent, spawn contracts + fail-closed artifact verification. Read before editing `/build`, `/research`, the `/build new` Stage 0 interview gate, or any skill that spawns agents.
- `hooks-map.md` — inventory of all 6 `.claude/settings.json` hooks (event, script, purpose, fail-open/fail-closed) + candidates evaluated and rejected, with reopen triggers.

**Rule:** If you discover a pattern, write it down immediately. Not later. Now. Confirmed cross-session patterns go to patterns.md; single-session lessons go to lessons.md and earn promotion by recurring.

**Rule:** The moment a recurring lesson gets promoted into patterns.md (usually the user approving it mid-conversation), record it in the same breath: `python3 vera-system/scripts/curate-mode.py promotions record --match "<2-4 word phrase from the lesson lines>" --pattern "<patterns.md heading>"`. Promotion is rarely a formal event; if the record waits for /curate, the moment is gone and the pattern is never verified.

**Rule (append-with-revision):** When new information contradicts a stored fact, search for the conflict FIRST (grep the key entities and their aliases across memory), then write the new entry AND mark the old one superseded in place: a strikethrough or a `SUPERSEDED-BY: <new entry>, <YYYY-MM-DD>` note. Never silently delete; never leave two contradicting entries standing unmarked. Recall should return current belief plus provenance. /curate audits both directions: old entries missing their superseded mark, and new entries that contradict an unsuperseded older fact.

**Update triggers:** Pattern discovered, anti-pattern hit, cost lesson learned, research insight confirmed across multiple interactions.
