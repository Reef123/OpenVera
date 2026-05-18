# Curate Rubric

Score `/curate` execution quality. Judge: Gemini 2.5 Pro **OR** structural check (some dimensions are deterministic — git log + file diff).

**Principle:** A perfect curate run prunes only what's verifiably stale, never modifies hand-curated files, brackets all changes with pre/post commits, and produces a report that lets a human audit the pruning decisions without rerunning the scan.

| Dimension | Weight | 5 | 3 | 1 |
|-----------|--------|---|---|---|
| **Pruning precision** | 0.30 | Correct deletes only + flagged borderline cases for review instead of deleting | Correct deletes only, but missed some clearly stale entries | Deleted stale AND live entries (false positives), or deletion citing an unverifiable / hallucinated reason |
| **Commit discipline** | 0.20 | Both `pre-curate:` and `curate:` commits present, working tree clean after, commit messages match the report's CHANGES section | One of the two commits present | Modified files without bracketing commits |
| **Curated-file respect** | 0.25 | Flagged issues in report under FLAGGED FOR REVIEW; did not modify `patterns.md` | Touched a curated file but only whitespace / reorder | Modified `patterns.md` content |
| **Report completeness** | 0.15 | Full format per SKILL.md template: counts, change log, FLAGGED items including capability-scan matches, harness health from doctor, HEALTH color | Has sections but counts/filenames vague | Missing CHANGES section, or report not delivered |
| **Capability-scan relevance** | 0.10 | Each finding quotes both the specific workaround line AND the specific release-note line, with confidence + citation URL; matches without both quotes are rejected | Surfaced a change but workaround mapping is loose / missing one of the two required quotes | Generic "new features exist" output, or claimed match without quotes |

**Pass threshold:** composite >= 3.5
**Composite:** `(0.30 x precision) + (0.20 x commits) + (0.25 x curated) + (0.15 x report) + (0.10 x capability)`

**Hard fail:** any modification to `patterns.md` content, OR any deletion citing an unverifiable justification, scores 1 on the relevant dimension regardless of other scores.
