# Full SDLC Pipeline (`/build full`)

Complete software development lifecycle. PRD to shipped product with test-first methodology, code reviews, and quality gates.

**First step:** If upgrading from a V0, read `spec.md` — especially the **Cut List**. These are features that were deliberately deferred. Evaluate each: does real usage confirm it's needed, or was cutting it the right call? The Cut List seeds Phase 1 (PRD) requirements.

**Supporting files:**
- [phases.md](phases.md) — detailed instructions for each SDLC phase
- [sdlc-patterns.md](sdlc-patterns.md) — anti-patterns and review checklists
- [templates/](templates/) — 9 artifact templates (PRD, tech spec, arch review, etc.)

---

## Overview

```
Phase 1: PRD              → define WHAT and WHY
Phase 2: Technical Design  → define HOW (includes stack re-evaluation)
Phase 3: Architecture Review → adversarial review, pre-mortem
Phase 4: Phase Planning    → break into ordered phases with test specs
Phase 5: Build Phase N     → test-first: write tests, then code
Phase 6: Code Review N     → adversarial code review
Phase 6.5: Simplification  → remove accidental complexity (after last build phase)
Phase 7: Integration & QA  → end-to-end verification
Phase 8: Ship              → deploy, verify, document
```

Each phase has:
- **Context to read** — only what's needed (keeps context lean)
- **A template** — in `templates/` for the artifact
- **A gate** — must pass before proceeding (user approval or automated check)

---

## How to Execute

1. **Create MANIFEST** via script:
   ```bash
   python3 vera-system/scripts/manifest-update.py <slug> init --tier <targeted|structured|major>
   ```

2. **Run phases sequentially.** Read [phases.md](phases.md) for detailed instructions per phase. Each phase:
   - Reads its required context (and ONLY its required context)
   - Produces an artifact from its template
   - Passes its gate (user approval or test pass)
   - Updates MANIFEST

3. **Build phases loop.** Phase 5 (Build) and Phase 6 (Code Review) repeat for each planned build phase:
   ```
   Build Phase 1 → Code Review 1 → Build Phase 2 → Code Review 2 → ... → Simplification → QA → Ship
   ```

4. **Continue across sessions.** MANIFEST tracks state. After context compression or new session:
   - Read MANIFEST
   - Read the artifact for the current phase
   - Continue from where you left off

---

## Phase Gate Summary

| Phase | Gate |
|-------|------|
| PRD | User approves scope |
| Tech Design | User approves architecture |
| Arch Review | No Critical findings open |
| Phase Plan | User approves phases + test specs |
| Build Phase N | All tests passing |
| Code Review N | No Critical findings |
| Simplification | Reviewed all files, removed or justified |
| QA | All acceptance criteria tested and passing |
| Ship | Deployed, smoke-tested, docs updated |

---

## Context Efficiency

Each phase reads ONLY what it needs:

| Phase | Reads |
|-------|-------|
| PRD | Nothing (fresh start) |
| Tech Design | PRD |
| Arch Review | PRD + Tech Spec |
| Phase Plan | PRD + Tech Spec + Arch Review |
| Build N | PRD + Phase Plan (section N only) |
| Code Review N | PRD + Tech Spec + Build Spec N |
| QA | PRD + Phase Plan + all Review files |
| Ship | PRD + QA Report |

---

## Scoring & Completion

After Ship:
1. Score using Gemini (same as V0 Stage 3 in `v0-stages.md` "Stage 3: Score")
2. If score < 3.5 → fix cascade: outputs → process → instructions via `/improve`
3. User retro (same AskUserQuestion as V0 Stage 4 Retro Phase) → write retro.md. Unlike V0, /build full's retro fires immediately at completion — the user has already used V0 and has signal coming into /build full, so no need to defer.
4. Run `/doc-sync`
5. Update `vera-system/state.md` and `vera-system/ROADMAP.md`
