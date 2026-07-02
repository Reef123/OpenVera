# Phase Plan Template

Use this template when creating `{projects_dir}/<project-slug>/plans/04-PHASE-PLAN.md`.

**Context required:** Read `01-PRD.md`, `02-TECH-SPEC.md`, and `03-ARCH-REVIEW.md` before writing this.

Replace all `[PLACEHOLDER]` values. Remove this instruction block.

---

```markdown
# Phase Plan: [Project Name]

**Author:** Vera
**Date:** [YYYY-MM-DD]
**Status:** Draft | Approved
**Total Build Phases:** [N]

---

## Phase Strategy

**Ordering rationale:** [Why phases are sequenced this way — dependency chain, risk reduction, etc.]

**Test methodology:** Tests are designed here, written BEFORE code in each build phase.

---

## Design System (UI projects only)

*Extracted from PRD wireframes. This section is the builder's visual north star — read it before every UI build phase.*

**Visual identity:** [e.g., "Tonal layering — dark sidebar, light workspace, dark code preview. No borders between regions."]

**Color palette (PRESCRIPTIVE — use these exact values):**
| Token | Hex | Tailwind Class | Usage |
|-------|-----|---------------|-------|
| primary | [#0078D4] | [bg-[#0078D4] text-white] | [CTA buttons, active nav] |
| surface | [#ffffff] | [bg-white] | [Center panel, form area] |
| sidebar | [#1e1e2e] | [bg-[#1e1e2e] text-gray-300] | [Left nav, project tree] |
| preview | [#1e1e2e] | [bg-[#1e1e2e] text-gray-100] | [YAML preview panel] |
| border | [none] | [border-0] | [Tonal contrast replaces borders] |
| input-bg | [#f8f9fa] | [bg-gray-50 border-0 focus:ring-1 focus:ring-[primary]] | [All form inputs] |
| error | [#cf222e] | [text-red-600] | [Validation errors] |
| success | [#1a7f37] | [text-green-600] | [Validation pass indicators] |

**Typography (PRESCRIPTIVE):**
| Element | Font | Weight | Size | Class |
|---------|------|--------|------|-------|
| body | [Inter] | [400] | [14px] | [font-sans text-sm] |
| heading | [Inter] | [600] | [18px] | [font-sans text-lg font-semibold] |
| label | [Inter] | [500] | [12px] | [font-sans text-xs font-medium uppercase tracking-wide] |
| code | [monospace] | [400] | [13px] | [font-mono text-sm] |

**Component patterns (PRESCRIPTIVE — copy these classes):**
| Component | Classes | Notes |
|-----------|---------|-------|
| form input | [bg-gray-50 border-0 rounded-md px-3 py-2 focus:ring-1 focus:ring-[primary]] | No visible border. Tonal contrast. |
| validation icon | [text-green-600 w-4 h-4] (pass) / [text-red-600 w-4 h-4] (fail) | Icons, not colored borders. |
| chip/tag | [bg-[primary]/10 text-[primary] rounded-full px-3 py-1 text-sm] | For trigger phrases, lists. |
| nav item active | [bg-[primary] text-white rounded-md px-3 py-1.5] | Pill style, not underline. |
| panel divider | [none — use background color change] | Tonal layering, not border lines. |

**Interaction patterns:** [e.g., "Chip/tags for lists. Slide-out panels for detail editing. Contextual help sidebars."]
**Design tool project ID:** [ID for wireframe retrieval]

*If you're building UI and this section is empty, STOP. Go back to Phase 1 and create wireframes first.*

---

## Build Phase 1: [Name]

### Scope
- [What gets built in this phase]
- [What gets built in this phase]

### Deliverables
- [ ] [Specific file or component]
- [ ] [Specific file or component]

### Dependencies
- **Requires:** [What must exist before this phase starts]
- **Produces:** [What downstream phases need from this]

### Interfaces
*Skip only if nothing downstream consumes this phase's output.*
- **Consumes:** [shape of data/function/component this phase expects to receive — a type or one-line schema, not code]
- **Produces:** [shape this phase hands off — must match the next phase's Consumes]

### PRD Requirements Addressed
- FR-[N]: [requirement]

### Visual Spec
*Skip if this phase has no UI work.*
- **Screens:** [Screen IDs from PRD wireframes, refined for this phase]
- **Key interactions:** [user flows this phase implements]

### Test Spec

**Unit Tests:**
- [ ] [Test: what behavior to verify]
- [ ] [Test: what behavior to verify]

**Integration Tests:**
- [ ] [Test: what end-to-end behavior to verify]

**Edge Cases:**
- [ ] [Test: what edge case to cover]

### Estimated Complexity
- **Files:** [count]
- **Complexity:** Low / Medium / High
- **Risk:** [primary risk for this phase]

---

## Build Phase 2: [Name]

### Scope
- [What gets built in this phase]

### Deliverables
- [ ] [Specific file or component]

### Dependencies
- **Requires:** Phase 1 complete
- **Produces:** [What downstream phases need from this]

### Interfaces
*Skip only if nothing downstream consumes this phase's output.*
- **Consumes:** [shape this phase expects from Phase 1's Produces — must match]
- **Produces:** [shape this phase hands off]

### PRD Requirements Addressed
- FR-[N]: [requirement]

### Visual Spec
*Skip if this phase has no UI work.*
- **Screens:** [Screen IDs from PRD wireframes, refined for this phase]
- **Key interactions:** [user flows this phase implements]

### Test Spec

**Unit Tests:**
- [ ] [Test: what behavior to verify]

**Integration Tests:**
- [ ] [Test: what end-to-end behavior to verify]

**Edge Cases:**
- [ ] [Test: what edge case to cover]

### Estimated Complexity
- **Files:** [count]
- **Complexity:** Low / Medium / High
- **Risk:** [primary risk for this phase]

---

## [Repeat for each build phase]

---

## Cross-Phase Concerns

### Shared State
- [What state is shared between phases and how]

### Integration Points
- [Where phases connect — APIs, shared files, events]

### Rollback Boundaries
- [If phase N fails, can we revert without losing phase N-1?]

### Requirement Coverage Map
*Every FR-N/NFR-N from the PRD must have at least one phase. A requirement with no row here is a gap shipping silently — fix before the Phase 4 gate.*

| Requirement | Covered by |
|-------------|-----------|
| FR-[N] | Build Phase [N] |
| NFR-[N] | Build Phase [N] |

---

## Acceptance Criteria (for QA phase)

These criteria will be tested after all build phases complete:

- [ ] [End-to-end acceptance criterion from PRD]
- [ ] [End-to-end acceptance criterion from PRD]
- [ ] [Performance target met]
- [ ] [Security requirement verified]

---

## Approval

- [ ] User approves build phases
- [ ] User approves test specs
- [ ] User approves phase ordering
```
