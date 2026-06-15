---
name: start-vague
description: "Front door for vague ideas. Bounded interview (max 4 rounds) that shapes an itch into a buildable idea.md, with mid-fire scout to catch 'already exists' before /research spends real money."
argument-hint: "[optional: a rough idea or topic]"
---

# Start Vague

Turn "I kinda want to build something" into a real idea. Then hand it to `/build new`.

**Vague is welcome.** Some ideas are itches before they're nouns. The interview shapes the itch — you don't need to arrive with the answer. Hard cap: 4 rounds. If shape hasn't landed by round 4, the escape hatch fires (re-pitch, keep going, or park).

---

## How this skill walks the design tree

`/start-vague` is a **design-tree walk**, not a form. Each step resolves the decisions the next step's options depend on — the user moves down the tree, and each step's content is generated from what came above it. No question is asked before the answers it depends on are in. *(Same pattern + same vocabulary as `/build new` Stage 0 — by design.)*

```
Step 1   — Spark               (open-text, root of the tree)
   ↓
Step 1.5 — Scout gate          (signal-driven; runs scout EARLY on crowded-category /
   ↓                            named-platform / "alternative to X" signals)
Step 2   — Reframe + Audience  (3-question batch: Framing + Audience + Scope —
   ↓                            framings GENERATED from Step 1's words; partial save
   ↓                            scaffolds idea.md so a bail here doesn't lose work)
Step 3   — Success picture     (question GENERATED from Step 1 + Step 2 audience;
   ↓                            scout fires in background here IF the gate didn't run it)
Step 3.5 — Show back            (3.5a: soft-redirect inline if scout found a strong match;
   ↓                             3.5b: ASCII wireframe — "is THIS what you mean?" — one
   ↓                             retry; skip 3.5b for clearly-non-visual ideas)
Step 3.6 — Widen check          (anti-tunnel: surface 2-3 distinct angles, recommend the
   ↓                             core, multi-select to capture scope, push back if >2)
Step 4   — The Bet → Idea doc → Check
                               (bet options GENERATED from spark + scout findings)
                               (Open Questions walk: ordered by dependency)
                               (Round-4 escape hatch fires on 2nd "Close, but..." OR
   ↓                            any "Nope": re-pitch / keep going past cap / park)
Step 5   — Hand off            (next-action options informed by full idea state)
```

Every option list is **generated from prior steps**, never hardcoded — if Step 2 framings don't reference Step 1's words, the walk is broken (the user is filling out a form, not building down a tree).

**Scout policy:** scout runs ONCE during `/start-vague` — Step 1.5 gate fires it early (blocking) on crowded-space signals; otherwise it runs in Step 3 background. `## What's out there` is filled before Step 4 generates bet options either way.

