# QA Report Template

Use this template when creating `{projects_dir}/<project-slug>/plans/05-QA-REPORT.md`.

**Context required:** Read `01-PRD.md`, `04-PHASE-PLAN.md`, and all `build/phase-*-review.md` files before QA.

Replace all `[PLACEHOLDER]` values. Remove this instruction block.

---

```markdown
# QA Report: [Project Name]

**Tester:** Vera
**Date:** [YYYY-MM-DD]
**Status:** Pass | Fail
**Build Phases Completed:** [N of N]

---

## Integration Test Results

### Cross-Phase Integration

| Test | Phases Involved | Result | Notes |
|------|----------------|--------|-------|
| [test name] | [1, 2] | Pass/Fail | [details] |

### End-to-End Tests

| Test | Steps | Result | Notes |
|------|-------|--------|-------|
| [test name] | [steps taken] | Pass/Fail | [details] |

---

## Acceptance Criteria (from Phase Plan)

**IMPORTANT:** Distinguish Tested (ran a test, observed a result) from Analyzed (read the code, looks correct). Only Tested items count toward the pass rate. "Pass (design)" is NOT a pass — mark it Analyzed.

| # | Criterion | Verification | Result | Evidence |
|---|-----------|-------------|--------|----------|
| 1 | [criterion from 04-PHASE-PLAN.md] | Tested / Analyzed | Pass/Fail/Not Tested | [how verified] |
| 2 | [criterion from 04-PHASE-PLAN.md] | Tested / Analyzed | Pass/Fail/Not Tested | [how verified] |

**Pass Rate (Tested only):** [N of M tested criteria passing] — Analyzed items excluded from this count

---

## PRD Requirements Final Check

| ID | Requirement | Met? | Verified By |
|----|-------------|------|-------------|
| FR-1 | [requirement] | Yes/No/Partial | [test or review reference] |
| FR-2 | [requirement] | Yes/No/Partial | [test or review reference] |
| NFR-1 | [requirement] | Yes/No/Partial | [measurement] |

**Coverage:** [N of M] functional requirements met (tested). [N of M] non-functional requirements met (tested). [N] items analyzed-only (not counted in pass rate).

---

## Browser Smoke Tests (MANDATORY for UI projects)

*If no browser tests exist, this is a BLOCKER. Do not proceed to ship.*

**Command:** `npm run test:smoke`
**Environment:** Real browser (Playwright + Chromium), NOT jsdom

```
[Paste full test output here]
```

| Test | Result | Notes |
|------|--------|-------|
| Hydration — all routes | Pass/Fail | [buttons clickable, forms accept input] |
| CSP — no violations | Pass/Fail | [no EvalError, no blocked scripts] |
| Navigation — SPA transitions | Pass/Fail | [client-side routing works] |
| Assets — no broken requests | Pass/Fail | [no 4xx/5xx responses] |
| Dark mode — no errors | Pass/Fail | [toggle works, no JS errors] |

**Every NFR below must be FUNCTIONALLY tested (exercised in real browser), not just grepped for in code.**

---

## Non-Functional Verification

### Performance
- [Metric tested]: [Result vs Target] — **How verified:** [DevTools measurement / Lighthouse / real browser timing]

### Security
- [Security check]: [Result] — **How verified:** [Exercised in browser, not just code review]

### Reliability
- [Reliability check]: [Result]

---

## Code Review Summary

| Phase | Review Status | Critical Findings | Open Items |
|-------|--------------|-------------------|------------|
| Phase 1 | [Pass/Fail] | [count] | [count remaining] |
| Phase 2 | [Pass/Fail] | [count] | [count remaining] |

---

## Outstanding Issues

| # | Issue | Severity | Recommendation |
|---|-------|----------|----------------|
| 1 | [issue] | Critical/High/Medium/Low | [fix or accept] |

---

## Plan Drift Audit

Compare Phase 4 plan vs actual build. Aggregate all deviations from build specs.

| Phase | Planned Deliverable | Actual | Deviation |
|-------|-------------------|--------|-----------|
| [N] | [What was planned] | [What was built] | [None / Minor / Major] |

**Drift rate:** [N of M deliverables deviated]
**Assessment:** [On track / Minor drift (acceptable) / Major drift (>30% — are we still building what the PRD asked for?)]

---

## Tech Debt Summary

[Aggregate tech debt from all build phases]

- [Debt item 1 — from phase N]
- [Debt item 2 — from phase N]

**Recommendation:** [Address before ship / Accept for now / Schedule follow-up]

---

## Verdict

**Result:** [Pass / Fail]

**If Pass:** Ready to ship. Proceed to Phase 8.

**If Fail:**
- [What must be fixed]
- [Which phase to revisit]
- [Re-test plan]

---

## Approval

- [ ] All acceptance criteria met
- [ ] User approves for ship
```
