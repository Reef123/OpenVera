---
name: gap-handler
description: "Return-after-gap restart protocol. Pre-written by gap length so restarting after missing days doesn't require deliberation. Invoke when the user resumes after a gap or asks 'where was I'."
allowed-tools: Read, Write, Edit, Bash(python3 vera-system/scripts/doc-sync-gap.py *)
---

# Gap Handler

Handle returning after a gap in work. The plan is already written — no thinking required, just execute the protocol for the gap length.

## Why This Exists

Long gaps trigger three things that kill momentum: a shame spiral ("I already fell behind"), overwhelm ("where do I even start?"), and decision fatigue ("what should I do first?"). This skill removes all three by pre-deciding the restart shape.

## Step 1: Measure the Gap

Reuse doc-sync's own gap detector — don't duplicate the logic:

```bash
python3 vera-system/scripts/doc-sync-gap.py vera-system/conversations/
```

Output is one of `NO_HISTORY` / `NO_GAP` / `SHORT_GAP days=N` / `MEDIUM_GAP days=N` / `LONG_GAP days=N`. Map `days` to the protocol below (SHORT ≈ 2-7, MEDIUM ≈ 8-14, LONG ≈ 15+ — match to the closest band; exact boundaries aren't load-bearing).

## Step 2: Read State

Read `vera-system/state.md` (STATUS/SPRINT/NEXT) and, for MEDIUM/LONG gaps, `vera-system/ROADMAP.md` Current Sprint + the last 2 conversation logs.

## Protocol: Short Gap (2-7 days)

**Action:** Reconnect with purpose, then do the minimum next action.
**Mindset:** "I'm back. That's what matters."

1. State which project/thread you're picking up (from state.md NEXT) — wrong guesses get caught in line one.
2. Ask: "Still the right focus, or has it changed?"
3. If unchanged, do the next NEXT item.
4. If changed, update ROADMAP.md Current Sprint before proceeding.

## Protocol: Medium Gap (8-14 days)

**Action:** Relevance check before resuming.
**Mindset:** "Life happened. Now I choose what's next."

1. Summarize where things stood (state.md + ROADMAP.md Sprint) and how long the gap was.
2. For the active sprint item, ask: "Still relevant? Continue, park, or drop?"
3. Continue → do the next NEXT item.
4. Park → move it to ROADMAP.md Backlog with a wake condition (per the Parked pattern).
5. Drop → move to ROADMAP.md Done or delete, whichever fits, with a one-line reason.

## Protocol: Long Gap (15+ days)

**Action:** Full review. Fresh-start mentality.
**Mindset:** "Clean slate. What do I actually want?"

1. Read state.md, ROADMAP.md (Sprint + Backlog), and the last 2 conversation logs.
2. Present a short summary: where things were, how long the gap.
3. For each Backlog/Sprint item, ask: continue, park (with wake condition), or drop.
4. Ask: "Anything new to add?" — route new items the normal way (ideas.md for concepts, ROADMAP.md for tasks, or `inbox.md` if it needs more thought first).
5. Rewrite ROADMAP.md Current Sprint + state.md NEXT to reflect the decisions.

## The One Rule

**Coming back IS the win.** Note it in state.md's "Done This Session" as the first line of the session — the return itself is logged, not just the work that follows it.
