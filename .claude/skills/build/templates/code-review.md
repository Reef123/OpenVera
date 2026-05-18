# Code Review Template

Use this template when creating `{projects_dir}/<project-slug>/plans/build/phase-N-review.md`.

**Context required:** Read `01-PRD.md`, `02-TECH-SPEC.md`, and `build/phase-N-spec.md` before reviewing.

Replace all `[PLACEHOLDER]` values. Remove this instruction block.

---

```markdown
# Code Review: Phase [N] — [Phase Name]

**Reviewer:** Vera
**Date:** [YYYY-MM-DD]
**Status:** Pass | Pass with Findings | Fail
**Build Spec:** `build/phase-[N]-spec.md`

---

## Review Summary

**Verdict:** [Pass / Pass with Findings / Fail]

[2-3 sentence summary]

---

## Files Reviewed

| File | Lines | Review Notes |
|------|-------|-------------|
| [path] | [count] | [brief note] |

---

## Findings

### Critical (Must Fix Before Proceeding)

| # | File:Line | Finding | Fix |
|---|-----------|---------|-----|
| C1 | [location] | [issue] | [fix] |

### High (Should Fix Before Proceeding)

| # | File:Line | Finding | Fix |
|---|-----------|---------|-----|
| H1 | [location] | [issue] | [fix] |

### Medium (Fix During Build)

| # | File:Line | Finding | Fix |
|---|-----------|---------|-----|
| M1 | [location] | [issue] | [fix] |

### Low (Nice to Have)

| # | File:Line | Finding | Fix |
|---|-----------|---------|-----|
| L1 | [location] | [issue] | [fix] |

---

## Checklist

### Correctness
- [ ] Code does what the spec says
- [ ] Edge cases handled
- [ ] Error paths tested
- [ ] No silent failures

### Design
- [ ] Consistent with tech spec architecture
- [ ] No unnecessary complexity
- [ ] Separation of concerns maintained
- [ ] No premature abstraction

### Security
- [ ] No hardcoded secrets
- [ ] Input validation at boundaries
- [ ] Auth/authz checks where needed
- [ ] No injection vulnerabilities

### Tests
- [ ] Tests written before code (verified from build spec timeline)
- [ ] Tests cover happy path
- [ ] Tests cover error cases
- [ ] Tests are deterministic (no flaky tests)

### Visual Fidelity (UI phases only)
- [ ] Built UI matches wireframes from phase plan
- [ ] Deviations documented and justified
- [ ] Layout, spacing, hierarchy consistent with design spec

### Code Quality
- [ ] Names are clear and descriptive
- [ ] No dead code
- [ ] No commented-out code
- [ ] Consistent style with codebase

---

## PRD Alignment

| Requirement | Addressed? | Notes |
|-------------|-----------|-------|
| FR-[N] | Yes/No | [observation] |

---

## Tech Debt Assessment

- [ ] Any new tech debt introduced? [Details]
- [ ] Any existing tech debt resolved? [Details]

---

## Verdict Details

**If Pass:** Proceed to next build phase (or QA if this is the last phase).

**If Pass with Findings:** Fix High/Critical findings, then proceed. Medium/Low can be addressed later.

**If Fail:** Fix all Critical findings. Re-review required before proceeding.

### Action Items
1. [Action needed]
2. [Action needed]
```
