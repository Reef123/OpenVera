---
name: consult
description: "Decision accelerator — reframe the real question, summon 2-4 domain experts with different incentives, find agreement, isolate real tradeoffs, recommend a path. Free (no API calls). Use for any decision with genuine tradeoffs between known options."
argument-hint: <decision or tradeoff>
---

# /consult — Decision Accelerator

Not a panel generator. A decision accelerator. The recommendation is the point.

**Cost:** Free. No API calls. Use for any decision with genuine tradeoffs.

---

## Truthfulness Rule

`/consult` is perspective synthesis, not evidence gathering.

It does NOT invent facts, user behavior, market data, or implementation constraints. It reasons through tradeoffs between known options using simulated expert perspectives.

If the answer depends on external evidence, say so and route to `/scout` or `/research`. "I don't know whether users prefer X or Y" is not a consult question — it's a scout question.

Use `/consult` for: tradeoffs between known options.
Do NOT use `/consult` for: discovering whether a claim is true.

---

## How It Works

1. **Reframe** — What decision is actually being made? The stated question often isn't the real question. "Should we use Rust?" might really be "Can we afford the learning curve given our deadline?" Name the real decision before consulting.

2. **Select experts** — Use the selection algorithm below. If the user named specific experts in their prompt, use those instead.

3. **Consult** — Run each perspective. Find agreement (foundation) and conflict (real tradeoffs).

4. **Recommend** — Pick a path. State assumptions. Say what would change it.

---

## Expert Selection Algorithm

For any decision, choose:

1. **One builder lens** — the person who would have to implement it
2. **One risk lens** — the person who has seen it fail
3. **One outcome lens** — the person closest to user/business impact
4. **Optional fourth** — only if the decision has unusual stakes (security, legal, scale, compliance)

**Rules:**
- Never pick multiple experts with the same incentive
- Pick for the **decision**, not the topic. "Should we migrate to microservices?" needs a platform engineer AND someone who's lived through a failed migration — not two architecture experts who agree.
- 2 experts for simple tradeoffs. 3-4 for complex ones. Never more than 4.
- If you can't find genuinely different perspectives, the decision is probably obvious — just say so.

---

## Depth Selection

### Quick (default) — 30-90 seconds

Use when:
- 2-3 known options
- Reversible decision
- Low blast radius
- Needed inline during `/build`

```markdown
## Consult: [reframed decision]

**The real question:** [reframe if different from stated]

**[Expert A — lens]** — [their take in 2-3 sentences]
**[Expert B — lens]** — [their take in 2-3 sentences]

**They agree on:** [1-2 points]
**The real tradeoff:** [the one thing they disagree on and why it matters]

**Do this:** [recommended path]. [Why in 1 sentence].
**Verify:** [what to check before committing]
```

### Deep — 3-5 minutes

Use when:
- Architecture choice
- Migration path
- Build vs buy
- Irreversible scope/stack decision
- Meaningful time/money/security consequences

User can force either mode: `/consult --quick ...` or `/consult --deep ...`

```markdown
## Domain Panel: [reframed decision]

**The real question:** [reframe if different from stated]

### Experts Consulted
- [Expert A — builder lens]
- [Expert B — risk lens]
- [Expert C — outcome lens]

### Where they agree (foundation)
- [point 1]
- [point 2]

### Where they conflict (real tradeoffs)
| Question | Expert A says | Expert B says | Stakes |
|----------|--------------|--------------|--------|

### What they'd check first
- [Expert A]: "Before anything, I'd verify..."
- [Expert B]: "The thing most people skip is..."

### Red Flags
- [stop signs, hidden constraints, false assumptions]

### Recommendation
**Do this now:** [best next move]
**Because:** [2-4 bullets]
**Assumptions:** [what must be true for this to be right]
**Do not do this:** [tempting but wrong path, and why]
**Confidence:** [high/medium/low]
**Confidence drops if:** [specific condition that would change the recommendation]
**Verify before committing:**
- [check 1]
- [check 2]
```

---

## Routing

- If the problem is "what do users actually think?" → `/scout`
- If the problem is "I need evidence and sources" → `/research`
- If the problem is a tradeoff between known options → `/consult`
- If all experts would agree → just say so. Don't manufacture disagreement.
- If you catch yourself inventing data to support a perspective → stop. Route to `/scout` or `/research` for the evidence gap.

---

## `/build` Integration

`/build` calls `/consult --quick` only when there is a genuine tradeoff:
- Stack choice (when "Help me choose" is selected)
- Architecture choice during build
- Major scope cut (what to keep vs cut)
- Build vs buy (library vs custom)

Skip `/consult` when:
- The path is obvious
- The project is a straightforward V0
- The decision is already made
- The user said what they want

`/consult` does NOT replace `/build`'s Senior Frame for every build. Senior Frame is "what would an expert check first?" — a quick lens, not a full panel. Only escalate to `/consult` when the Senior Frame surfaces a disagreement.

---

## When NOT to Use

- "What is X?" → just answer it
- "Find docs for Y" → `/scout` or WebSearch
- "Summarize this" → just read and summarize
- "Is X true?" → `/scout` or `/research` (consult doesn't verify claims)
- Already-decided execution tasks → just build
- When you're stalling instead of building → just build

---

*Author: Shareef Ellis · [@shareefatwork](https://x.com/shareefatwork)*
