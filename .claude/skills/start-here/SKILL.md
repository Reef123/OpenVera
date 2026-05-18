---
name: start-here
description: "Guided idea-fleshing for new users. From vague notion to buildable idea. Conversational, teaches Vera as you go."
argument-hint: "[optional: a rough idea or topic]"
---

# Start Here

Turn "I kinda want to build something" into a real idea. Then hand it to `/build new`.

---

## How this skill walks the design tree

`/start-here` is a **design-tree walk**, not a form. Each step resolves the decisions the next step's options depend on — the user moves down the tree, and each step's content is generated from what came above it. No question is asked before the answers it depends on are in. *(Same pattern + same vocabulary as `/build new` Stage 0 — by design.)*

```
Step 1   — Spark              (open-text, root of the tree)
   ↓
Step 1.5 — Scout gate         (signal-driven recommendation; runs scout EARLY if
   ↓                          the spark names a crowded category or specific tool)
Step 2   — Reframe + Audience (options GENERATED from Step 1's words; if scout
   ↓                          ran via the gate, framings shaped by scout findings)
Step 3   — Success picture    (question GENERATED from Step 1 + Step 2 audience;
   ↓                          scout fires in background here IF the gate didn't run it)
Step 4   — The Bet → Idea doc → Check
                              (bet options GENERATED from spark + scout findings)
                              (Open Questions walk: ordered by dependency)
   ↓
Step 5   — Hand off           (next-action options informed by full idea state)
```

Every option list is **generated from prior steps**, never hardcoded — if Step 2 framings don't reference Step 1's words, the walk is broken (the user is filling out a form, not building down a tree).

**Scout policy:** scout runs ONCE during `/start-here` — Step 1.5 gate fires it early (blocking) on crowded-space signals; otherwise it runs in Step 3 background. `## What's out there` is filled before Step 4 generates bet options either way.

---

## Step 1: The Spark

**If they passed an argument**, treat it as the Step 1 spark — skip the open-text question and the 1-2 follow-ups, but **still evaluate Step 1.5 (Scout gate) before continuing to Step 2.** A passed argument is just an inline answer to Step 1; the scout-gate signals fire the same way (crowded category, named platform, "alternative to X"). Don't skip the gate.

**If no argument**, one question. Keep it light. **Use the Question Block format** (see Question Block Format below) — first-time users need the question to visually pop out from conversational chatter so they know exactly when it's their turn to talk:

```
> **Your turn**
>
> **What's something you wish existed?**
>
> Could be an app, a tool, anything that makes
> something in your life easier. Doesn't have
> to be fully formed — just the spark.

*Just type your answer below ↓*
```

Let them talk. Listen for:
- The real problem (often sentence two or three)
- Who else has it (just them? their team? everyone?)
- What they do now instead (the manual workaround — this is the good stuff)

**1-2 follow-ups max.** Not an interview. Pick questions that match what they said. **Use the Question Block format for follow-ups too:**
- Workflow problem → "What do you do right now when that happens?"
- Creative idea → "What does the good version of this feel like?"
- Frustration → "How often does this bite you?"
- Vague spark → "Is this just you or does anyone else deal with this?"

---

## Step 1.5: Early Scout Gate (signal-driven, between Spark and Reframe)

After Step 1 finishes, evaluate the Spark text for signals that warrant running `/scout` **before** Step 2's reframings. If a strong existing tool already dominates the space, framings generated cold will miss it — Step 2 ends up offering reframings of a problem the user could solve by downloading something tonight.

**Signals (any one fires the gate):**
- Spark names a crowded category — "todo", "notes", "dashboard", "habit tracker", "journal", "kanban", "note-taking", "reading list", "bookmark manager"
- Spark names a specific external platform/API — "Notion", "Linear", "Slack", "GitHub", "Stripe", "Obsidian", "Roam", any named SaaS or API
- Spark framed as "alternative to <existing tool>" or "X but better" or "<tool> for <use case>"

**Gate logic:**
- No signals fire → skip the gate. Continue to Step 2. Scout still runs in Step 3 background as the default.
- ≥1 signal fires → fire the gate. Plain text, single yes/no recommendation:

```
🔍 Quick check before I shape this: <one-line reason — e.g., "todo apps are a crowded space — there might already be a tool that does what you described"</one-line>. Running `/scout` (~2-3 min, ~free) now would tell me what's out there so I can shape framings around the real gap, not generic angles.

   Run scout first? (recommended)
```

