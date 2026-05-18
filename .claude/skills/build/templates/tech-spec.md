# Technical Design Template

Use this template when creating `{projects_dir}/<project-slug>/plans/02-TECH-SPEC.md`.

**Context required:** Read `01-PRD.md` before writing this.

Replace all `[PLACEHOLDER]` values. Remove this instruction block.

---

```markdown
# Technical Design: [Project Name]

**Author:** Vera
**Date:** [YYYY-MM-DD]
**Status:** Draft | Approved
**PRD Reference:** `01-PRD.md`

---

## Overview

**What are we building?**
[1-2 sentences — technical summary, not business summary]

**Key Technical Decisions:**
1. [Decision + rationale]
2. [Decision + rationale]

---

## Stack Evaluation (MANDATORY for new projects)

*Evaluate before choosing. Familiarity is one factor, not the deciding factor.*

| Criterion | [Stack A] | [Stack B] | [Stack C] |
|-----------|-----------|-----------|-----------|
| [Project-specific need 1] | /10 | /10 | /10 |
| [Project-specific need 2] | /10 | /10 | /10 |
| [Project-specific need 3] | /10 | /10 | /10 |
| Component/library ecosystem | /10 | /10 | /10 |
| Team familiarity | /10 | /10 | /10 |

**Choice:** [Stack] — [1-sentence justification with data, not comfort]

*For existing projects being upgraded: skip this section, note "Existing codebase — stack inherited."*

---

## Architecture

### System Context

[How this fits into the existing system — what it connects to, what it replaces/extends]

```
[ASCII diagram or description of component relationships]
```

### Component Design

#### Component 1: [Name]
- **Purpose:** [What it does]
- **Inputs:** [What it receives]
- **Outputs:** [What it produces]
- **Dependencies:** [What it needs]

#### Component 2: [Name]
- **Purpose:** [What it does]
- **Inputs:** [What it receives]
- **Outputs:** [What it produces]
- **Dependencies:** [What it needs]

### Data Model

[Key data structures, schemas, state management approach]

```
[Schema or type definitions]
```

---

## Technology Choices

| Concern | Choice | Rationale | Alternatives Considered |
|---------|--------|-----------|------------------------|
| [area] | [tech] | [why] | [what else, why not] |

---

## Decision Records

For each one-way door decision (from PRD Decision Classification), document the full reasoning and reversal conditions.

### DR-1: [Decision Title]
- **Context:** [What situation led to this decision]
- **Decision:** [What we decided]
- **Consequences:** [What this enables and what it prevents]
- **Reversal trigger:** [Specific condition that would make us revisit: "if X happens, reconsider this"]
- **Status:** Proposed | Accepted

### DR-2: [Decision Title]
- **Context:** [What situation led to this decision]
- **Decision:** [What we decided]
- **Consequences:** [What this enables and what it prevents]
- **Reversal trigger:** [Specific condition]
- **Status:** Proposed | Accepted

---

## API / Interface Design

### Interface 1: [Name]
- **Type:** [REST / CLI / function / event]
- **Contract:**
```
[Interface definition — endpoints, function signatures, event schemas]
```

---

## File Structure

```
[Proposed file/folder layout for this project's code]
```

**Rationale:** [Why this structure]

---

## Integration Points

| System | Direction | Protocol | Auth | Notes |
|--------|-----------|----------|------|-------|
| [system] | inbound/outbound | [how] | [method] | |

---

## Security Considerations

- [Authentication approach]
- [Authorization model]
- [Data handling / PII]
- [Secret management]

---

## Performance Considerations

- [Expected load / scale]
- [Bottleneck analysis]
- [Caching strategy if any]

---

## Error Handling

| Error Scenario | Detection | Recovery | User Impact |
|---------------|-----------|----------|-------------|
| [what can go wrong] | [how we know] | [what we do] | [what user sees] |

---

## Migration / Rollback

- **Migration plan:** [How to go from current to new state]
- **Rollback plan:** [How to revert if something goes wrong]
- **Data migration:** [If applicable]

---

## Open Technical Questions

- [ ] [Question that affects implementation]

---

## Approval

- [ ] User approves architecture
- [ ] User approves technology choices
```
