# Architecture Review Template

Use this template when creating `{projects_dir}/<project-slug>/plans/03-ARCH-REVIEW.md`.

**Context required:** Read `01-PRD.md` and `02-TECH-SPEC.md` before writing this.

Replace all `[PLACEHOLDER]` values. Remove this instruction block.

---

```markdown
# Architecture Review: [Project Name]

**Reviewer:** Vera
**Date:** [YYYY-MM-DD]
**Status:** Pass | Pass with Conditions | Fail
**Spec Reference:** `02-TECH-SPEC.md`

---

## Review Summary

**Verdict:** [Pass / Pass with Conditions / Fail]

[2-3 sentence summary of the review outcome]

---

## PRD Alignment Check

| Requirement (from PRD) | Addressed in Tech Spec? | How | Gap? |
|------------------------|------------------------|-----|------|
| FR-1: [requirement] | Yes/No/Partial | [where] | [gap description] |
| FR-2: [requirement] | Yes/No/Partial | [where] | [gap description] |
| NFR-1: [requirement] | Yes/No/Partial | [where] | [gap description] |

**Unaddressed requirements:** [List any PRD requirements not covered by the tech spec]

---

## Architecture Assessment

### Strengths
- [What's good about this design]

### Concerns

| # | Concern | Severity | Recommendation |
|---|---------|----------|----------------|
| 1 | [issue] | Critical/High/Medium/Low | [fix] |
| 2 | [issue] | Critical/High/Medium/Low | [fix] |

**Severity guide:**
- **Critical:** Blocks proceeding. Must fix before build.
- **High:** Significant risk. Should fix before build.
- **Medium:** Acceptable risk. Fix during build.
- **Low:** Nice to have. Fix if time permits.

---

## Pre-Mortem

*Assume this project has failed. Why?*

| Failure Mode | Category | Likelihood | Why We Missed It |
|-------------|----------|------------|-----------------|
| [e.g., "Kivy doesn't render on Wayland"] | Platform/Integration | High/Med/Low | [What assumption was wrong] |
| [e.g., "Event loop blocks during API call"] | Concurrency | High/Med/Low | [What assumption was wrong] |
| [e.g., "imsg CLI abandoned, no alternative"] | Supply Chain | High/Med/Low | [What assumption was wrong] |
| [e.g., "Can't tell if system is working without reading logs"] | Operational Visibility | High/Med/Low | [What assumption was wrong] |

**Categories to check:** Platform/Integration, Concurrency/Load, Supply Chain, Operational Visibility, The Thing Nobody Verified

**If any failure mode has Likelihood: High → elevate to a Concern in the section below.**

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation | Owner |
|------|-----------|--------|------------|-------|
| [what could go wrong] | High/Med/Low | High/Med/Low | [plan] | [who] |

---

## Complexity Assessment

| Component | Complexity | Confidence | Notes |
|-----------|-----------|------------|-------|
| [component] | Low/Med/High | High/Med/Low | [why] |

**Overall complexity:** [Low / Medium / High]
**Estimated build phases:** [N] (validated in Phase 4)

---

## Dependencies Check

- [ ] All external dependencies available and accessible?
- [ ] API contracts stable or under our control?
- [ ] No circular dependencies in component design?
- [ ] Shared state managed explicitly?

---

## Anti-Pattern Check

- [ ] No premature optimization?
- [ ] No over-engineering for hypothetical future requirements?
- [ ] No god objects or god functions?
- [ ] Separation of concerns maintained?
- [ ] No implicit coupling between components?
- [ ] Error handling is explicit, not swallowed?

---

## Conditions for Approval

[If "Pass with Conditions" — list what must happen before proceeding]

1. [Condition]
2. [Condition]

---

## Approval

- [ ] User accepts risk assessment
- [ ] Conditions addressed (if any)
```