Use plain text + single yes/no, not `AskUserQuestion`. This is a recommendation with one clearly preferred answer.

- If user says **yes** → spawn `/scout` foreground (not background — Step 2 needs the result). When scout returns, summarize findings in 2-3 lines, then continue to Step 2 with framings shaped by what scout found. **Mark scout as already-run** so Step 3 skips re-running it (re-using cached findings) — Step 3 still asks the success-picture question, just doesn't re-fire scout.
- If user says **no** → continue to Step 2 with framings generated cold. Scout still runs in Step 3 background as the default. Don't re-recommend.

**If scout ran via this gate**, idea.md's `## What's out there` is filled at Step 2 partial-save time, not waiting for Step 3 to complete.

---

## Step 2: Reframe Their Problem (NOT a static menu)

**Do NOT use hardcoded categories.** Generate 3 different framings of THEIR specific problem. Each framing leads to a different product.

```
AskUserQuestion(
  questions: [
    {
      question: "Which angle feels right?",
      header: "Framing",
      options: [
        // GENERATE 3 different framings from Step 1's words. Each must lead to a different product.
        // Example — user said "I hate tracking my reading list across apps":
        //   "Unify everything into one view" / "Stop tracking — just save what matters" / "Make it automatic"
        {label: "[Framing A — their words]", description: "[what this product would feel like]"},
        {label: "[Framing B — different angle]", description: "[different approach to same pain]"},
        {label: "[Framing C — unexpected take]", description: "[reframe they might not have considered]"},
        {label: "None of these", description: "I'll tell you what I actually want"}
      ],
      multiSelect: false
    },
    {
      question: "Who's this for?",
      header: "Audience",
      options: [
        {label: "Just me", description: "Personal tool"},
        {label: "Me + someone", description: "Shared with a partner or colleague"},
        {label: "A group", description: "Team or community"},
        {label: "Anyone with this problem", description: "Public"}
      ],
      multiSelect: false
    }
  ]
)
```

**Rules for generating framings:**
- **Extract first, then frame.** Before writing any options, list the 2-3 concrete nouns/verbs the user said they want (e.g., "wireframes", "up-to-date info", "guided walkthrough"). Call this the must-preserve list.
- **At least one framing must preserve ALL must-preserve items.** The other 2 can fragment, simplify, or reframe — but one angle has to bundle everything they asked for. Otherwise the user has no choice but to type their own answer.
- Use their words, not yours. If they said "hate," use "hate."
- Each framing should lead to a genuinely different product, not variations of the same thing.
- Framing C should be the unexpected one — reframe the problem itself, not just the solution.
- "None of these" should be rare. If users consistently pick it, the framings are failing to capture their vision.

**Signal logging (reserved):** If the user picks "None of these" and types their own angle, append one line to `vera-system/runs/start-here-corrections.jsonl` (gitignored runtime path — never tracked):

```json
{"date": "YYYY-MM-DD", "user_input": "<what they said in Step 1>", "offered": ["A", "B", "C"], "chose": "<what they typed>"}
```

This is captured as a corpus of misses for future use by `/improve /start-here`. The improve loop does not read this file yet — the data is being collected so it's available when that wiring lands. Safe to skip if the file isn't writable.

Synthesize into one sentence. Say it back:

> "So basically: [problem in their words]. Yeah?"

If they correct, update. If they nod, move on.

**Partial save now.** Don't wait for the full idea doc — Vera's promise is *"you didn't finish, but the thread remembers."* Scaffold immediately so a user who bails after Step 2 still finds their work tomorrow:

1. Generate kebab-case slug from the synthesized problem statement (e.g., `track-reading-list`).
2. Use the synthesized problem statement as the tentative idea name — Step 4 may refine it.
3. `mkdir -p {paths.projects_dir}/<slug>/`
4. Write `{paths.projects_dir}/<slug>/CLAUDE.md` with this frontmatter:
   ```markdown
   ---
   name: <tentative idea name>
   slug: <slug>
   status: exploring
   created: <YYYY-MM-DD>
   updated: <YYYY-MM-DD>
   stack: null
   run: null
   score: null
   origin: /start-here
   ---
   # <tentative idea name>
   <one line — what this does>
   ```
5. Write `{paths.projects_dir}/<slug>/idea.md` — fill three sections immediately, leave the rest as `[pending]`:
   - `## Original spark` — **verbatim** Step 1 input. The literal first thing they typed (or the argument they passed to `/start-here`). Don't edit it. Don't summarize it. This is the source-of-truth audit trail for V0→V1 drift checks.
   - `## The problem` — synthesized statement from Step 2.
   - `## Who it's for` — audience answer from Step 2.

