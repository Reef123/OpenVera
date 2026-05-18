# Ship Log Template

Use this template when creating `{projects_dir}/<project-slug>/plans/06-SHIP-LOG.md`.

**Context required:** Read `01-PRD.md` and `05-QA-REPORT.md` before shipping.

Replace all `[PLACEHOLDER]` values. Remove this instruction block.

---

```markdown
# Ship Log: [Project Name]

**Date:** [YYYY-MM-DD]
**Status:** Deployed | Rolled Back | Partial

---

## Deployment Summary

**What was deployed:** [1-2 sentence summary]

**Where:**
- [Environment / system / location]

**How:**
- [Deployment method — manual, script, CI/CD]

---

## Deployment Steps

1. [Step taken]
2. [Step taken]
3. [Step taken]

---

## Verification

| Check | Result | Notes |
|-------|--------|-------|
| [Smoke test 1] | Pass/Fail | |
| [Smoke test 2] | Pass/Fail | |
| [User-facing verification] | Pass/Fail | |

---

## Files Shipped

| File | Action | Location |
|------|--------|----------|
| [file] | Created/Modified/Deleted | [path] |

---

## Documentation Updated

- [ ] `vera-system/state.md` — state updated
- [ ] `ROADMAP.md` — task marked complete
- [ ] [Other docs] — [what was updated]

---

## Rollback Plan

**If issues arise:**
1. [Rollback step 1]
2. [Rollback step 2]

**Rollback tested:** Yes / No

---

## Post-Deploy Notes

- [Anything observed after deployment]
- [Monitoring to watch]
- [Follow-up tasks identified]

---

## Project Closeout

**Total elapsed time:** [from PRD to ship]
**Build phases completed:** [N]
**PRD requirements met:** [N of M]
**Tech debt remaining:** [summary]

---

## Process Cost

Track ceremony-to-code ratio to calibrate future Scope Calibration tier decisions.

| Metric | Value |
|--------|-------|
| **Total LoC shipped** | [count] |
| **Total test count** | [count] |
| **SDLC artifacts generated** | [count of .md files in {projects_dir}/<slug>/plans/] |
| **Build phases** | [N] |
| **LoC per build phase** | [total LoC / build phases] |
| **Tier used** | Lite / Standard / Full |
| **Tier appropriate?** | Yes / No — [if No: what tier should it have been?] |
| **Sessions consumed** | [count] |

**Was the process overhead justified?** [Yes — complexity warranted rigor / No — should have been Tier [X] / Partially — [specific phases] were ceremony]

**Decision records created:** [N] | **Decision records that were actually referenced during build:** [N]

---

**Lessons learned:**
- [What went well]
- [What to do differently next time]
- [Process improvement for next project]
```
