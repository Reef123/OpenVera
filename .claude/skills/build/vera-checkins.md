# Vera Check-ins

At each pipeline boundary, print a short assistant-voice note so the user understands what just happened and what to watch for. These replace silent stage transitions.

## Format

Always bold the header, so the user trains their eye: *bold elephant line = Vera is telling me something.*

```
**🐘 Quick Vera check-in, <user-name>:** <one sentence — what the pipeline just did>.

[Watch for:                                                 ← entire block optional
- <thing 1 — specific to this moment, grounded in the actual artifacts>
- <thing 2 — optional, cut if nothing worth flagging> ]
```

**The "Watch for:" block is conditional.** Default to omitting it. Only include when there's a genuine project-specific risk worth surfacing now (not generic scaffolding-warnings). Aligned with the voice rule below — zero bullets when nothing's worth flagging.

## Voice rules

Source of truth: `vera-system/who-i-am/voice.md` — read its "Onboarding & user-facing surfaces" section once per session. Build check-ins are an onboarding surface (the user sees them on their first build), so the 5% warmth ceiling applies: no exclamation, no celebration, specific over generic, zero-or-one-or-two bullets — never more.

Skill-specific:
- Read `vera-system/relationships/user.md` once to get the name. Drop it naturally in the opening line.
- **Fall back gracefully.** If `voice.md` or `user.md` is missing (fresh install, pre-bootstrap), use a neutral tone and "you" instead of a name.

## Fire points

### V0 (`/build new`)

- After Kickoff + Purpose (Stage 0 submit)
- After Parallel Sprint completes (Stage 1 → Stage 2 transition)
- After first browser/command verify succeeds (Stage 2 mid-point)
- After Score lands (Stage 3 → Stage 4 transition)

### Full SDLC (`/build full`)

**Targeted Fix path:**
- After Kickoff submit (Stage 0 → Stage 1)
- After first browser/command verify succeeds
- After Score (Stage 2)

**Structured Upgrade / Major Rework paths:**
- After Kickoff submit (Stage 0 → Stage 1)
- After research/scout completes (if requested — before SDLC phases start)
- After PRD lands (Phase 1)
- After Architecture Review (Phase 3) — last decision point before heavy build
- After all build phases complete (entering Integration/QA)
- After Score + Complete (Stage 2)

Skip per-phase check-ins inside Phase 5 (build) + Phase 6 (code review) cycles — those repeat and would be noise. Treat the whole build-phases block as one milestone.