Update this same file at the end of each subsequent step — but **never overwrite `## Original spark`**. That section is append-only history, written once in Step 2 and preserved through Step 4. Step 5 just routes — the file already exists.

---

## Step 3: Reality Check + Success Picture

**If scout already ran via the Step 1.5 gate**, skip the spawn below — `## What's out there` is already filled. Go straight to the success-picture question. Don't re-fire scout, don't tell the user "running scout" again.

**Otherwise**, run scout in background — grounds the idea, prevents building something that already exists:

```
Agent(
  description: "scout for idea",
  prompt: "Run /scout on: '[problem statement]'. What exists, what people like/hate about it, what's missing. 2 minutes max.",
  run_in_background: true
)
```

**If scout is unavailable** (no OpenRouter key, scout errors out, network fails), fall back to Claude Code's built-in `WebSearch` tool — no API keys required. Run 2-3 searches on the problem (e.g., `"[problem] tool"`, `"[problem] reddit"`, `"[problem] alternatives"`) and synthesize the results into `## What's out there`. Tell the user once, plain: *"Scout's unavailable — using WebSearch instead. Lighter signal, still real."*

Only if WebSearch ALSO fails (rare — offline or rate-limited) do you punt to: `## What's out there: Not checked yet` + 2-3 assumptions to verify during build. Public users without keys must finish `/start-here` end-to-end.

**While scout runs**, ask. **Generate this question from Step 1 + Step 2** — don't ship the generic template. Anchor it in *their* audience, *their* problem, *their* friction. The user's reply is the success picture you'll quote verbatim into idea.md `## What good looks like` (Step 4) — vague question → vague quote → vague spec. Use the Question Block format:

```
> **Your turn**
>
> **{Picture-anchor — name the audience + the specific moment the
> problem from Step 2 currently happens.}**
>
> {Friction-probe — name one friction they already mentioned and ask
> what it feels like in the new world.}

*Just type your answer below ↓*
```

**Generation rules:**
- **Picture-anchor must reference the audience + moment**, not "what's different about your day." Example for pretty-todo-cards (audience: solo builder; problem: my todo list looks like a spreadsheet): *"It's Tuesday morning. You open the app and see your list — what do you see instead of the spreadsheet?"*
- **Friction-probe must name a friction they actually said** in Step 2. Example: *"You said adding a task feels like data entry. What does it feel like now?"*
- **Two clauses max.** No "what does adding feel like? what does opening feel like? what about the home screen?" — that's a survey, not a question.
- If their Step 2 was thin (one-liner answer), say so plainly: *"You haven't named a specific friction yet — paint the picture in your own words and I'll work from that."* Don't fabricate friction to probe.
- **Quote the audience by name** if Step 2 named one. *"Picture {Sara, your designer friend}..."* beats *"Picture the user..."*.

**Bad (current generic):** *"If this worked perfectly — what's different about your day?"* — applies to every product ever built.
**Good (anchored):** *"Sunday night, you sit down to plan the week. Your list opens — what do you see? You said the current spreadsheet view kills the mood — what carries the mood now?"*

**Breadcrumb after scout returns:**
> "That was `/scout` by the way — it checks Reddit, YouTube, and the web for real opinions. You can run it anytime: `/scout <any question>`."

---

## Step 4: Crystallize

You now have: the spark, the narrowed problem, community signal, and their success picture.

**First — capture the bet.** Before writing the idea doc, ask one AskUserQuestion that elicits the *category claim* — what changed that lets this exist now. Without this, V0 builds the literal spec but misses the move that makes it interesting.

