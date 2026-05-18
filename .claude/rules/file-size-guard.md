# File Size Guard

After writing to any of these files, check the line count:

| File | Threshold | Action |
|------|-----------|--------|
| `CLAUDE.md` | 150 lines | Split non-essential content into `who-i-am/` or `memory/` |
| `state.md` | 100 lines | Archive completed items, keep only current state |
| `memory/patterns.md` | 200 lines | Promote rarely-used patterns to a secondary file |
| `ROADMAP.md` | 150 lines | Archive completed milestones |

If a file exceeds its threshold, mention it. Don't silently let files grow — bloated context files waste tokens every session.
