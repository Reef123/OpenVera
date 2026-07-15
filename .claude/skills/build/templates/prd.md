# PRD Template

Use this template when creating `{projects_dir}/<project-slug>/plans/01-PRD.md`.

Replace all `[PLACEHOLDER]` values. Remove this instruction block.

---

```markdown
# PRD: [Project Name]

**Author:** Vera + [Your Name]
**Date:** [YYYY-MM-DD]
**Status:** Draft | Approved
**Steer brief:** Consumed steer brief: [file + one line on what it changed] | No steer brief on file.

---

## Problem Statement

**What problem does this solve?**
[2-3 sentences describing the pain point or opportunity]

**Who has this problem?**
[Target user/persona — be specific]

**What happens if we don't solve it?**
[Cost of inaction]

---

## Goals

### Primary Goals
1. [Goal with measurable outcome]
2. [Goal with measurable outcome]

### Non-Goals (Explicitly Out of Scope)
- [Thing we're NOT doing and why]
- [Thing we're NOT doing and why]

---

## Requirements

### Functional Requirements

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-1 | [What the system must do] | Must | |
| FR-2 | [What the system must do] | Must | |
| FR-3 | [What the system should do] | Should | |
| FR-4 | [What the system may do] | May | |

### Non-Functional Requirements

| ID | Requirement | Target | Notes |
|----|-------------|--------|-------|
| NFR-1 | Performance | [metric] | |
| NFR-2 | Security | [standard] | |
| NFR-3 | Reliability | [target] | |

---

## User Stories

### Story 1: [Title]
**As a** [user type], **I want** [action], **so that** [outcome].

**Acceptance Criteria:**
- [ ] [Testable criterion]
- [ ] [Testable criterion]

### Story 2: [Title]
**As a** [user type], **I want** [action], **so that** [outcome].

**Acceptance Criteria:**
- [ ] [Testable criterion]
- [ ] [Testable criterion]

---

## Concept Wireframes

*Generated during PRD phase for UI projects. Skip for API-only projects.*

**Design Tool Project:** `[project-id]`

| Screen | Story | Screen ID | Device | Notes |
|--------|-------|------------------|--------|-------|
| [screen name] | Story 1 | [screen-id] | Desktop | [concept note] |

---

## Constraints

- **Technical:** [Platform, language, framework constraints]
- **Timeline:** [Any deadlines or time pressure]
- **Dependencies:** [External systems, APIs, people]
- **Budget:** [Cost constraints if any]

---

## Decision Classification

Classify major decisions by reversibility. One-way doors get more scrutiny downstream; two-way doors move fast.

| Decision | Type | Rationale | Reversal Trigger |
|----------|------|-----------|-----------------|
| [e.g., "Use SQLite for storage"] | One-way / Two-way | [Why this classification] | [What would make us revisit: "if >100 concurrent writers"] |
| [e.g., "Use Tailwind for styling"] | One-way / Two-way | [Why] | [Trigger] |

**One-way door:** Irreversible or expensive to reverse. Needs deep analysis in Phase 2+3.
**Two-way door:** Easy to swap later. Decide fast, move on.

---

## Value Threshold

**Would a user choose this over the manual alternative?** [Yes/No + why]

If the answer is no or weak, the scope is too thin. Expand before proceeding. A tool that doesn't cross the "worth learning" threshold is waste regardless of how correct it is.

---

## Delight Features

*3-5 features beyond strict requirements that would make users recommend this. At least one build phase must be allocated to delight in Phase 4.*

1. [Feature that makes users say "this is better than I expected"]
2. [Feature that makes users say "this is better than I expected"]
3. [Feature that makes users say "this is better than I expected"]

---

## Success Metrics

| Metric | Current | Target | How to Measure |
|--------|---------|--------|---------------|
| [metric] | [baseline] | [goal] | [method] |

---

## Open Questions

- [ ] [Question that needs answering before proceeding]

---

## Approval

- [ ] User approves scope
- [ ] User approves requirements
- [ ] User approves non-goals
```