Generate 3 bets from the spark + scout + success picture. Each bet must be a **category claim** (not a feature) with a **"Why now"** descriptor (what couldn't be built before that can now). The 4th option is the escape hatch:

```
AskUserQuestion(
  questions: [
    {
      question: "What's the bet — what changed that lets this exist now?",
      header: "The Bet",
      options: [
        // GENERATE 3 from spark + scout findings. Labels = 3-6 word noun phrases.
        // Descriptions = "Why now: <one line>" (forces articulation of real-time leverage).
        // Example bets must span DIFFERENT category types (not 3 aesthetic, not 3 speed) — for pretty-todo-cards:
        //   • "Taste — AI makes the aesthetic call" / "Why now: models can be trusted with taste in 2026."
        //   • "Speed — skip the manual styling work" / "Why now: streaming makes per-item generation viable in <1s."
        //   • "Texture — visual variety carries emotional weight" / "Why now: per-item generative UI shipped (streamUI, Tambo)."
        {label: "[Bet A — short noun phrase]", description: "Why now: <one line>"},
        {label: "[Bet B — different angle]", description: "Why now: <one line>"},
        {label: "[Bet C — different again]", description: "Why now: <one line>"},
        {label: "Different bet — let me say it", description: ""}
      ]
    }
  ]
)
```

**Rules for generating bets:**
- Labels must be **category claims**, not features. "AI styles tasks" ✗ → "AI has taste on your behalf" ✓.
- Descriptions must answer "what changed?" — "Why now: <one line>". If the bet has no real "why now," the bet is fake; the user reroutes to "Different bet."
- All 3 must map to genuinely different categories. Variants of the same idea waste an option.
- Don't pick a bet that scout findings directly contradict ("AI todo styling is unique" — but scout found Tiimo doing it). Acknowledge the scout finding when generating.
- "Different bet" should be rare. If users keep picking it, the generation rules need fixing.

The picked bet (or typed answer) becomes `## The bet` in idea.md. `/build new` Stage 0 reads it. Stage 2 build decisions check against it: *"does this scaffold reach for the bet, or just the literal job?"*

---

Now write the idea doc using **their words**, not yours. If they said "I hate hunting for invoices," write that — not "invoice retrieval optimization."

**Update the idea.md from Step 2's partial save** — overwrite the body with the full template below, but **preserve `## Original spark` exactly as Step 2 wrote it.** Read the existing file first, splice the spark section back in unchanged. If the user gave a much better idea name during this step, update the `name:` field in `CLAUDE.md` and the `# [Idea Name]` heading too (slug + dir rename happens in Step 5):

```markdown
# [Idea Name]

## Original spark
<!-- Verbatim Step 1 input. Do not edit. -->
> [the literal first thing the user typed, unchanged]

## The bet
<!-- The category claim. Why this exists now. Anchors V0 build decisions. -->
**[Bet label they picked, or their typed bet]**

Why now: [the leverage that makes this possible — model capability, primitive that shipped, etc.]

## The problem
[1-2 sentences in their language.]

## Who it's for
[Audience, plain.]

## What's out there
[Scout summary. What exists, what's missing.]

## What this would do
[The angle — why build when X exists? Should reach for ## The bet, not just restate ## The problem.]

## What good looks like
[Their words from the success picture. Include a verbatim quote of their Step 3 answer at the top of this section, formatted as a blockquote (`> "..."`); the rest of the section can be Vera's framing of that quote.]

## What this is NOT
[Scope they explicitly DON'T want, in their words. 1-2 lines. Omit the section entirely if nothing surfaced — better empty than invented.]

## Open questions
[2-3 unknowns to figure out during build.]
```

The verbatim-preservation rules — `## Original spark` and the Step 3 quote at the top of `## What good looks like` — are the V0→V1 audit trail. Combined with `## The bet`, they let `/build full` later check whether what shipped matches what the user actually asked for *and* reaches for the category claim. Never paraphrase those.

**When presenting back in chat**, use markdown headings (`## [Idea Name]` + `### Section`) so it reads as a document, not a reply. Same hierarchy for every section.

Present it, then:

```
AskUserQuestion(
  questions: [
    {
      question: "How's this looking?",
      header: "Check",
      options: [
        {label: "Answer the open questions", description: "I have thoughts on these before we move on"},
        {label: "Yes, this is it", description: "Move on to the next step"},
        {label: "Close, but...", description: "I'll tell you what to tweak"},
        {label: "Nope, start over", description: "Not it — back to brainstorming"}
      ],
      multiSelect: false
    }
  ]
)
```

"Close, but..." → adjust, present once more, then move forward regardless.

"Answer the open questions" → Walk through each open question one at a time, **ordered by dependency** — if B's answer depends on A's, ask A first. Use AskUserQuestion with generated options per question (like Step 2 framings — not generic, specific to the question). **Mark one option as `(Recommended)` with a one-line rationale** so the user confirms or overrides instead of choosing cold. Update the idea doc with their answers. Then continue to handoff.

**Breadcrumb:**
> "Saved to your project folder. Closing here is fine — the thread will be here when you come back."

---

## Step 5: Hand Off

The dir, `CLAUDE.md`, and `idea.md` already exist from Step 2's partial save and have been updated through Step 4. Now finalize:

1. **If the idea name shifted in Step 4**, regenerate the slug from the new name and `mv` the project dir to match. Update the `slug:` field in `CLAUDE.md` frontmatter accordingly.
2. Bump `updated:` in `CLAUDE.md` frontmatter to today's date. Leave `status: exploring` — the routing question below decides whether it stays or flips.
3. Append a one-line summary to `vera-system/ideas.md`.

Then:

```
AskUserQuestion(
  questions: [
    {
      question: "What next?",
      header: "Next",
      options: [
        {label: "Build it (Recommended)", description: "/build new turns this into a working app — one session"},
        {label: "Pressure-test the bet", description: "/panel scans for blind spots before /build (~3 min)"},
        {label: "Dig deeper first", description: "/research goes wide on the topic (~15 min)"},
        {label: "Save for later", description: "Idea's saved — come back whenever"}
      ],
      multiSelect: false
    }
  ]
)
```

**Build it** → Run `/build new <slug>` using the slug you generated above. The project dir already exists with idea.md — /build will detect it and skip re-scaffolding. The Step 3 reality check carries forward as build context.

**Breadcrumb before build starts:**
> "/build new will ask about the job, the pain, stack, and how to validate — then it builds autonomously."

**Pressure-test the bet** → Run `/panel <slug>`. Two domain reviewers (clean-context Explore subagents) scan idea.md for blind spots — what's stated, missing, or assumed. Surfaces top concerns, you confirm what you've already considered, bet locks. Confirmation-bias check before /build.

**Dig deeper** → Run `/research [topic]`.

**Save for later** → Done. Tell them:
> "Saved. When you're ready: `/build new <slug>`."

---

## Rules

- **Their words, not yours.** No jargon. No "requirements." No "stakeholders."
- **One problem.** If they name three, help them pick the one with energy. Others go in open questions.
- **Scout the idea, one way or another.** Real signal > building in a vacuum. Try `/scout` first; fall back to `WebSearch` if no keys; document assumptions only if both fail. Never dead-stop on a missing key.
- **Two refinement rounds max.** Ship the idea, not the perfect idea.
- **Breadcrumbs, not lectures.** One line after each step showing what Vera can do. That's it.
- **Voice — see `vera-system/who-i-am/voice.md` "Onboarding & user-facing surfaces."** 5% warmth ceiling. No exclamation, no celebration words, no anthropomorphizing. The signature is in considered specifics — framings of their words, anchored questions, real scout signal — not in warmth.
- **Question Block format for every open-text question.** First-timers can't easily distinguish "Claude is asking me something" from "Claude is talking." The bordered block resolves it visually. AskUserQuestion has its own UI — don't double-wrap.

---

## Question Block Format

For open-text questions (not `AskUserQuestion` — that has Claude Code's built-in UI). First-time users need it visually clear when they're being asked vs. when Vera is just talking. Use a markdown blockquote with three elements:

| Element | Style | Purpose |
|---------|-------|---------|
| `**Your turn**` header | Bold inside blockquote | Frames the moment as an interaction |
| Question text | Bold | The ask, visually pops |
| Affordance hint below | Italic | Tells first-timers where to type |

Pattern:

```
> **Your turn**
>
> **<Question — bold, max ~50 chars/line>**
>
> <Optional context — plain text, why you're asking,
> what kind of answer you're looking for>

*Just type your answer below ↓*
```

(ANSI escape codes render as literal text in Claude Code chat — markdown only. See `vera-system/CLAUDE.md` "Output Formatting".)

---

*Author: Shareef Ellis · [@shareefatwork](https://x.com/shareefatwork)*
