---
name: happy-path
created: 2026-04-21
rubric: curate
---

## Input

Auto-memory state at run time:
- 12 files in the project's `~/.claude/projects/<hash>/memory/` directory
- 3 files reference paths that no longer exist (project archived, script removed)
- 2 pairs of files cover the same concept with overlap
- 1 contradiction across two files (e.g., conflicting model recommendation for the same use case)

`vera-system/memory/` is at its normal state. Last curate ran > 7 days ago.

## Expected Qualities

- Pre-flight `pre-curate: save current state` commit if working tree dirty (else skip cleanly).
- Deletes the 3 stale files, verifying path-doesn't-exist before each deletion.
- Merges each duplicate pair into one file, keeping the more detailed/recent content.
- Resolves the contradiction by keeping the more recent entry.
- MEMORY.md index updated: 3 lines removed, 2 descriptions updated.
- Curate Report has full format with INVENTORY counts, CHANGES enumerating each delete/merge, GROWTH delta showing -3 files.
- Post-flight `curate: pruned 3 stale, merged 2 dupes` commit.
- `.claude/last-curate-date` updated to today.
- Working tree clean after.
- Should NOT modify any file in `vera-system/memory/patterns.md`.

## Why this test exists

The basic shape of a successful curate run. If this fails, something fundamental is broken — start debugging here before any other test.
