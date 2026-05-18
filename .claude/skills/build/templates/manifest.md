# MANIFEST Template

Use this template when creating `{projects_dir}/<project-slug>/plans/MANIFEST.md`.

Replace all `[PLACEHOLDER]` values. Remove this instruction block.

---

```markdown
# MANIFEST: [Project Name]

**Slug:** [project-slug]
**Created:** [YYYY-MM-DD]
**Last Updated:** [YYYY-MM-DD]
**Status:** active | paused | complete | abandoned
**Tier:** Lite | Standard | Full
**Tier Override:** [None | "User chose [X] because [reason]"]

---

## Current Phase

**Phase:** [1-8]
**Phase Name:** [PRD | Technical Design | Architecture Review | Phase Planning | Build Phase N | Code Review N | Integration & QA | Ship]
**Phase Status:** in-progress | awaiting-approval | complete
**Build Phase:** [N of M] (only during phases 5-6)

---

## Phase History

| # | Phase | Status | Date Started | Date Completed | Artifact |
|---|-------|--------|-------------|----------------|----------|
| 1 | PRD | [status] | [date] | [date] | `01-PRD.md` |
| 2 | Technical Design | [status] | [date] | [date] | `02-TECH-SPEC.md` |
| 3 | Architecture Review | [status] | [date] | [date] | `03-ARCH-REVIEW.md` |
| 4 | Phase Planning | [status] | [date] | [date] | `04-PHASE-PLAN.md` |
| 5 | Build Phase 1 | [status] | [date] | [date] | `build/phase-1-spec.md` |
| 6 | Code Review 1 | [status] | [date] | [date] | `build/phase-1-review.md` |
| 5 | Build Phase 2 | [status] | [date] | [date] | `build/phase-2-spec.md` |
| 6 | Code Review 2 | [status] | [date] | [date] | `build/phase-2-review.md` |
| 6.5 | Simplification Pass | [status] | [date] | [date] | `build/phase-2-simplification.md` |
| 6.7 | Security Review (OWASP Top 10) | [status] | [date] | [date] | `build/phase-2-security.md` |
| 7 | Integration & QA | [status] | [date] | [date] | `05-QA-REPORT.md` |
| 8 | Ship | [status] | [date] | [date] | `06-SHIP-LOG.md` |

---

## Project Summary

**One-liner:** [What this project does in one sentence]

**Key Requirements:** (from PRD)
- [Requirement 1]
- [Requirement 2]
- [Requirement 3]

**Architecture:** (from Tech Spec)
- [Key architectural decision 1]
- [Key architectural decision 2]

**Build Phases:** [N total] (from Phase Plan)
1. [Phase 1 name — brief description]
2. [Phase 2 name — brief description]

---

## Context Loading Guide

To resume this project, read these files in order:

1. **This file** (MANIFEST.md) — current state
2. **Current phase artifact** — see Phase History for which file
3. **Phase-specific context** — see table below

| Current Phase | Read These |
|---------------|-----------|
| 2 (Tech Design) | `01-PRD.md` |
| 3 (Arch Review) | `01-PRD.md`, `02-TECH-SPEC.md` |
| 4 (Phase Planning) | `01-PRD.md`, `02-TECH-SPEC.md`, `03-ARCH-REVIEW.md` |
| 5 (Build N) | `01-PRD.md`, `04-PHASE-PLAN.md` (phase N section) |
| 6 (Code Review N) | `01-PRD.md`, `02-TECH-SPEC.md`, `build/phase-N-spec.md` |
| 7 (QA) | `01-PRD.md`, `04-PHASE-PLAN.md`, all `build/phase-*-review.md` |
| 8 (Ship) | `01-PRD.md`, `05-QA-REPORT.md` |

---

## Trace Map

Links PRD requirements → build phases → files changed. Updated during each build phase. Read during QA to verify coverage.

| PRD Req | Build Phase | Key Files | QA Status |
|---------|-------------|-----------|-----------|
| [R1: requirement] | [Phase N] | [src/foo.ts, src/bar.ts] | [Tested / Not Tested] |
| [R2: requirement] | [Phase N] | [src/baz.ts] | [Tested / Not Tested] |

**Coverage:** [N of M requirements traced] | **Untested:** [list any]

---

## Open Questions

- [Any unresolved questions from any phase]

## Decisions Log

| Decision | Rationale | Phase | Date |
|----------|-----------|-------|------|
| [What was decided] | [Why] | [#] | [date] |
```
