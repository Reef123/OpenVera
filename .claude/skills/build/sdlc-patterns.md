# SDLC Patterns & Anti-Patterns

Reference material for all phases of the Build Full pipeline. Covers enterprise development anti-patterns, code review checklists, and quality gates.

---

## Enterprise Anti-Patterns

### Requirements Phase

| Anti-Pattern | Signs | Fix |
|-------------|-------|-----|
| **Scope Creep via Ambiguity** | PRD has vague requirements like "should be fast" or "user-friendly" | Every requirement gets a measurable acceptance criterion |
| **Gold Plating** | Adding features nobody asked for because they seem useful | Non-goals section in PRD. If it's not in requirements, it's out. |
| **Assumed Context** | PRD doesn't state constraints because "everyone knows" | Constraints section must be explicit. Future sessions DON'T know. |
| **Solution Disguised as Requirement** | "Use Redis for caching" instead of "Response time < 200ms" | Requirements describe WHAT, not HOW. Tech choices go in tech spec. |

### Architecture Phase

| Anti-Pattern | Signs | Fix |
|-------------|-------|-----|
| **Resume-Driven Development** | Choosing tech to learn it, not because it fits | Technology choices table must include "Alternatives Considered" |
| **Astronaut Architecture** | Over-abstracted design for hypothetical future needs | YAGNI. Design for current requirements. Document when to upgrade. |
| **Accidental Complexity** | System is more complex than the problem requires | Count components. If more components than requirements, simplify. |
| **Distributed Monolith** | Microservice boundaries but monolith coupling | Integration points table. If everything depends on everything, it's a monolith. |
| **Cargo Culting** | Copying architecture from FAANG without their scale/team | "Why does THIS project need this?" for every architectural choice |

### Build Phase

| Anti-Pattern | Signs | Fix |
|-------------|-------|-----|
| **Test-After** | Tests written after code, then rationalized to match | Build spec timestamps. Test spec comes from Phase 4, code comes after. |
| **Big Bang Integration** | All phases built independently, integrated at the end | Each build phase integrates with previous phases. No surprise merges. |
| **Premature Optimization** | Optimizing before measuring | Profile first. Optimize only measured bottlenecks. |
| **Copy-Paste Inheritance** | Duplicating code instead of finding the right abstraction | Code review catches this. But don't abstract on first duplication — wait for three. |
| **Lava Flow** | Dead code left "just in case" | If it's not tested and not called, delete it. Version control has history. |
| **Building Blind** | UI built from text specs with no visual reference | Generate wireframes during PRD (validate scope) + Phase Planning (spec each phase). Code review compares against them. |

### Architecture Review Phase

| Anti-Pattern | Signs | Fix |
|-------------|-------|-----|
| **Shallow Pre-Mortem** | Pre-mortem finds "what if the API is slow" but misses "Kivy doesn't work on Wayland" | Pre-mortem must check all 5 categories: Platform/Integration, Concurrency, Supply Chain, Operational Visibility, The Thing Nobody Verified |
| **Severity Avoidance** | All findings are Medium/Low — no High or Critical ever found | Must state what was checked at each severity level, even if nothing found. "No Critical findings — checked: platform compatibility, data loss scenarios, auth bypass" |
| **Own-Work Bias** | Self-review of own design is gentler than review of someone else's | Ask "what would an external reviewer flag?" before writing the review |

### Code Review Phase

| Anti-Pattern | Signs | Fix |
|-------------|-------|-----|
| **Rubber Stamping** | Review passes everything without findings | Every review MUST have at least one observation (even if Low severity) |
| **Bike Shedding** | Spending review time on style, ignoring logic | Checklist forces: correctness first, then design, then security, then style |
| **Review Scope Creep** | Reviewer suggests redesigns beyond the phase scope | Findings must reference current phase scope. Out-of-scope goes to tech debt. |

### QA Phase

| Anti-Pattern | Signs | Fix |
|-------------|-------|-----|
| **Happy Path Only** | All tests pass because no error cases tested | Phase Plan test specs MUST include edge cases section |
| **Testing Implementation** | Tests break when refactoring without behavior change | Test behavior, not implementation. Test the WHAT, not the HOW. |
| **QA as Afterthought** | QA finds requirements that should have been in PRD | Acceptance criteria defined in Phase 4, not discovered in Phase 7 |

---

## Code Review Checklist

Use during Phase 6 (Code Review). Check in this order, and report every finding across the whole checklist (don't stop at the first Critical).

### 1. Correctness (Most Important)

- [ ] Code does what the spec says it should
- [ ] All code paths have been considered (happy path + error paths)
- [ ] Edge cases from test spec are handled
- [ ] No off-by-one errors in loops/ranges
- [ ] Null/undefined/empty handled at boundaries
- [ ] Async operations have proper error handling
- [ ] State mutations are intentional and tracked

### 2. Design

- [ ] Consistent with `02-TECH-SPEC.md` architecture
- [ ] Single responsibility — each function/class does one thing
- [ ] Dependencies flow in one direction (no circular)
- [ ] Abstractions are justified (not premature)
- [ ] Interface contracts match between components

### 3. Security

- [ ] No hardcoded secrets, tokens, or credentials
- [ ] User input validated before processing
- [ ] Output encoded/escaped where needed (HTML, SQL, shell)
- [ ] Authentication checked on protected operations
- [ ] Authorization verified (not just authentication)
- [ ] Sensitive data not logged

### 4. Reliability

- [ ] Errors don't crash the system (graceful degradation)
- [ ] External calls have timeouts
- [ ] Retries have backoff (not tight loops)
- [ ] Resource cleanup in finally/defer blocks
- [ ] No race conditions in concurrent code

### 5. Maintainability

- [ ] Names are clear (no single-letter vars outside loops)
- [ ] No dead code or commented-out code
- [ ] Complex logic has comments explaining WHY (not WHAT)
- [ ] Consistent style with existing codebase
- [ ] No TODO without a tracking reference

