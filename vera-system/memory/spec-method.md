# Spec Method: Divergent Reasoning Before Build

**Status:** Reusable pattern. Not build-specific. Reference doc.
**Audience:** Vera, and any agent or human running a design-reasoning session before a build.
**Pairs with:** the `/build new` Stage 0 interview gate (`vera-system/memory/interview-method.md` — blind-spot scan, `/panel` retired v1.21), `/build`, the Phase Planning stages in `phases.md` (decision records + reversal triggers).

---

## What this is

This is the method for the phase **before** code. The phase where we prune a decision tree, kill forks, and find the one decision that everything else is a surface of. The output of this phase is a settled spec, not a working artifact. That spec is the handoff to build.

The whole value of this phase is friction. The reasoning is nonlinear and conversational, and the work happens in the push-back. A build agent run on an unsettled design produces confident scaffolding, and we spend more time unwinding confident output than the thinking would have cost. So we finish reasoning here, then hand a settled spec across once.

**When this applies:** the next question is still "which branch is true."
**When to exit:** the next question becomes "build this." See Exit Criteria.

---

## Entry guard: reversibility triage

There are exit criteria but the dangerous failure is at the *front*. This method is the most sophisticated avoidance pattern available: forking is intellectually satisfying and produces no artifact. The reasoning *feels* like progress while no thing gets built.

So gate every fork by reversibility before spending divergent energy on it:

| Door | Treatment |
|---|---|
| **Two-way** (cheap to reverse) | Pick the default and move. No fork. Reversing later is cheaper than reasoning now. |
| **One-way** (expensive or irreversible) | Earns the full divergent treatment below. |

Most forks are two-way doors wearing one-way clothes. The entry gate: *is the next decision a one-way door? If not, this method is overkill — just build, and let the build teach you.* This is the mirror of the exit criteria, and it's the governor that keeps the phase from becoming the work.

Run this method at all only when **both** hold: the next question is "which branch is true," **and** the branch is a one-way door. Otherwise skip straight to build.

---

## Core moves

| Move | What it means | Why |
|---|---|---|
| Triage by reversibility | Before forking, ask if the decision is a one-way door. Two-way doors get a default, not a fork. | Equal divergent energy on every fork is how the method becomes avoidance. Most forks don't earn it. |
| Divergent before convergent | Reason to settle. Build to execute. Do not mix the modes. | A build agent on an unsettled design builds the wrong thing fast. |
| Fork and collapse | End turns on a fork. Push on it. Collapse it. | Forks force the next edge into view. |
| Kill forks in writing | When you collapse a fork, write the killed branch and a one-line reopen trigger into the live tree. | An unwritten kill comes back next session. The trigger tells you exactly when the kill stops holding. |
| Find the invariant | When the same decision keeps reappearing in different clothes, name it. | One decision usually governs the whole system. Everything else is its surface. |
| Name the load-bearing unknown | Tag the empirical assumption everything rests on. Do not build floors above it untested. | Stacking confident design on an untested floor makes the doc read as more solid than the foundation justifies. |
| Verify external facts before they kill | A kill-reason resting on an external claim (API behavior, a doc statement, a third-party constraint) gets checked against the primary source before the kill is written into the tree. | External "facts" arriving via a model or from memory are hypotheses until sourced — a fork has died before on a confabulated API claim. |
| One spot, then tune | Pick a fixed starting point. Change one variable. Read one delta. | A fixed start makes the first measurement interpretable. Tuning everything at once is unattributable. |
| Measure mechanism, not outcome | Instrument so a failure attributes to one broken assumption, or is flagged as confounded. | "It worked / it failed" teaches almost nothing. The mechanism is the signal. |
| Metaphor to architecture, then break it | Reason from an analogy to a design. Then find exactly where the analogy stops holding. | The break point is where the real edge cases live, and naming it is the judgment. |
| Prose first, formalism later | Hold math and formal contracts until the concept is stable. Append as a versioned, volatile-flagged layer. | The formal layer moves most where it touches unmeasured things. Freeze the concept, let the math float. |
| Falsify, do not prove | You cannot prove a design adequate from inside it. Accumulate failed honest attempts to break it. | Confidence is "N escalating attacks survived," not "it is correct." |
| Pull back to the goal | Periodically stop and re-anchor on the actual deliverable. | The intellectually interesting layer is rarely the priority layer. It is easy to optimize the thinking and lose the goal. |

