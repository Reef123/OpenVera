# File Size Guard

The thresholds live in code — `SIZE_THRESHOLDS` in `vera-system/scripts/vera_config.py` — and are enforced mechanically: `doctor.py` checks them on every run, `/doc-sync` Step 8 checks them after stamping, and `/curate` must not commit with MEMORY.md over its cap. To check by hand:

```bash
python3 vera-system/scripts/curate-mode.py sizes
```

Remediation when a file prints OVER:

| File | Action |
|------|--------|
| `CLAUDE.md` | Split non-essential content into `who-i-am/` or `memory/` |
| `state.md` | Archive completed items, keep only current state |
| `memory/patterns.md` | Promote rarely-used patterns to a secondary file |
| `memory/MEMORY.md` | Consolidate entries — URGENT: lines past the cap are silently truncated at load time |
| `memory/lessons.md` | Let /curate prune promoted + stale one-off lines |
| `ROADMAP.md` | Archive completed milestones |

Don't silently let files grow — bloated context files waste tokens every session.