**Round structure:** Each step IS a round. WITHIN a round, questions are siblings (batchable in one `AskUserQuestion` call — Q2's options don't depend on Q1's answer). BETWEEN rounds, the next round's options are GENERATED from prior answers (the design-tree principle). Aim for 3 questions per `AskUserQuestion` batch where the surface supports it. **Hard cap: 4 rounds of new-content questions** (Steps 1, 2, 3, 4). Step 3.6 (Widen check) is a scope-confirm, not new exploratory content, so it doesn't count against the cap. If shape hasn't landed at Step 4, the round-4 escape hatch in Step 4 fires — re-pitch in your own words, keep going past the cap, or park to `vera-system/ideas.md`. Model judges round transitions, not a turn-counter.

---

## Step 0: Orientation (print first, then fire Step 1)

First-time users can't tell if this is a form, an interview, or a free-text chat. Print this before anything else so they know the shape of what's coming:

```
**🐘 Quick orientation:** this is a short interview — 4 rounds max. You answer
loosely, I do the shaping, and at the end you get an idea.md that /build new
can run with. Bail anytime; whatever we've shaped is saved.
```

**Skip the orientation when:** the user arrived here from a `/build new` redirect or another skill's hand-off (already oriented), or they've clearly run /start-vague before (idea docs exist in the projects dir).

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

**Run the signal scan** (the keyword list lives in one place — `gate-scan.py` — so `/start-vague` and `/build` fire on exactly the same spaces; they used to drift):

```bash
python3 vera-system/scripts/gate-scan.py scout "<Spark text>"
# prints FIRE lines (crowded_category / named_platform / alternative_pattern) then RESULT=FIRE|PASS
```

**Gate logic:**
- `RESULT=PASS` and no judgment override (the Spark names a SaaS/API the list doesn't enumerate) → skip the gate. Continue to Step 2. Scout still runs in Step 3 background as the default.
- `RESULT=FIRE` (or your override) → fire the gate. Plain text, single yes/no recommendation:

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

**Print this 🐘 tip in chat before firing the AskUserQuestion:**

> 🐘 *Same problem, three different apps we could build. What you pick here changes what gets made.*

Then:

```
AskUserQuestion(
  questions: [
    {
      question: "Which angle feels right?",
      header: "Framing",
      options: [
        // Frame variation — same problem, different mental models. Each framing leads to a different product.
        // GENERATE 3 framings from Step 1's words.
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
        // Perspective variation — same question, different POV scales.
        {label: "Just me", description: "Personal tool"},
        {label: "Me + someone", description: "Shared with a partner or colleague"},
        {label: "A group", description: "Team or community"},
        {label: "Anyone with this problem", description: "Public"}
      ],
      multiSelect: false
    },
    {
      question: "How big is this in your head?",
      header: "Scope",
      options: [
        // Scope variation — same question, different sizes. Surfaces scope-creep early.
        {label: "A weekend script", description: "One file, no UI. Solve the one thing."},
        {label: "A small app I'd use", description: "A few screens, one stack, runs locally or on Vercel."},
        {label: "A real product", description: "Multi-user, auth, payments-eventually, the works."},
        {label: "Not sure yet", description: "Help me figure out the right size."}
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

Synthesize into one sentence. Say it back:

> "So basically: [problem in their words]. Yeah?"

If they correct, update. If they nod, move on.

**Partial save now.** Don't wait for the full idea doc — Vera's promise is *"you didn't finish, but the thread remembers."* Scaffold immediately so a user who bails after Step 2 still finds their work tomorrow:

1. Generate the slug + create the project dir and `CLAUDE.md` in one pair of calls. The tentative idea name is the synthesized problem statement (Step 4 may refine it):
   ```bash
   SLUG=$(python3 vera-system/scripts/frontmatter.py slug "<synthesized problem statement>")
   python3 vera-system/scripts/frontmatter.py create --slug "$SLUG" --name "<tentative idea name>" \
     --status exploring --origin "/start-vague" --summary "<one line, what this does>"
   ```
   The script makes the dir, writes `created`/`updated`, leaves `stack`/`run`/`score` as `null`, and adds the lifecycle comment.
2. Write `{paths.projects_dir}/<slug>/idea.md` — fill four sections immediately (five if the Step 1.5 gate fired scout), leave the rest as `[pending]`:
   - `## Original spark` — **verbatim** Step 1 input. The literal first thing they typed (or the argument they passed to `/start-vague`). Don't edit it. Don't summarize it. This is the source-of-truth audit trail for V0→V1 drift checks.
   - `## The problem` — synthesized statement from Step 2.
   - `## Who it's for` — audience answer from Step 2.
   - `## Scope hint` — **verbatim Step 2 scope option label** (one of the four labels exactly as shown: `A weekend script`, `A small app I'd use`, `A real product`, `Not sure yet`). Informational signal for the user and for downstream readers (you, on a future session) about the intended size. Downstream skills do not currently branch on this field — it's a note, not a control.
   - `## What's out there` — **only if Step 1.5 gate ran scout early.** Write the scout summary here now so a Step-2 bail still leaves a complete-enough idea.md. If the gate did NOT run, omit this section here — Step 3 fills it after background scout returns.

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

Only if WebSearch ALSO fails (rare — offline or rate-limited) do you punt to: `## What's out there: Not checked yet` + 2-3 assumptions to verify during build. Public users without keys must finish `/start-vague` end-to-end.

**While scout runs**, ask. **Generate this question from Step 1 + Step 2** — don't ship the generic template. Anchor it in *their* audience, *their* problem, *their* friction. The user's reply is the success picture you'll quote verbatim into idea.md `## What good looks like` (Step 4) — vague question → vague quote → vague spec.

**Print this 🐘 tip in chat before the Question Block:**

> 🐘 *If you describe success vaguely, the build comes out vague. Picture one specific moment when this works and tell me what you see.*

Then use the Question Block format:

```
> **Your turn**
>
> **{Picture-anchor — name the audience + the specific moment the
> problem from Step 2 currently happens.}**
>
> {Friction-probe — name one friction they already mentioned and ask
> what it feels like in the new world.}
>
> Two directions to anchor against (or describe your own):
> - **Solid:** {a baseline take — the obvious, well-built answer}
> - **More out there:** {a stretch take — an unexpected angle that
>   reframes the moment}

*Just type your answer below ↓*
```

**Generation rules:**
- **Picture-anchor must reference the audience + moment**, not "what's different about your day." Example for pretty-todo-cards (audience: solo builder; problem: my todo list looks like a spreadsheet): *"It's Tuesday morning. You open the app and see your list — what do you see instead of the spreadsheet?"*
- **Friction-probe must name a friction they actually said** in Step 2. Example: *"You said adding a task feels like data entry. What does it feel like now?"*
- **Two clauses max in the picture+friction.** No "what does adding feel like? what does opening feel like? what about the home screen?" — that's a survey, not a question.
- **Two anchor suggestions — Solid + More out there.** Cold open-text questions invite sparse answers ("big timer in the corner"). Two anchored directions give the user something to react to or push past. **Solid** must be the obvious, well-built version of what they described (preserve their words). **More out there** must be a genuine stretch — reframe the moment itself, not just the styling. The user can pick one, riff off one, or say "actually neither, I want X." All three are wins.
- **Anchor honestly.** Don't pad the Solid option to make the stretch look better. Both must be plausible answers a thoughtful person would give. Suggestion-as-strawman is theater.
- If their Step 2 was thin (one-liner answer), say so plainly: *"You haven't named a specific friction yet — paint the picture in your own words and I'll work from that."* Skip the two anchors in this case — they'll fabricate friction from nothing. Don't fabricate friction to probe.
- **Quote the audience by name** if Step 2 named one. *"Picture {Sara, your designer friend}..."* beats *"Picture the user..."*.

**Bad (current generic):** *"If this worked perfectly — what's different about your day?"* — applies to every product ever built.
**Good (anchored + two directions):** *"Sunday night, you sit down to plan the week. Your list opens — what do you see? You said the current spreadsheet view kills the mood — what carries the mood now? **Solid:** Soft cards, one per day, neutral palette with a single accent. **More out there:** The list dissolves into a sketch — each item drawn in a different hand, like notes from your past self."*

**Breadcrumb after scout returns:**
> "That was `/scout` by the way — it checks Reddit, YouTube, and the web for real opinions. You can run it anytime: `/scout <any question>`."

---

## Step 3.5: Show Back (soft-redirect + wireframe)

Between Step 3 and Step 4, *show back* what scout found and what you think they want. This is the moment of truth before crystallizing — visual learners need a sketch, and anyone gets value from seeing "the thing you described already exists as X" surfaced honestly.

### 3.5a — Soft-redirect (only if scout found a strong match)

If `## What's out there` named a real product solving most of the problem, surface it inline as a single plain-text recommendation. Don't bury it in idea.md and march on — that wastes their time and your tokens.

```
🔍 One thing before we shape this — **<Product>** (<URL>) does <one line of what it does>
for <price>. Looks like it solves a lot of what you described.

Does that solve it for you? If not, what's missing that you'd build instead?
```

Plain text + open answer (not `AskUserQuestion` — recommendations want one preferred path, not a menu). Capture their response — it sharpens `## What this would do` in Step 4 by forcing the "what's missing" reframe.

- **"Yeah it solves it"** → exit gracefully. (1) `python3 vera-system/scripts/frontmatter.py set <project>/CLAUDE.md status=declined updated=today declined-for="<product> (<URL>) <date>"` (the script appends `declined-for` since it isn't an existing field). (2) Append a one-line entry to `vera-system/ideas.md`: `<date> — <slug>: considered then declined in favor of <product> (<URL>).` (3) Tell them: *"Saved the find. If you want to try it: <URL>. Come back anytime."* End the skill. User keeps agency. The scaffolded dir stays as a record — delete it manually if you want to forget the consideration ever happened.
- **"No, here's what's missing"** → carry their reframe into Step 4 as `## What this would do`.
- **Scout found nothing relevant** → skip this sub-step entirely. No empty "good news, nothing exists" lap.

### 3.5b — Mid-interview ASCII wireframe

After 3.5a (or skipping it if no scout match), sketch one screen in ASCII and ask if it matches. **Visual confirmation beats more questions** for visual users, and catches alignment failures that words miss — "oh, I didn't mean a list view, I meant a card grid."

**Print this 🐘 tip in chat before the sketch:**

> 🐘 *Words about layout are fuzzy. A sketch is exact. If you're picturing something different, say so now — way easier than changing it after I build it.*

Generate the wireframe from spark + framing + audience + success picture. **One screen only** (the main view — the screen they'd open most). Plain ASCII boxes:

```
┌─────────────────────────────────────────────┐
│  <App name (working title)>                 │
├─────────────────────────────────────────────┤
│  <Primary action / hero element>            │
│                                             │
│  ┌───────────────────┐  ┌────────────────┐  │
│  │ <Main content A>  │  │ <Main content  │  │
│  │                   │  │   B or aside>  │  │
│  └───────────────────┘  └────────────────┘  │
│                                             │
│  [Primary CTA]   [Secondary]                │
└─────────────────────────────────────────────┘
```

Present, then one open-text question:

```
> **Your turn**
>
> **Is this roughly what you have in mind?**
>
> If yes, we crystallize. If no, tell me what's
> wrong — too much on one screen? Wrong primary
> action? Different layout entirely?

*Just type your answer below ↓*
```

- **"Yes" or close to yes** → proceed to Step 4. Write the wireframe into idea.md as its own `## Wireframe (proposed)` section (a fenced code block under the heading). Step 4 must preserve this section verbatim, like `## Original spark` — `/build new` Stage 1 pulls it into the spec, and `/frame` can refine it.
- **"No, here's what's off"** → ONE retry with the correction. If the second sketch still misses, say plainly: *"Let's stop on the visual — Step 4 will write it in words and `/frame` can sketch it properly later."* Move on.

**Skip 3.5b entirely** if the idea is clearly non-visual (a CLI tool, a cron job, a script). For "rename my downloads folder," sketching a wireframe is theater. Use judgment.

---

## Step 3.6: Widen check (capture scope, don't tunnel)

The interview narrows fast, and it's easy to lock onto ONE angle of the idea and miss the others. This is the anti-tunnel beat (the "widen" pattern, applied up front instead of waiting for the user to ask). It widens what you SEE, then scopes what you BUILD — so V0 stays tight, but on purpose, not by accident.

**Print this 🐘 tip in chat before the question:**

> 🐘 *I want to make sure I'm not boxing this in too soon. Here are the angles your idea could take. Tell me which ones are actually part of the first version.*

One `AskUserQuestion`, multi-select. **Generate 2-3 DISTINCT angles** the idea could span from spark + framing + success picture (genuinely different directions, not three flavors of one thing). Mark the strongest as the core.

```
AskUserQuestion(
  questions: [
    {
      question: "Which of these are part of your first version?",
      header: "Scope",
      options: [
        {label: "<angle A> (Recommended — the core)", description: "<why this is the heart of V0>"},
        {label: "<angle B>",                          description: "<what it adds, and the cost of doing it now>"},
        {label: "<angle C>",                          description: "<what it adds, and the cost of doing it now>"},
        {label: "Just the core for now",              description: "Ship one thing; the rest goes to ## Open questions"}
      ],
      multiSelect: true
    }
  ]
)
```

Read the picks. **If they select more than two angles, push back once** to protect V0 (the cut-to-1-2 rule): *"That's a bigger first version. Ship the core now and park the rest, or is the wider scope the actual point?"* Whatever they keep flows into Step 4's idea doc. Whatever gets cut goes to `## Open questions` so it's parked, not lost.

---

## Step 4: Crystallize

You now have: the spark, the narrowed problem, community signal, and their success picture.

**First — capture the bet.** Before writing the idea doc, ask one AskUserQuestion that elicits the *category claim* — what changed that lets this exist now. Without this, V0 builds the literal spec but misses the move that makes it interesting.

**Print this 🐘 tip in chat before the AskUserQuestion:**

> 🐘 *Lots of similar apps already exist. What's the one reason to build yours instead of using one of those? I'll keep the build focused on that.*

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

## Scope hint
[Verbatim Step 2 scope label — exactly one of: `A weekend script`, `A small app I'd use`, `A real product`, `Not sure yet`. Informational note about intended size; not a control field for downstream skills.]

## What's out there
[Scout summary. What exists, what's missing.]

## What this would do
[The angle — why build when X exists? Should reach for ## The bet, not just restate ## The problem.]

## Wireframe (proposed)
<!-- Verbatim Step 3.5b sketch (if user confirmed). Omit section entirely if 3.5b was skipped or rejected. Do not edit on Step 4 rewrite — splice in unchanged. -->
```
[ASCII wireframe from Step 3.5b, unchanged]
```

## What good looks like
[Their words from the success picture. Include a verbatim quote of their Step 3 answer at the top of this section, formatted as a blockquote (`> "..."`); the rest of the section can be Vera's framing of that quote.]

## What this is NOT
[Scope they explicitly DON'T want, in their words. 1-2 lines. Omit the section entirely if nothing surfaced — better empty than invented.]

## Open questions
[2-3 unknowns to figure out during build.]
```

The verbatim-preservation rules — `## Original spark`, the Step 3 quote at the top of `## What good looks like`, and `## Wireframe (proposed)` if Step 3.5b confirmed — are the V0→V1 audit trail. Combined with `## The bet`, they let `/build full` later check whether what shipped matches what the user actually asked for *and* reaches for the category claim. Never paraphrase those.

**When presenting back in chat**, use markdown headings (`## [Idea Name]` + `### Section`) so it reads as a document, not a reply. Same hierarchy for every section.

Present it, then:

```
AskUserQuestion(
  questions: [
    {
      question: "How's this looking?",
      header: "Check",
      options: [
        {label: "Answer the open questions", description: "I have thoughts on these — walk me through each (multiple choice, with your Recommended pick)"},
        {label: "Yes, this is it", description: "Move on to the next step"},
        {label: "Close, but...", description: "I'll tell you what to tweak"},
        {label: "Nope, start over", description: "Not it — back to brainstorming"}
      ],
      multiSelect: false
    }
  ]
)
```

**Track an explicit `check_cycle` counter** (in conversation state — initialize 0 when Step 4 starts):

- **"Yes, this is it"** → continue to handoff. Done.
- **"Answer the open questions"** → Walk through each open question one at a time, **ordered by dependency** — if B's answer depends on A's, ask A first. Use AskUserQuestion with generated options per question (like Step 2 framings — not generic, specific to the question). **Mark one option as `(Recommended)` with a one-line rationale** so the user confirms or overrides instead of choosing cold. Update the idea doc with their answers. Then continue to handoff. (Doesn't increment `check_cycle`.)
- **"Close, but..."** → If `check_cycle == 0`: adjust per the user's tweak, increment `check_cycle` to 1, present the idea doc once more (re-run this same AskUserQuestion). If `check_cycle == 1` (this is the second "Close, but..."): fire the round-4 escape hatch below. We've now used the adjust budget.
- **"Nope, start over"** → fire the round-4 escape hatch below immediately. "Nope" means the direction is wrong, not the details — adjusting won't help.

### Round-4 Escape Hatch

When the interview hasn't landed after the second check-cycle (we've spent ~4 rounds), don't force a deliverable. Give the user three honest paths:

```
AskUserQuestion(
  questions: [
    {
      question: "We've gone a few rounds and the shape isn't landing. What feels right?",
      header: "Escape",
      options: [
        {label: "Let me re-pitch in my own words", description: "Open-text. Type the idea fresh — I'll regenerate framings from your wording. Scout findings + audience carry forward."},
        {label: "Keep going — push past the cap", description: "More questions. We've passed the 4-round soft cap, but you want to keep shaping. OK."},
        {label: "Park it for now", description: "I'll save what we have to vera-system/ideas.md with the current state. Come back when the shape is clearer."}
      ],
      multiSelect: false
    }
  ]
)
```

- **Re-pitch** → emit a Question Block to capture the new spark first, then re-enter Step 2 with the new wording. Preserve `## What's out there` and `## Who it's for` from the previous attempt (don't re-scout). The Question Block:

  ```
  > **Your turn**
  >
  > **Say it again, in your own words — what's the idea?**
  >
  > Don't worry about matching what we said before.
  > Just describe the thing as you'd describe it to a friend.

  *Just type your answer below ↓*
  ```

  Overwrite `## Original spark` with the new input (this is the only path where overwrite is allowed). Log the prior spark in a `<!-- prior spark (re-pitched <YYYY-MM-DD>): "<verbatim text>" -->` HTML comment ABOVE the new spark. **On a second or third re-pitch in the same session**, prepend additional `<!-- prior spark (re-pitched <date>): ... -->` lines — newest comment closest to the new spark, oldest at the top. Never delete prior-spark comments; they're the audit trail of how the idea shifted. Reset `check_cycle` to 0. Regenerate Step 2 framings from the new spark.
- **Keep going** → continue from here, no cap. Round budget is gone — Vera leans on the user's energy to know when to stop.
- **Park** → (1) `python3 vera-system/scripts/frontmatter.py set <project>/CLAUDE.md status=parked updated=today`. (2) Append the current state to `vera-system/ideas.md` as `<date> — <slug>: parked at Step 4 (shape didn't land). Spark: "<verbatim spark>". Audience: <X>. Scout: <one-line summary>.` (3) End the skill cleanly. Tell them: *"Saved. The thread is here when you come back."* A future `/start-vague <slug>` (or `/build new <slug>`) can re-enter from this state.

**Breadcrumb:**
> "Saved to your project folder. Closing here is fine — the thread will be here when you come back."

---

## Step 5: Hand Off

The dir, `CLAUDE.md`, and `idea.md` already exist from Step 2's partial save and have been updated through Step 4. Now finalize:

1. **If the idea name shifted in Step 4**, regenerate the slug (`python3 vera-system/scripts/frontmatter.py slug "<new name>"`), `mv` the project dir to match, then `python3 vera-system/scripts/frontmatter.py set <project>/CLAUDE.md slug=<new-slug>`.
2. Bump the date: `python3 vera-system/scripts/frontmatter.py set <project>/CLAUDE.md updated=today`. Leave `status: exploring` — the routing question below decides whether it stays or flips.
3. Append a one-line summary to `vera-system/ideas.md`.

Then:

```
AskUserQuestion(
  questions: [
    {
      question: "What next?",
      header: "Next",
      options: [
        {label: "Build it (Recommended)", description: "/build new turns this into a working app, resumable across sessions"},
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
- **Four rounds max** (Steps 1, 2, 3, 4). Sub-steps (Step 1.5 scout gate, Step 3.5 show-back) don't count as rounds — they're conditional decision points inside their parent step, not new question rounds. At Step 4, if shape hasn't landed after one adjust-cycle, the round-4 escape hatch fires (re-pitch / keep going / park). Don't force a deliverable that isn't shaped — parking is a clean exit, not a failure.
- **Three questions per `AskUserQuestion` batch where the surface supports it.** Step 2 batches framing + audience + scope. Other steps batch where the questions are genuine siblings (no Q2-depends-on-Q1 cross-talk).
- **Take variation per question.** Each option list is one of three shapes — **frame** (same question, different mental models), **scope** (same question, different sizes), or **perspective** (same question, different POV). Vera picks the shape per question based on what would surface the most useful answer. The variation IS the value — don't ship a "pick something generic" menu.
- **Breadcrumbs, not lectures.** One line after each step showing what Vera can do. That's it.
- **Voice — see `vera-system/who-i-am/voice.md` "Onboarding & user-facing surfaces."** 5% warmth ceiling. No exclamation, no celebration words, no anthropomorphizing. The signature is in considered specifics — framings of their words, anchored questions, real scout signal — not in warmth.
- **Question Block format for every open-text question.** First-timers can't easily distinguish "Claude is asking me something" from "Claude is talking." The bordered block resolves it visually. AskUserQuestion has its own UI — don't double-wrap.
- **🐘 tip lines before each major question.** One italicized line, 1-2 sentences, prefixed with the elephant emoji, explaining WHY this step exists. Surgical — Steps 2, 3, 3.5b, 4 only. Lives ABOVE the Question Block or AskUserQuestion call, never inside it. Voice: matter-of-fact, not patronizing. Skip if the explanatory prose already in the step body makes the WHY obvious.

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
