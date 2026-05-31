---
name: panel
description: "Pressure-test the bet before /build. Convenes 2 domain reviewers (read-only, clean-context) who scan for blind spots — what's stated, what's missing, what's assumed. Surfaces top concerns, you confirm, bet locks. Confirmation-bias prevention, not flaw-finding."
argument-hint: "[optional: path to idea.md — defaults to last project]"
---

# Panel

Convene 2 domain reviewers to scan the bet for blind spots. Forge first, then a scope-check tail.

Use this AFTER `/start-vague` Step 4 (bet locked in idea.md), BEFORE `/build new` Stage 0.

---

## When to use

- The bet feels right, but maybe too right — overconfidence smell.
- Audience claim is broad ("solo builders", "anyone with X").
- Category claim is novel — you want a reality check before betting V0 hours on it.
- You re-read idea.md and can't tell if it's solid or you've just stopped seeing it.

Skip if: you're in pure /scout / exploration mode, or the bet is genuinely throwaway-tiny.

---

## Step 1: Locate idea.md

If `$ARGUMENTS` is a path, use it. Otherwise find the most recently updated `idea.md` under `{paths.projects_dir}/<slug>/idea.md`.

Read the file. Required sections for /panel to run:
- `## The bet` (the category claim from /start-vague Step 4)
- `## Who it's for` (audience)
- `## The problem`

If any are missing or empty, halt with: *"Panel needs the bet, audience, and problem locked first. Run `/start-vague` to fill them in."*

---

## Step 2: Pick the panel

The roster (fixed list, V0):

| Function | Lens |
|---|---|
| **user-experience reviewer** | How users encounter and react to the product surface |
| **ideal-customer-profile reviewer** | Who the audience actually is, what they pay for, what alternatives exist |
| **product-strategy reviewer** | Whether the bet is a real category claim or a feature dressed up |
| **technical-feasibility reviewer** | What's hard / impossible / hidden-cost in shipping the bet |
| **monetization reviewer** | Willingness-to-pay, pricing, value capture |
| **competitive-landscape reviewer** | Who's already doing this, what's the delta |
| **distribution reviewer** | How the audience hears about and adopts this |

Read the bet + audience + problem. Propose 2 reviewers most relevant to *this* bet. Bias: pick reviewers whose lens the idea.md content seems thinnest on, not reviewers whose lens you most agree with.

```
AskUserQuestion(
  questions: [
    {
      question: "Recommended panel for this bet:",
      header: "Panel",
      options: [
        // Generate from roster + bet content. Vera's pick goes first with (Recommended).
        // Example for a taste-driven todo bet:
        //   {label: "UX + ICP (Recommended)",        description: "[function-A] + [function-B] — [one-line why]"},
        //   {label: "Pick different two",            description: "Show me the full roster"},
        //   {label: "Add a third reviewer",          description: "Three-person panel — costs more, more thorough"},
        //   {label: "Just one reviewer",             description: "Lighter pass — single domain only"}
        {label: "[A] + [B] (Recommended)",   description: "[one-line why these two for this bet]"},
        {label: "Pick different two",        description: "Show me the full roster"},
        {label: "Add a third reviewer",      description: "Three-person panel — more thorough, more cost"},
        {label: "Just one reviewer",         description: "Lighter pass — single domain only"}
      ],
      multiSelect: false
    }
  ]
)
```

If user picks "different" or "third," follow up with a multi-select AskUserQuestion offering the full roster (split across calls if >4).

Lock the panel. Tell the user briefly: *"Panel: [function-A] + [function-B]. Reading the bet now — back in ~30s."*

---

## Step 3: Spawn the panel (parallel, clean-context)

Each reviewer is an Explore subagent (read-only). They get a role, a file path, and an open task. **No framing, no pre-summary, no leading questions** — that's bias we'd have to subtract later.

Spawn both in parallel — single message, two Agent tool calls.

For each reviewer:

```
Agent(
  description: "[function] panel reviewer",
  subagent_type: "Explore",
  prompt: """
You are a {function} reviewer with 10+ years of senior experience.

Read: {abs_path_to_idea_md}

Task: What might the author of this idea NOT be seeing from your
domain perspective? Surface concerns — what's wrong, what's missing,
or what's assumed.

Output: YAML list only. Each item must include exactly ONE of:
evidence (quote from idea.md), gap (what's missing), or assumption
(hidden assumption).

```yaml
- concern: "[one sentence]"
  severity: high | med | low
  confidence: high | med | low
  evidence: "[quote from idea.md]"
  # OR
  gap: "[what's missing]"
  # OR
  assumption: "[hidden assumption]"
```

List as many or as few findings as you actually have. Do not pad.
No preamble, no summary, no prose outside the YAML block.
"""
)
```

Wait for both to return.

---

## Step 4: Synthesize (d+)

Parse each reviewer's YAML output. Build the merged finding set:

