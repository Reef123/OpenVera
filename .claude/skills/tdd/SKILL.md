---
name: tdd
description: "Red-green-refactor cycle for /build full Phase 5. Internal skill — invoked by phases.md, not by the user. Governs HOW each test gets written, not WHICH tests to write (that's phase-plan.md)."
internal: true
---

# TDD — Red-Green-Refactor

Phase 5 already prescribes test-first; this skill enforces the loop.

---

## When this fires

`/build full` Phase 5 entry. The phase-plan.md test spec for the current phase is already written — it names WHICH behaviors to test. This skill governs how each one gets implemented.

Skip this skill for:
- V0 builds (`/build new`) — validation is browser/command/validator-agent, not red-green-refactor.
- Targeted Fix path of `/build full` — no Phase 5, no test spec, fast change.
- Phases 1-4 (PRD / Tech Design / Arch Review / Phase Plan) — no code written.

---

## The cycle

For each behavior in the phase's test spec, complete one full RED → GREEN → REFACTOR loop before starting the next.

### RED — Write the failing test

1. Pick ONE behavior from the test spec. Not the easiest, not the hardest — the next in the spec's order.
2. Write the test file (or append to an existing one). Test name reads as the expected outcome: `returns_normalized_path_when_given_relative_input` over `test_one`.
3. Run the test. **See it fail.** Read the failure message.
4. **Tripwire:** failure says "module not found," "no such function," or "import error" — you haven't actually tested the behavior, you've tested that code doesn't exist yet. Fix that: add the minimum scaffolding so the failure becomes an *assertion* failure (function exists, returns wrong thing). The first real RED is an assertion failure.

### GREEN — Smallest code that passes

1. Write the smallest possible implementation that makes the test pass. Hard-coded return values are allowed when only one case is tested.
2. Run the test. **See it pass.**
3. Run the rest of the suite. Confirm nothing else broke.
4. **Tripwire:** if green required more than ~10 lines, the test was probably too coarse. Note this — the next test will refine, but flag it in the build-spec output so reviewers can see why.

### REFACTOR — Improve structure on green

1. Tests are green. Now improve the code without changing behavior.
2. Rename misleading identifiers. Extract duplication. Simplify conditionals.
3. After each refactor edit, re-run the test. Stay green.
4. **Tripwire:** if a refactor turns the test red, you changed behavior, not structure. Revert and try again.
5. Skip refactor only when the *next* test in the spec will obviously restructure this code (e.g., next test forces extraction into a function). Note "deferred to next cycle" in the build-spec.

Then return to RED with the next behavior.

---

## What makes a good failing test

- **One observable behavior per test.** Not "the whole feature works" — one input → one expected output, or one event → one expected state change.
- **Names the outcome, not the mechanism.** `rejects_when_path_escapes_root` over `test_path_validation`.
- **Fails for the right reason.** Assertion failure on the value being tested. Not `ImportError`, not syntax error, not test-runner config drift.
- **EARS-compatible when the acceptance criterion is EARS.** If the criterion in `handoff.md ## Invariants` is `When <event>, the system shall <response>`, the test name and assertion mirror that: `when_<event>_shall_<response>`. EARS notation reference lives in `.claude/skills/build/v0-stages.md`.
- **Independent.** Doesn't depend on test execution order. Setup and teardown are explicit.

If a test would need to read multiple files, mock multiple services, or set up half the system — the unit is wrong. Move it to integration tests or shrink the unit.

---

## Smallest code that passes

The point of "smallest" is to force the *next* test to do the generalization work, not your imagination.

- One test covers one input → return that value hard-coded.
- Two tests cover two inputs → add an `if`.
- Three tests with the same shape → extract the pattern.

This is sometimes called "fake it 'til you make it" or "triangulation." Either is fine. **What's not fine:** writing the full generalized implementation when only one test exists. That's speculative abstraction — the next test might force a different shape and the abstraction wastes effort.

Exception: if the implementation is genuinely one line (`return x + y`), write it. Don't ceremoniously hard-code `return 5` first when the real implementation is obvious and equally short.

---

## When to refactor

After every green, before the next red. The green test is the safety net — refactor while it's there.

Refactor when:
- A name reads wrong on second look.
- Two blocks of code do the same thing.
- A function has grown past one screen.
- A conditional has more than two branches and the branches share structure.

Skip refactor when:
- The next test in the spec will obviously restructure this code anyway. Refactoring now means refactoring again in 5 minutes. Note "deferred" and move on.
- The structure is already clean. Don't refactor for the sake of it. Tripwire: "what specifically am I improving?" If you can't name it, skip.

---

## Anti-patterns

| Anti-pattern | Fix |
|--------------|-----|
| Writing all tests first, then all code | Waterfall in TDD clothing. One test, one implementation, one refactor — then the next test. |
| Testing implementation, not behavior | Tests asserting "function X called function Y" instead of "given input X, output is Y" couple tests to refactors and break on every cleanup. |
| Refactoring while red | The safety net is gone. Get to green first, then refactor. |
| Modifying tests after they pass to match what the code actually does | This is weakening tests. Covered by `.claude/rules/test-integrity.md` — don't do it, fix the code instead. |
| Skipping the "see it fail" step | If you didn't watch the test fail, you don't know it can fail. Run it once on no implementation. |
| Tests that pass without the implementation existing | The test isn't actually exercising the unit under test. Verify by deleting the implementation — the test must now fail. |

---

## What this skill does NOT cover

- **Test selection** — which behaviors to test. That's `.claude/skills/build/templates/phase-plan.md` test specs, written in Phase 4.
- **Test infrastructure setup** — which runner, which assertion library, which fixtures pattern. That's Phase 2 Tech Design, decided per-project.
- **EARS criteria writing** — `while/when/shall` notation. Reference: `.claude/skills/build/v0-stages.md` § handoff.md Invariants.
- **Integration tests across multiple components** — TDD applies, but the cycle is slower and the "smallest code that passes" rule loosens. This skill is calibrated to unit tests. For integration, use the same loop but expect each red→green to take longer.
- **Test integrity (don't weaken tests)** — `.claude/rules/test-integrity.md` covers this. Skill references, doesn't duplicate.

---

*Author: Shareef Ellis · [@shareefatwork](https://x.com/shareefatwork)*
