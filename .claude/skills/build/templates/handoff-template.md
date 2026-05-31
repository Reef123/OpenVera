# Handoff — &lt;Project Name&gt;

*V0 → V1 handoff contract. `/build full` reads this first.*
*Generated at Stage 4b from `.build/validation.md` + `.build/review.md` + spec.md + running code. Auto-drafted; sharpened in the retro phase.*

---

## Outcome

&lt;One sentence. What V1 must achieve. Reaches for `idea.md ## The bet`, not just the literal Job from spec.md. Imperative shape: "V1 must …", not "We hope V1 will …"&gt;

---

## Audience

This file is read by `/build full` running on Claude Opus 4.7 / GPT-5.5-class autonomous agents.

- **Literal instruction following.** The agent will NOT generalize an instruction from one item to another. Every invariant, constraint, and anti-pattern below must be enumerated explicitly.
- **No inference of "and similar."** If V0 has three protected files and a hidden fourth that should be protected too, the agent will only protect the three listed.
- **Constraints are front-loaded by design.** Invariants and anti-patterns come BEFORE observable behavior in this file because the constraint-prominence research (Jiang et al. 2025, arXiv:2505.07591) shows mid-prompt constraints get systematically missed.

---

## Invariants (DO NOT MODIFY without an ADR)

Concrete file paths and behaviors V0 demonstrates that V1 must preserve. Each invariant uses **SHALL** (EARS notation, Mavin 2009) for unambiguous parsing.

- &lt;Specific path&gt; SHALL &lt;specific behavior&gt;. &lt;Why this is invariant — one line.&gt;
  - Example: `app/api/items/route.ts` SHALL return JSON with keys `{id, title, completed}`. Existing consumers (the React list view at `app/page.tsx`) depend on this shape.
- &lt;Next invariant — be specific. Generic statements like "preserve the API contract" don't survive literal instruction following.&gt;
- &lt;Next.&gt;

**Format reminders for generation:**
- Concrete file paths beat general statements ("Do not modify `app/Models/Driver.php`" beats "preserve auth model").
- SHALL, not should/must/will/can.
- 3-7 invariants is the right density. Fewer than 3 → V0 didn't lock enough down. More than 7 → likely codifying accidents.

---

## Anti-patterns (DO NOT for this project)

Adversarial bookend to invariants. Failure modes observed during V0 build (mined from `.build/decisions.log`) that V1 must NOT repeat.

- DO NOT &lt;specific action&gt;. &lt;What went wrong when V0 tried this, or why it would break.&gt;
  - Example: DO NOT introduce optimistic UI updates to the task list. V0 trialed this; it desynced with the API and produced phantom items on refresh.
- DO NOT &lt;next&gt;.

**Generation rule:** mine `.build/decisions.log` for "tried X, reverted because Y" entries. Empty log → 0-2 anti-patterns from spec.md ## Out of Scope items that V1 might be tempted to walk back into. Never invent anti-patterns; they must trace to observed behavior or explicit user-stated scope.

---

## Observable behavior (what V0 actually does — measured, not promised)

Enumerated, factual. Read from running code + `.build/validation.md` PASS entries. **This is "what V0 demonstrably does", NOT "what V0 was supposed to do".** Distinguish from the next two sections.

**Routes / entry points:**
- &lt;Exact path or command — `GET /api/items`, `npm run dev`, `./bin/cli --help`&gt;

**Data shapes:**
```
&lt;Exact schemas — input, storage, output. JSON Schema or TypeScript types where applicable. Closed schemas only — V1 must know which fields are load-bearing vs additive.&gt;
```

**Success states:**
- &lt;What V0 paints / returns / writes when the happy path runs. Verbatim from `.build/validation.md` PASS items.&gt;

**Failure states V0 handles explicitly:**
- &lt;Validation errors, empty states, missing data — what V0 catches and how.&gt;

**Failure states V0 does NOT handle:**
- &lt;Race conditions, auth failures, network errors, edge cases V0 walked past. V1 must decide whether to handle these, NOT inherit V0's silence.&gt;

---

## What V0 proved

Concrete claims V0 demonstrably validates. Stevenson, Burnell & Fisher (2024, Journal of Management) frame MVPs as **learning instruments** — what learning did this V0 produce?

- &lt;Claim V0 supports + the evidence in the running code or validation. E.g. "Top-of-page action button with single 'Add Task' CTA — users intuit this without instruction (validated in 30-second test, .build/validation.md PASS)."&gt;
- &lt;Next claim with evidence.&gt;

---

## What V0 did NOT prove

**Critical section.** Felin, Gambardella, Stern & Zenger (2024, Journal of Management) — MVPs can produce **misleading feedback** for novel value propositions. Without this section, V1 risks codifying V0 accidents as invariants.

- &lt;Thing V0's success does NOT validate. E.g. "V0 ran with a single user — multi-user behavior, conflict resolution, and shared state are unproven. Any V1 invariant claiming 'data is per-user' has no V0 evidence."&gt;
- &lt;Next unproven assumption.&gt;
- &lt;Next.&gt;

**Generation rule:** for every claim in ## What V0 proved, ask "what would have to be true elsewhere for this to generalize?" That counterfactual is a candidate for this section. Also include: any spec.md ## Out of Scope item the user explicitly cut — V0 doesn't prove the cut item is unwanted, just that V1 will need to decide.

---

## Constraints

Hard limits on V1's solution space.

- **Stack lock:** &lt;framework + key libs + exact versions tested working. E.g. `SvelteKit 2.5.18 + TailwindCSS 4.0.7 + Drizzle 0.30.10`. V1 must not silently upgrade.&gt;
- **Validation method:** &lt;Browser / Run command / Test suite. V1 must validate the same way V0 was validated.&gt;
- **Aesthetic floor:** &lt;Palette name from `/frame` rotation set. V1 must apply same DESIGN.md tokens, no aesthetic regression.&gt;
- &lt;Any project-specific constraint surfaced in spec.md or Stage 0 Pressure Test.&gt;

---

## Open questions (V1 must resolve)

Decisions V0 punted on. V1 must surface these in its Stage 0 ## Trigger options (per `full-sdlc.md` Stage 0 instruction: generate trigger options from `handoff.md ## Open questions` first, then `v1-notes.md ## Friction`, then `spec.md` Cut List).

- &lt;Thing V0 hardcoded that needs a real decision. E.g. "Date format is currently `YYYY-MM-DD` everywhere. Locale support, relative dates ('2 days ago'), and timezone handling are all V1 decisions."&gt;
- &lt;Next open question.&gt;

---

## Provenance

Auto-generated metadata. V1 uses this to assess freshness and audit-trail-back to V0 evidence.

- **Generated:** &lt;ISO date at Stage 4b&gt;
- **V0 score:** &lt;X.X/5.0 from Stage 3&gt;
- **Validation evidence:** `.build/validation.md` (&lt;N&gt; PASS, &lt;N&gt; FAIL entries)
- **Review evidence:** `.build/review.md` (&lt;Critical/High/Medium/Low count&gt;)
- **Source artifacts read:** idea.md, spec.md, &lt;component files enumerated&gt;
- **Retro-updated:** &lt;ISO date when user-triggered retro sharpened this file. Empty until retro fires.&gt;

---

*Theoretical anchor: this artifact is a **boundary object** (Star & Griesemer 1989, Social Studies of Science 19:387-420). Plastic enough that V1 can adapt to local needs; robust enough that V0→V1 preserves common identity across the handoff.*
