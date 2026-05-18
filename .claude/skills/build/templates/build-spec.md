# Build Spec Template

Use this template when creating `{projects_dir}/<project-slug>/plans/build/phase-N-spec.md`.

**Context required:** Read `01-PRD.md` and `04-PHASE-PLAN.md` (relevant phase section) before building.

Replace all `[PLACEHOLDER]` values. Remove this instruction block.

---

```markdown
# Build Spec: Phase [N] — [Phase Name]

**Date Started:** [YYYY-MM-DD]
**Date Completed:** [YYYY-MM-DD]
**Status:** in-progress | tests-passing | complete

---

## Scope (from Phase Plan)

[Copy the scope section from 04-PHASE-PLAN.md for this phase]

---

## Implementation Log

### Files Created
| File | Purpose | Lines |
|------|---------|-------|
| [path] | [what it does] | [count] |

### Files Modified
| File | Change | Reason |
|------|--------|--------|
| [path] | [what changed] | [why] |

---

## Test Results

### Tests Written BEFORE Code
- [ ] [Test name]: [what it verifies]
- [ ] [Test name]: [what it verifies]

### Test Execution

```
[Paste test output here]
```

**Result:** [All passing / N failing]
**Failing tests:** [List any failures and why]

---

## PRD Validation

| Requirement | Met? | Evidence |
|-------------|------|----------|
| FR-[N] | Yes/No/Partial | [How verified] |

---

## Verification Evidence (BOLDFACE — blocking)

*Default: FAILED. Each item must be actively proven PASSED with evidence. Empty = build spec rejected.*

| Check | Status | Evidence |
|-------|--------|----------|
| Browser boot | FAILED | [Screenshot path or "N/A — no UI in this phase"] |
| Console clean | FAILED | [0 errors confirmed via Chrome console read, or "N/A"] |
| Routes verified | FAILED | [List each route loaded: /, /editor, /wizard, or "N/A"] |
| Wireframes loaded | FAILED | [Screen IDs retrieved from design tool, or "N/A — no Visual Spec"] |

**Rule:** "N/A" is valid for non-UI phases. "FAILED" or empty is never valid. If a check fails, fix the code before writing the spec.

---

## Visual Targets (UI phases only)

*Skip if this phase has no UI work.*

### Wireframes Referenced
| Screen | Screen ID | Loaded? | What It Specifies |
|--------|-----------|---------|-------------------|
| [screen name] | [ID] | Yes — retrieved from design tool | [layout, color, key elements] |

### Visual Deviations
| Element | Wireframe Shows | Implementation | Justification |
|---------|----------------|----------------|---------------|
| [element] | [what design says] | [what was built] | [why different] |

---

## Deviations from Plan

| Planned | Actual | Reason |
|---------|--------|--------|
| [what was planned] | [what was done] | [why it changed] |

---

## Technical Debt Introduced

- [Any shortcuts taken, with justification]
- [Any TODOs left for later phases]

---

## Notes for Code Review

- [Areas that need careful review]
- [Tricky implementations to explain]
- [Design decisions made during build]
```
