---
name: panel
description: "Pressure-test the bet before /build. Convenes 2 domain reviewers (read-only, clean-context) who scan for blind spots — what's stated, what's missing, what's assumed. Surfaces top concerns, you confirm, bet locks. Confirmation-bias prevention, not flaw-finding."
argument-hint: "[optional: path to idea.md — defaults to last project]"
---

# Panel

Convene 2 domain reviewers to scan the bet for blind spots. Forge first, then a scope-check tail. The point isn't to find every flaw — it's to make sure you've seen the perimeter before committing to /build.

Use this AFTER `/start-here` Step 4 (bet locked in idea.md), BEFORE `/build new` Stage 0.

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
- `## The bet` (the category claim from /start-here Step 4)
- `## Who it's for` (audience)
- `## The problem`

If any are missing or empty, halt with: *"Panel needs the bet, audience, and problem locked first. Run `/start-here` to fill them in."*

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

**Score each finding:**
- `severity_score`: high=3, med=2, low=1
- `confidence_score`: high=3, med=2, low=1
- `base_score = severity_score × confidence_score` (range 1-9)

**Cross-panel adjustments (the "+" in d+):**
- If 2+ reviewers raised related concerns (similar text, same evidence/gap/assumption target): bundle them as one merged finding, score = max + 1 (cross-panel bump).
- If 1 reviewer raised a concern but the OTHER reviewer's findings contradict it (e.g., A says "audience too narrow," B says "audience too broad"): tag as `contested`, score unchanged.
- If a concern's text is already addressed in idea.md (mechanical check — does the concern's keyword appear in idea.md outside `## The bet`?): downweight by 1.

**All-clean edge case:** if both reviewers returned 0 findings, skip Step 5. Log directly + verdict-prompt:

> "Panel returned no concerns. Bet looks clean from both lenses. Proceed?"

→ Single AskUserQuestion (verdict only — Step 6 shape).

**Otherwise, surface top 4** by score (AskUserQuestion options cap). Anything beyond top 4 stays in the `## Panel log` for the user to pull manually if curious.

**Tie-break order** (when scores are equal): severity > confidence > cross-panel-bumped > order in raw output. Ties are common; this keeps surfacing deterministic.

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

One AskUserQuestion call, multi-select. The labels are short concern names; descriptions show the failure type and the snippet.

```
AskUserQuestion(
  questions: [
    {
      question: "Which of these has panel surfaced that you've already considered?",
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
        {label: "Yes — proceed",   description: "Lock the bet, continue to /build new"},
        {label: "Revise",          description: "Update idea.md, /panel re-fires manually if you want"},
        {label: "Kill",            description: "Back to /start-here Step 4 to re-bet"}
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

### Scope diff
<diff if growth detected, or "No growth — bet unchanged.">

### Verdict
<proceed | revise | kill>

### Outcome
<!-- Filled later by /retro after V0 ships or kills. Tracks whether
     panel concerns proved real, false-positive, or unaddressed. -->
[blank]
```

The `### Outcome` block stays blank until `/retro` populates it post-V0. That closes the Karpathy loop — panel logs become training data for future calibration via `/improve`.

---

## Step 8: Hand off

**Verdict = proceed:**
> "Bet locks. Run `/build new <slug>` when you're ready."

**Verdict = revise:**
> "Update idea.md with the changes. Re-run `/panel` if you want a fresh pass — it doesn't auto-fire."

**Verdict = kill:**
> "Bet archived in panel log. Run `/start-here` again to re-bet from scratch — your scout findings and audience can carry forward."

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

## Future direction (V1+)

- **Auto-fire from /start-here Step 5.** Once /panel earns trust, promote from manual to automatic gate after bet capture.
- **Adaptive roster.** Replace fixed 7-function list with AI-invented roles per bet ("for THIS bet, who would the right reviewers be?").
- **/retro hook.** Wire `### Outcome` block to be filled by `/retro` after V0 ships — closes the Karpathy loop. /improve reads paired panel-log + retro-outcome data to recalibrate scoring weights.
- **Three-person panel as default.** If two-person panels miss too many real concerns at retro, bump default size.
- **Per-user severity calibration.** Track which "high-severity" concerns the user dismisses and which they take seriously. Surface this back as bias visibility.

---

*Author: Shareef Ellis · [@shareefatwork](https://x.com/shareefatwork)*
