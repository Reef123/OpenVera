# conversations/

`/doc-sync` writes one log here per session, named `NNN-YYYY-MM-DD.md` (e.g., `001-2026-04-20.md`). They're how you recover context across sessions.

Each log follows this shape:

```markdown
# Session NNN — YYYY-MM-DD

## Summary
One paragraph: what you shipped or decided.

## What Happened
- Bullet list of the real work

## Course Corrections
| What Went Wrong | What Changed | Generalizable? |
|----------------|-------------|----------------|
| ... | ... | Yes/No — if yes, promoted to patterns.md |

## Files Changed
| File | Action |
|------|--------|
| path | Created/Updated/Deleted |

## State at End
Where things stand. What's next.
```

### Example (fictional)

> Built recipe tracker V0 — searchable list + detail view with ingredient scaling. Scored 3.8/5.0, shipped. Course correction: started building categories before checking community patterns; `/scout` showed tags beat categories for recipe apps. Generalized to "scout before building UI patterns" in `patterns.md`.

Don't edit these manually mid-session — `/doc-sync` writes the whole file at the end. If you need to capture mid-session state, use `state.md` and `ROADMAP.md`.