---

## The cheapest probe

Naming the load-bearing unknown is half the move. The other half: test it with the **cheapest probe that can falsify it**, not the most satisfying one. The ladder, cheapest first:

1. **Existing evidence** — has this already been answered by past behavior? (Usage logs, prior sessions, an old project's fate.)
2. **Ask** — one direct question to the person whose behavior is the unknown.
3. **Simulate** — walk the workflow on paper / in conversation for a week's worth of moments.
4. **Stub** — the fake version: a static page, a hardcoded table, a manual step standing in for the automation.
5. **Build** — the real thing. Last resort as a *probe*; correct only once a cheaper rung already said yes.

Rule: state which rung you're on and why the cheaper rungs can't answer it. Motivating case: a dashboard built before probing whether it would be opened — the unknown was "will anyone open a second surface?", existing evidence (rung 1, $0) already said no, and a full build (rung 5) sat unused for months answering a question that was already answered.

---

## The live decision tree

The decision tree is **not** a section you write up at the end. It is the running scratchpad from turn one, and it is the artifact that survives interruption.

Two reasons it has to be live:

- **Re-litigation.** A killed fork that isn't written down with its kill-reason comes back next session and gets re-argued from scratch. If it's not in a file, it doesn't exist after reboot — and that applies *mid-spec*, not just at handoff.
- **Reversal triggers.** Every killed branch carries a one-line *reopen trigger*: what would have to become true to bring this branch back. Write it at the moment you kill the fork, not later — that's when you actually know why you killed it. When a build assumption breaks, the triggers tell you exactly which node to climb back to instead of re-reasoning the whole tree.

Shape of a live tree entry:

```
NODE: <the decision>
  ├─ CHOSEN: <branch>  — because <reason>
  └─ KILLED: <branch>  — because <reason>  ⟲ reopen if <trigger>
```

Keep it in the spec file as it grows. The thick path is what we chose; dotted/killed branches stay visible with their reasons and triggers. The diagram makes path-dependence legible, so a broken early assumption tells you exactly where to climb back to. Carry it across sessions verbatim — resuming a spec means reading the tree, not rebuilding it.

**In `/build`:** the PRD template's `## Decision Classification` table is this tree's landing spot — every major decision gets a Type (one-way/two-way), Rationale, and Reversal Trigger column. Killed forks that don't rise to PRD-level (implementation-detail forks collapsed during Phase 2/4) still get one line each in the tech spec or phase plan's rationale notes, with the same reopen-trigger shape. Don't build a second decision-log mechanism — write into the one that already exists.

---

## The role contract

The reasoning partner is **co-architect, not executor**.

- Analysis over validation. Insight over reassurance. Surface the pattern the other party may miss.
- End turns on the next real edge, usually a fork. Do not end on a summary that closes prematurely.
- Push back. Reasonable disagreement is the product, not a problem to smooth over.
- Flag your own blind spots in-line and briefly. Name when you are reaching for a win instead of sitting on the hard question.
- Do not explain process unless asked. Skip scaffolding. High density is fine.
- Tree stops moving, or forks keep collapsing too easily → that's the trigger for the `/build new` Stage 0 interview gate's blind-spot lenses. Run the gate instead of grinding.

---

## Anti-patterns to watch

These recurred and got caught. Expect them again.

| Anti-pattern | Tell | Correction |
|---|---|---|
| Method as avoidance | Forking and re-forking on a decision that's actually a two-way door, because reasoning feels safer than building. | Run the reversibility gate. If it's reversible, pick a default and build. |
| Closure one layer early | Calling something "closed" to land the turn when only its membership is settled and its contract is open. | Separate the conceptual decision from the interface layer. State which one actually closed. |
| Building toward wins | Reaching for the next buildable node because closing feels like progress, while walking past the harder unresolved question. | The hard questions are the ones being avoided on the way to an easy artifact. Stay on them. |
| Reviewer pull to the interesting layer | Every sharp reviewer drags you toward the measurement or theory layer, because that is where the intellectual content lives. | That is not where the priority is. It is where the excitement is. Resist until the goal-critical thing exists. |
| Study mistaken for deliverable | A plan that produces a report, a benchmark, or a taxonomy when the goal needed a running thing. | Ask what artifact the goal actually requires. A document rarely clears a "shipped a thing" bar. |
| Over-forking | Posing a clean binary when the real object is a menu of options on different axes. | If a third or fourth option is real, say so. Do not flatten a menu into a fork to end a turn cleanly. |
| Unwritten kills | Re-arguing a fork you already collapsed last session because the kill never made it into the tree. | Kill forks in writing, with a reopen trigger, the moment you collapse them. |
| False from-the-armchair resolution | Trying to reason to a number that can only be measured. | Some questions are not gates. They are the first thing the loop measures. Stop reasoning and run. |
| Usage assumed, mechanism measured | The build instruments its mechanism carefully while the adoption assumption ("someone will actually open/use this") goes untested. | Name the usage/channel assumption as a load-bearing unknown and probe it on the ladder before building. Mechanism metrics on an unused artifact measure nothing. |

---

## Document shape that emerges

The spec is layered so the conceptual record stays clean while volatile parts move under it.

1. **Thesis.** One sentence. The invariant the whole system reduces to.
2. **Prose body.** The reasoning, kept pure. Each section a settled or explicitly-open node.
3. **Formal layer, appended.** Math, signatures, contracts. Banner-marked volatile, versioned. Added only once the prose is stable, because formalizing it first locks in something the build will change.
4. **Decision tree.** The live tree (see above), finalized. Thick path is what we chose. Dotted is what we killed, why, and the reopen trigger.
5. **Status section, honest.** Fact vs inference labeled. Reasoning is not result. If the doc is held with more confidence than the measurements justify, say so. Open nodes flagged, not softened.

Labeling convention carried throughout: `[Inference]`, `[Speculation]`, `[Unverified]`, `[Assumption]`. Never present inference as fact.

---

## Exit criteria

Hand to build when **all** hold:

- The thesis is fixed and the invariant is named.
- The remaining open items are interface-shaped, not "which branch is true."
- Every killed fork has a written reopen trigger; nothing live is being re-litigated in your head.
- There is a fixed first spot and a single first variable to change.
- The instrument can attribute a failure to one assumption.

The cleanest first handoff is the load-bearing measurement, because it gates everything above it and is the least ambiguous build. Do not hand off the elegant part first.

---

## Checklist for Vera

Run this against any spec before accepting it as buildable.

- [ ] Is this even a one-way door? If reversible, why are we reasoning instead of building?
- [ ] Is there a one-sentence thesis, and is it the invariant or just a feature?
- [ ] What is the single load-bearing unknown, and is it tested or assumed?
- [ ] What is the cheapest probe on the ladder (existing evidence < ask < simulate < stub < build) that can falsify it — and why isn't a cheaper rung enough?
- [ ] Is the adoption/channel assumption ("who opens this, and when") named as an unknown, or silently assumed?
- [ ] Does any kill-reason rest on an external claim that hasn't been checked against a primary source?
- [ ] Does the live decision tree exist as a file (the PRD's Decision Classification table, or spec.md for V0), with every killed branch carrying a reopen trigger?
- [ ] Is anything being re-argued that was already killed in a prior session?
- [ ] Does any section read as more settled than its evidence allows?
- [ ] Is the first build the floor measurement, or an elegant upper layer?
- [ ] Can a failure in the first run attribute to one assumption, or is it confounded?
- [ ] Did a fork get closed by fiat to land a turn? Re-open it.
- [ ] Is the formal layer flagged volatile and versioned, or hardened too early?
- [ ] Does the plan produce the artifact the goal requires, or a study adjacent to it?
- [ ] Has the goal been restated recently, or did the thinking drift from it?

---

## One line to keep

The thinking is the product in this phase — but only on the one-way doors. The discipline that makes a trajectory climb instead of wander: gate forks by reversibility, kill the rest in writing with a reopen trigger, measure mechanism not outcome, and name the load-bearing unknown before building on it.