**Tag each finding** — this is the judgment part:
- `severity` and `confidence`: each `high` / `med` / `low`.
- `cross_panel: true` if 2+ reviewers raised related concerns (similar text, same evidence/gap/assumption target) — bundle them into one finding first.
- `contested: true` if one reviewer's concern is contradicted by the other (e.g., A "audience too narrow," B "too broad").
- `addressed: true` if the concern's keyword already appears in idea.md outside `## The bet`.

**Then score deterministically** — pipe the tagged findings (a JSON array) to the scorer, which does the arithmetic, sort, and tie-break so surfacing is reproducible:
```bash
echo '<findings JSON array>' | python3 vera-system/scripts/panel-score.py --top 4
```
It returns `{"top": [...], "rest": [...]}`. Scoring: `severity × confidence` (high=3 / med=2 / low=1), `+1` for `cross_panel`, `-1` for `addressed`, `contested` unchanged; tie-break severity > confidence > cross-panel-bumped > raw order.

**All-clean edge case:** if both reviewers returned 0 findings, skip the scorer and Step 5. Log directly + verdict-prompt:

> "Panel returned no concerns. Bet looks clean from both lenses. Proceed?"

→ Single AskUserQuestion (verdict only — Step 6 shape).

**Surface the `top`** (4 findings, the AskUserQuestion options cap). The `rest` stays in the `## Panel log` for the user to pull manually if curious.

Show the work briefly in chat (not just options). One line per surfaced finding — drop the confidence chip from the chat surface to reduce density (it's still in the panel log):

> Panel surfaced 8 concerns. Top 4 by relevance:
>
> 1. **[concern]** — [evidence|gap|assumption] · sev:high
> 2. **[concern]** — [evidence|gap|assumption] · sev:high
> 3. **[concern]** — [evidence|gap|assumption] · sev:med · *cross-panel*
> 4. **[concern]** — [evidence|gap|assumption] · sev:med · *contested*
>
> 4 more in panel log.

---

## Step 5: Triage with the user

**First, print the purpose banner** — one line, so the user knows *why* this step exists. A bare checklist with no framing reads as confusing (real user feedback). Print it in chat right before the question:

> 🐘 **Why this step:** I pulled in fresh eyes to spot what you might be too close to see. Check the ones you'd already thought about — the rest are the catches, and we'll look at each before any code.

Then one AskUserQuestion call, multi-select. The labels are short concern names; descriptions show the failure type and the snippet.

```
AskUserQuestion(
  questions: [
    {
      question: "Check the ones you'd already thought about (the unchecked ones are the panel's catches).",
      header: "Considered?",
      options: [
        {label: "[concern 1 short]",  description: "[evidence|gap|assumption]: [snippet]"},
        {label: "[concern 2 short]",  description: "[evidence|gap|assumption]: [snippet]"},
        {label: "[concern 3 short]",  description: "[evidence|gap|assumption]: [snippet]"},
        {label: "[concern 4 short]",  description: "[evidence|gap|assumption]: [snippet]"}
      ],
      multiSelect: true
    }
  ]
)
```

Read the user's selections. For unchecked items, follow up with a single plain-text turn:

> You didn't mark **[concern X]** and **[concern Y]**. Anything to say about them, or pass to log them as open?

User responds in prose. Capture verbatim — the response goes into the panel log.

---

## Step 6: Scope-check + verdict

**Scope-diff (mechanical):**

Compare idea.md content before /panel ran vs. after the user's free-text response in Step 5. If the user's response would add new constraints, success criteria, or scope items to idea.md, render the diff:

> **Scope diff:**
> Before: [bet length / scope sentence]
> After:  [bet length / scope sentence with growth]
>
> Heads up: this added [N] new constraints. Sanity check —

If no growth detected, skip the diff and go straight to verdict.

**Verdict:**

```
AskUserQuestion(
  questions: [
    {
      question: "Bet still V0-tight after this pass?",
      header: "Verdict",
      options: [
        {label: "Yes — proceed",        description: "Lock the bet, continue to /build new"},
        {label: "Deeper understanding", description: "Sharpen the plan before building. I ask one question at a time, biggest decisions first, each with my recommended answer, until we both see the plan the same way. (Runs the Step 6b interview.)"},
        {label: "Kill",                 description: "Back to /start-vague Step 4 to re-bet"}
      ],
      multiSelect: false
    }
  ]
)
```

**Proceed** → write the log (Step 7), done. **Deeper understanding** → run Step 6b, then re-show this verdict. **Kill** → log + back to /start-vague Step 4.

---

## Step 6b: Deeper understanding (the interview)

*Picked only when the user chooses "Deeper understanding" at the verdict. Adapted from Matt Pocock's `grill-me` skill (see THANKS.md) — sequential, dependency-aware questioning until shared understanding.*

Goal: turn the panel's open catches into resolved decisions **before** any code, so the build runs on decisions instead of guesses. By the end, the plan and the user's head hold the same picture.

**The method:**

1. **Explore before asking.** For each thing you'd ask, first check `idea.md`, the `## Panel log`, `spec.md`, and any `/frame` artifacts. If the answer is already there, use it — don't make the user re-state what's on the page. (grill-me's core efficiency rule. Also Vera's "do the work, don't ask busywork.")
2. **Walk the tree, biggest decisions first.** Resolve a parent decision before the children that depend on it, so you never settle a detail a larger call would erase. **Seed from the panel's `Unconsidered + open` items** (the known holes, e.g. "clustering underspecified") — those go first.
3. **One question at a time.** Each is its own `AskUserQuestion` turn (open-ended ones may be plain text). Do NOT batch — the point is to let each answer reshape the next question.
4. **Every question carries your recommended answer.** First option, labeled `(Recommended)`, plus a one-line *why*. Open-ended ones still lead with your pick. The user confirms or overrides.
5. **Push back once, on the biggest call.** After the load-bearing decision is locked, give the single strongest case against it, then ask: *"Strongest case against that: [X]. Keep it, or rethink?"* Log whichever way they go. One adversarial beat only — not every question. It sharpens the plan without nagging. (This is the counterfactual / attachment probe: what if the opposite is true, and are you over-invested past the evidence.)
6. **~6 questions, capped.** Target six; stop early once decisions are resolved and you both share the picture, or at six to keep it bounded. Don't pad to hit the number.
7. **Write it down.** Fold the resolved decisions into `idea.md` (`## The bet` / scope / `## What good looks like` / open questions). Show a short before/after diff. Then re-show the Step 6 verdict — usually a clean "proceed" now.

Per-question shape:

```
AskUserQuestion(
  questions: [
    {
      question: "<the decision, in plain words>",
      header: "<2-3 word topic>",
      options: [
        {label: "<my pick> (Recommended)", description: "<why this — one line>"},
        {label: "<alternative>",           description: "<when this is right instead>"},
        {label: "<alternative>",           description: "<...>"}
      ],
      multiSelect: false
    }
  ]
)
```

---

## Step 7: Write the panel log

Append to idea.md (don't overwrite earlier content):

```markdown
## Panel log — <YYYY-MM-DD>

**Bet at panel time:** <verbatim copy of `## The bet` content>
**Panel:** <function-A> + <function-B>

### Findings (raw)
\`\`\`yaml
- panelist: <function-A>
  concern: "..."
  severity: high
  confidence: high
  evidence: "..."   # or gap, or assumption

- panelist: <function-B>
  concern: "..."
  severity: med
  confidence: high
  gap: "..."

# ... ALL findings, both panelists, including ones cut from surfacing
\`\`\`

### Vera synthesis (d+)
- Surfaced top 4 by score: <list>
- Cross-panel notes:
  - <e.g., "AI-taste assumption + willingness-to-pay both surface trust-in-AI angle → bundled">
  - <e.g., "Delta vs existing single-source but high-severity → flagged">
- Contested: <list, or "none">
- Cut from surfacing: <list, or "none">

### User triage
- **Considered:** <items checked>
- **Unconsidered + addressed:** <items + verbatim user response>
- **Unconsidered + open:** <items left unaddressed>

### Deeper-understanding interview
<!-- Only if the user picked "Deeper understanding" at the verdict. One line per question: decision → resolution (recommended-and-accepted | overridden to X). "Not run" otherwise. -->
<resolved decisions, or "Not run">

### Scope diff
<diff if growth detected, or "No growth — bet unchanged.">

### Verdict
<proceed | deeper understanding | kill>

### Outcome
<!-- Filled later by /retro after V0 ships or kills. Tracks whether
     panel concerns proved real, false-positive, or unaddressed. -->
[blank]
```

The `### Outcome` block stays blank until `/retro` populates it post-V0.

---

## Step 8: Hand off

**Verdict = proceed:**
> "Bet locks. Run `/build new <slug>` when you're ready."

**Verdict = revise:**
> "Update idea.md with the changes. Re-run `/panel` if you want a fresh pass — it doesn't auto-fire."

**Verdict = kill:**
> "Bet archived in panel log. Run `/start-vague` again to re-bet from scratch — your scout findings and audience can carry forward."

---

## Rules

- **Subagents read, they don't get briefed.** Role + path + open task. No summary, no framing, no leading questions. Framing is the bias vector.
- **Confirmation-bias prevention, not flaw-finding.** The point is the 180° scan — make sure the user has seen the perimeter, not that every flaw is fixed.
- **Schema enforces lens.** No "don't validate" instruction. The YAML output schema has no slot for praise; that's the structural enforcement.
- **Vera proposes, user holds veto.** On panel pick. On surfaced concerns (override available). On verdict.
- **Top 4 is the cap.** AskUserQuestion limit. The 5th+ concerns live in the panel log; user can pull them manually if curious.
- **Scope-diff before verdict.** If the user's response added scope, show the diff. Pure transparency, no judgment — user decides whether the growth is real or bloat.
- **No auto re-fire.** Revising the bet doesn't auto-trigger another panel pass. User runs `/panel` again manually if they want another scan.
- **The log is the training data.** Every finding (surfaced or cut), every triage decision, every verdict goes into `## Panel log`. Future `/improve` calibrates against retro outcomes.

---

*Author: Shareef Ellis · [@shareefatwork](https://x.com/shareefatwork)*
