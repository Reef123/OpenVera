# V0 Pipeline (`/build new`)

Five stages — **one user stop, then autonomous to ship**:

```
Stage 0: Kickoff + Purpose   ← only user interaction
Stage 1: Parallel Sprint     ← background agents + scope/design/spec
Stage 2: Build Loop          ← supervisor + validator + reviewer
Stage 3: Score               ← external judge via openrouter
Stage 4: Ship                ← retro, V1 checklist, V0→V1 user interview, doc-sync
```

Vera check-in fire points + format: see [`vera-checkins.md`](vera-checkins.md).

---

## Stage 0: Kickoff + Purpose (ONE stop — the only one before code)

This is the ONLY user interaction before building starts. Combine kickoff, scoping, and purpose check into one shot. Be bold — present opinionated options based on the idea they gave you.

**Print this opener BEFORE firing AskUserQuestion** — sets expectation about what `/build new` produces and why the questions exist. Without it, first-time users see a wall of options with no context for why they're picking. Bold the Vera-voice line so it visually pops as a notification, not chatter:

```
**🐘 Here's the plan, <user-name>:**

By the end of this session you'll have a working V0 — a clickable prototype running in your browser that you can use, break, and show people. Not production. Just enough to validate the idea is worth building further.

I'll walk through the design tree in two to four short steps — Problem first, then build path, then the one action that has to work, plus a quick pressure-test on any gaps. ~2-3 minutes of decisions, then I run for ~10-20 min and surface back when V0 is ready.
```

**Voice rules:** read `relationships/user.md` for the name (fall back to "you"). Skip the opener if `voice.md`/`user.md` are missing AND the user clearly knows what /build does (referenced prior builds). On a true first-time `/build new`, always print it.

**Design-tree walk — 2-4 steps.** *Vocabulary note: pipeline phase names use "Stage" (Stage 0/1/2/3/4 — internal state-machine). User-decision walks within a stage use "Step" (matches `/start-here`'s convention). Same word as `/start-here` so users see one mental model across both onboarding skills.* Claude Code's `AskUserQuestion` tool caps at 4 questions per call, but the real reason for grouping is dependency resolution: each step resolves the decisions that the next step's options depend on. Stage 0 is structured as **Step 1 — Problem** (root of the tree), **Step 2 — Build path** (options informed by Step 1 + scout if it ran), **Step 3 — Surface** (options informed by Step 2's Shape), **Step 4 — Pressure Test** (generated grills on Vera's implicit-decision gaps — fires only when HIGH/MED gaps exist). Between Step 1 and Step 2 there's an optional **Scout gate** — a recommendation, not a step — that fires when signals warrant `/scout` even though the user said no to research. Total user-facing decisions: 2-4 steps plus an optional yes/no on scout.

**Step 1 — Problem (max 4 Qs):**

Three sibling questions at the root — Job + Pain + 30s test triangulate the problem from three angles. Plus user's pre-emptive research depth choice.
```
AskUserQuestion(
  questions: [
    {
      question: "Someone opens this for the first time. What's the ONE thing they're trying to get done?",
      header: "The Job",
      options: [
        {label: "[Job A — your best guess from the idea]", description: "Build around this. Everything else is decoration."},
        {label: "[Job B — a different framing]", description: "Different angle. Changes what 'done' looks like."},
        {label: "Neither — let me tell you", description: "I'll type the real job."}
      ]
    },
    {
      question: "If this works perfectly, what does the user STOP doing?",
      header: "The Pain It Kills",
      options: [
        {label: "[Pain A — specific manual process or workaround]", description: "They currently do this by hand or with duct tape."},
        {label: "[Pain B — a different friction point]", description: "This is what actually hurts."},
        {label: "Something else", description: "I'll describe the real pain."}
      ]
    },
    {
      question: "First person opens it. What do they try in the first 30 seconds?",
      header: "The 30-Second Test",
      options: [
        {label: "[Action A — the obvious first move]", description: "If this doesn't work, they close the tab."},
        {label: "[Action B — a different entry point]", description: "This is what they'd actually click first."},
        {label: "Let me think about it", description: "I'll type the real first action."}
      ]
    },
    // SKIP this question if idea.md's "What's out there" section has real signal (scout or WebSearch output).
    // KEEP it if the section says "Not checked yet" or is "[pending]" — start-here couldn't validate, user still needs to.
    {
      question: "Do you want to explore the space first?",
      header: "Research",
      options: [
        {label: "No — I know what I want. Build it.", description: "Skip research, go straight to building."},
        {label: "Quick scout", description: "2-3 min Reddit + web check for gotchas (~free)"},
        {label: "Full research", description: "Deep multi-model research (~15 min, ~$0.40)"}
      ]
    }
  ]
)
```

**Rules for generating options (applies to all steps):**
- Be specific and opinionated. "[Job A]" should be a real sentence like "Find out which licenses are wasted" — not "View dashboard data."
- Options should be DIFFERENT framings, not variations of the same thing.
- Make the user disagree with you — that produces better specs than agreement.
- If they pick "Neither" / "Something else" — best outcome. They just articulated it themselves.

---

**Scout gate (between Step 1 and Step 2 — recommendation, not a step):**

After Step 1 answers come back, evaluate Job + Pain + 30s test for signals that warrant `/scout` even when the user picked "No — I know what I want" in Research depth. The gate is Vera's catch for crowded spaces the user didn't anticipate.

**Signals (any one fires the gate):**
- Job names a crowded category — "todo", "notes", "dashboard", "habit tracker", "journal", "kanban", "note-taking"
- Specific external platform/API named in Job or Pain — "Notion", "Linear", "Slack", "GitHub", "Stripe", any named API or SaaS
- Pain framed as "alternative to <existing tool>" or "X but better"
- `/start-here` Step 4 left "What's out there" as `[pending]` AND Job is in a category where existing tools are likely

**Gate logic:**
- If user picked **"Quick scout"** or **"Full research"** in Step 1 → gate is moot (already running in Stage 1). Skip.
- If user picked **"No"** AND no signals fire → skip. Trust their pre-emptive choice.
- If user picked **"No"** AND ≥1 signal fires → fire the gate. Plain text, single yes/no recommendation:

```
🔍 Quick check before I lock the build path: <one-line reason — e.g., "todo apps are a crowded space — there might already be a tool that does what you described"</one-line>. Running `/scout` (~2-3 min, ~free) would tell me if there's an existing tool worth using vs. building from scratch.

   Run scout first? (recommended)
```

Use plain text + single yes/no, not `AskUserQuestion`. This is a recommendation with one clearly preferred answer, not a menu of equal options.

- If user says **yes** → spawn `/scout` foreground (not background — Step 2 needs the result). When scout returns, summarize findings in 2-3 lines, then continue to Step 2 with Build-vs-Use as the 4th question.
- If user says **no** → continue straight to Step 2 without Build-vs-Use. Don't re-ask. They've now declined twice.

**If idea.md already has fresh scout/research output** (from `/start-here` or prior session): skip the gate but USE the findings — Step 2 includes Build-vs-Use if existing tools were found.

---

**Step 2 — Build path (max 4 Qs):**

Now that the problem is defined, walk the build branch. **Shape is the parent** — it branches everything below (UI vs. UI+data vs. API). Stack and Validation depend on Shape; their options must be ordered by Shape fit before firing.

```
AskUserQuestion(
  questions: [
    {
      question: "What shape is this app?",
      header: "Shape",
      options: [
        {label: "Just UI", description: "No database, no auth — pure frontend"},
        {label: "UI + data", description: "Needs to store/read data (adds SQLite or Supabase)"},
        {label: "Nice-looking UI + data", description: "Add a component library (shadcn/ui, DaisyUI) + database"},
        {label: "API only", description: "No UI — just endpoints"}
      ]
    },
    {
      question: "Stack?",
      header: "Stack",
      // OPTIONS DEPEND ON LIKELY SHAPE — order them by Shape fit before firing.
      // Inference signal: if 30s test from Step 1 is web-clickable → Shape likely UI/UI+data → web frameworks first.
      // If Job mentions "API", "endpoint", "script", "CLI" → Shape likely API only → backend langs first.
      // The user still picks Shape in Q1 above, but option ORDERING here primes the right default.
      options: [
        {label: "SvelteKit", description: "Fast, simple, less boilerplate (default for UI)"},
        {label: "Next.js", description: "React ecosystem, huge community, most tutorials"},
        {label: "Astro", description: "Content/static sites, blogs, docs"},
        {label: "Python", description: "APIs, scripts, data tools"},
        {label: "Go", description: "CLI tools, fast APIs"},
        {label: "Help me choose", description: "I'll recommend based on Shape"},
        {label: "Something else", description: "Tell me your stack"}
      ]
    },
    {
      question: "How do we know it works?",
      header: "Validation",
      // OPTIONS DEPEND ON LIKELY STACK — Browser is the default for web stacks; Run command for CLI/API.
      // Order by likely Shape: UI → Browser first; API only → Run command first.
      options: [
        {label: "Browser", description: "Open in Chrome, click through it (UI apps — default)"},
        {label: "Run command", description: "Execute it, check output (CLIs, APIs, scripts)"},
        {label: "Test suite", description: "Write + run tests (libraries, packages, backends)"}
      ]
    },
    // ADD this question ONLY when scout/research (Step 1 choice OR Scout gate) found viable existing tools.
    // Generate options from the "What's out there" section of idea.md OR from scout results returned via the gate.
    // If scout found nothing relevant, skip this question entirely (Step 2 becomes 3 Qs).
    {
      question: "Scout found existing tools in this space. Build custom or use one?",
      header: "Build vs. Use Existing",
      options: [
        // GENERATE THESE from scout results. Example:
        //   {label: "Use Obsidian + Dataview", description: "Already dominates this niche — vault lock-in is the tradeoff"},
        //   {label: "Build custom", description: "Nothing does exactly what you described. Worth building."},
        //   {label: "Consult on this", description: "Run /consult to frame the build-vs-use tradeoff properly"}
        {label: "[Existing tool A]", description: "[what it does well + its main tradeoff]"},
        {label: "Build custom", description: "[why the gap justifies building]"},
        {label: "Consult on this", description: "Run /consult to think through build vs. use"}
      ]
    }
  ]
)
```

**Dependency rule:** Stack and Validation options are ORDERED by likely Shape inferred from Step 1's Job + 30s test. The user can still override (e.g., pick Python for a UI app), but the default-first option should match the most likely Shape so the user can ratify Vera's read instead of re-thinking from scratch.

---

**Step 3 — Surface (one question, single-select):**

After Step 2 answers come back, ask one final question that puts scope visibility in the user's hands. Without this, Vera unilaterally decides what's must-have vs. cut, and V0 ships narrower than the user's mental model expects.

**Why a separate step:** Surface action options depend on Step 2's Shape. For UI builds the must-have action is something like "Mark complete" or "Reorder cards"; for API-only builds it's "POST /tasks" or "Authenticate request". Folding this into Step 2 would force pre-Shape generation and lose fidelity.

Generate 3 most-likely-needed actions from the spark + spec sketch + The Bet. Each description = a one-line "stake" — what breaks without this. Single-select forces priority and protects V0 scope:

```
AskUserQuestion(
  questions: [
    {
      question: "Beyond 'add', what's the ONE action that has to work for V0 to feel real?",
      header: "Surface",
      options: [
        // GENERATE 3 from context. Labels = action verbs. Descriptions = stakes ("Without it, ...").
        // Example for pretty-todo-cards:
        //   {label: "Mark complete", description: "Without it, the list grows but never shrinks."},
        //   {label: "Delete a task", description: "Without it, mistakes pile up forever."},
        //   {label: "Reorder cards", description: "Without it, the board feels static."},
        {label: "[Action A]", description: "Without it, <one-line stake>."},
        {label: "[Action B]", description: "Without it, <one-line stake>."},
        {label: "[Action C]", description: "Without it, <one-line stake>."},
        {label: "Just 'add' is enough — I'll add more after seeing it work", description: "Minimalist V0 — everything else moves to V1."}
      ]
    }
  ]
)
```

**Rules for generating actions:**
- Pick from the user's likely sustained-use loop, not edge cases. "Mark complete" beats "Export CSV" for a personal todo.
- Stakes must be concrete. "Without it, <one line>" forces a real failure mode, not "would be nice."
- Don't include any item already named in user's Step 1 "The Job" — that's already in scope.
- Single-select. The PICK gets promoted from Cut List to spec.md "Core flow." The other 2 candidates stay on Cut List with their stakes preserved as the *Why Cut* reason.
- "Just 'add' is enough" is the explicit minimalist escape. Some users genuinely want the smallest V0; honor it.

**After Step 3 answer:** That action joins the V0 build. If Vera's scan finds HIGH or MEDIUM unresolved gaps, fire Step 4 — Pressure Test. Otherwise (no significant gaps, or user picked "Just 'add' is enough"), Stage 1 launches in parallel — no more stopping.

---

**Step 4 — Pressure Test (1-3 generated grills, opportunistic):**

Steps 1-3 collect *explicit* decisions. Step 4 surfaces the *implicit* ones — the choices Vera would have to make to write spec.md but the user hasn't actually told her. This step isn't a template; it's a procedure for runtime generation.

**Procedure:**

1. **Scan Steps 1-3 answers for implicit decisions.** Walk each branch:
   - **From Step 1 (Problem):** What rule defines the success/failure state? (e.g. "stalled" = ?) Single-user or multi? Pain recurring or one-time? Data lifecycle (transient/persistent/shared)?
   - **From Step 2 (Build path):** If Shape = UI+data, where does data persist between sessions? If Stack has multiple defaults (TS vs JS, SSR vs static, dev mode vs build snapshot), which? If Validation = Browser, what does FAIL paint look like?
   - **From Step 3 (Surface):** What's the success signal of the picked action — visual feedback, data change, navigation? Failure state? If the action implies drill-down or detail content, what's IN that detail?

2. **Rank each implicit decision by build-risk** — if Vera's guess is wrong:
   - **HIGH** = re-architect required (data lifecycle, success-rule definition, surface detail scope)
   - **MEDIUM** = substantial rework (validation thresholds, default behaviors, content shape)
   - **LOW** = trivial fix (label text, color choice) — ignore for Step 4

3. **Pick top 3 highest-risk gaps.** If fewer than 3 HIGH/MEDIUM exist, fire fewer grills. Pressure-Test is opportunistic, not ceremonial — don't manufacture rounds.

4. **Generate one grill per gap.** Each:
   - States Vera's current guess in **concrete values** (numbers, paths, behaviors — not abstractions)
   - Asks user to ratify or correct
   - Format: plain text usually; `AskUserQuestion` only when the gap is genuinely multiple-choice
   - Fires **sequentially** (not batched) — each answer may inform Vera's read of the next gap

5. **Apply each correction immediately** to scope notes. After the last grill, Stage 1 launches with the corrected reads, and spec.md will reflect ratified-or-corrected values rather than Vera's untested guesses.

**Skip Step 4 entirely if:**
- Step 3 answer was "Just 'add' is enough — I'll add more after seeing it work" (minimalist-V0 explicit ask — honor it)
- No HIGH or MEDIUM implicit decisions remain after the scan (the user's answers were already exhaustive — rare, but possible)

**Worked examples** (generated from a real vera-dashboard run — illustrative, NOT templates to copy verbatim):

> *Round 1 — drills on Step 1 (Job: "see which projects alive vs stalled"):*
> "I'm planning to define 'stalled' as `updated > 14 days AND status != shipped`. That right — or is stalled a different signal: last build attempt, last commit, no recent telemetry?"

> *Round 2 — drills on Step 2 (Stack: SvelteKit static):*
> "Two timing models for the data reads: live filesystem reads on every nav (dev-mode default), or build-time snapshot pinned at `npm run build` (shareable). Which matters — live, snapshot, or both?"

> *Round 3 — drills on Step 3 (Surface: "click row → detail page"):*
> "Detail page would show formatted CLAUDE.md content. Enough — or does it need things CLAUDE.md doesn't have: recent commits, build state machine, telemetry rows for this project?"

Each grill exposes a guess Vera was about to lock into spec.md. User answers either confirm (Vera proceeds with that guess as fact) or correct (spec.md changes before build runs). The whole step takes ~1-2 min when 3 gaps exist; less when fewer.

---

## Stage 1: Parallel Sprint (autonomous — no user interaction)

Launch ALL of these simultaneously. The user answered everything they need to in Stage 0.

**Background agent 1 — Doc-sync:**
```
Agent(
  description: "doc-sync build start",
  prompt: "Run /doc-sync. Update vera-system/state.md with 'Starting V0 build: [PROJECT_NAME]'. Add to vera-system/ROADMAP.md.",
  run_in_background: true
)
```

**Background agent 2 — Research/Scout** (if requested):
- "Quick scout" → `Agent(description: "scout for build", prompt: "Run /scout [IDEA]. Focus on gotchas, what actually works, what fails.", run_in_background: true)`
- "Full research" → `Agent(description: "research for build", prompt: "Run /research --no-scope on: [IDEA]. Do not ask clarification questions — scope was set in /build Stage 0.", run_in_background: true)`

**If research/scout fails (API key missing, network error):** Do NOT silently substitute. Tell the user:
> "Full research requires an OpenRouter API key. Your options: (1) Add key to vera-system/.secrets and retry, (2) Downgrade to /scout (free, web-only), (3) Skip research and build with what we have."
Never downgrade without asking.

**Background agent 3 — Framework picker** (if "Help me choose"):
```
Agent(
  description: "framework comparison",
  prompt: "Score 3 candidates on: AI Buildability, Time to Working App, Ecosystem (1-5 each). Table format. Recommend one. 3 min max.",
  run_in_background: true
)
```

**Main thread — idea.md guarantee + domain experts + scope + design + spec (do all of this NOW):**

0. **idea.md guarantee (30 sec):** Check if `{paths.projects_dir}/<slug>/idea.md` exists.

   - **Exists** (project came from `/start-here`): read it, use as-is. Skip the synthesis below.
   - **Missing** (direct `/build new <idea>` with no prior /start-here): synthesize one from Stage 0 answers + the original `<idea>` argument. This makes the spec-from-idea handoff uniform regardless of entry point — `## The bet`, `## Original spark`, and `## What good looks like` are the V0→V1 audit trail and must exist before Spec writes.

   Synthesis template (write to `{paths.projects_dir}/<slug>/idea.md`):

   ```markdown
   # <Project Name>

   ## Original spark
   <!-- Verbatim of the <idea> argument passed to /build new. Do not edit. -->
   > <the literal idea string the user passed, unchanged>

   ## The bet
   <!-- Synthesized from Step 1 (Job + Pain + 30s test) + scout findings (if scout ran).
        The category claim this V0 reaches for — what changed that lets this exist now.
        Labels = 3-6 word noun phrases. Why now = the leverage (model capability, primitive shipped). -->
   **<bet label>**

   Why now: <one line — the leverage that makes this possible>

   ## The problem
   <Step 1 "The Pain It Kills" answer, in their words.>

   ## Who it's for
   <Inferred from Step 1 — single-user / partner / team / public. Mark "inferred" if not explicit.>

   ## What's out there
   <If scout/research ran in Stage 0 or via the gate, summary here. Else: "Not checked yet — direct /build new path.">

   ## What good looks like
   <Step 1 "30-Second Test" answer, framed as a moment.>

   ## Open questions
   <Empty or 1-2 unknowns surfaced during Stage 0.>
   ```

   **Synthesis rules:**
   - **Spark is verbatim.** Whatever string the user passed after `/build new` is the spark, unedited. If they passed nothing (e.g., `/build new` with empty arg), use the answer to Step 1 "The Job" as the spark.
   - **Bet is a best-effort guess.** Vera generates the category claim from Stage 0 context — it's not as strong as a /start-here-captured bet (where the user picked from 3 framings), but it anchors V0 build decisions and gives /build full something to compare against. Flag in `retro.md` if the bet felt forced.
   - **Inference markers.** Where a field is inferred (audience, bet), include a one-word marker so /build full knows it wasn't explicitly user-stated.

   Once idea.md exists (either path), continue to step 1.

1. **Domain experts (2 min):** What domains? What would each 10-year expert check first? Agreement = foundation. Conflict = decisions. Quick table. Tripwire: "Am I excited about surface polish instead of whether the foundation supports the actual use case?"

2. **Scope guard (2 min):** From the user's Purpose answers + domain experts:
   - The ONE problem (from "The Job")
   - 3-5 steps of the core flow
   - Stack (from their answer, default SvelteKit)
   - Cut everything else aggressively. Can this ship in one session? If no, cut more.

3. **Spec (5 min):** Read `idea.md` to pull `## The bet` (guaranteed to exist after step 0). Then write `spec.md` (template below). **Spec is written BEFORE design artifacts** — `/frame --from-spec` reads spec.md mood signals to pick a palette from the rotation set, and reads spec.md component boundaries to scaffold wireframes. Design without spec context produces generic output.

4. **Design artifacts (3-5 min):** Now that spec.md exists, invoke `/frame` to generate architecture diagrams, design system, and wireframes:

   ```
   /frame <slug> --quick --from-spec
   ```

   This produces `arch.md`, `DESIGN.md`, and `wireframes.md` in the project dir. These are the build targets — the build loop and reviewer validate code against them. Palette is picked from the Vera Considered Palettes rotation set (see `/frame` SKILL.md "Aesthetic Floor") based on spec.md mood signals.

**Spec template** (referenced by step 3):

```markdown
# [Project Name]

## The bet
<!-- Pulled verbatim from idea.md ## The bet. The category claim this V0 reaches for. -->
**[Bet label]**

Why now: [the leverage from idea.md]

## Purpose (what this actually does)
**The job:** [their answer to Q1]
**The pain it kills:** [their answer to Q2]
**The 30-second test:** [their answer to Q3]

## Problem
[1-2 sentences from The Pain It Kills]

## Solution
[1-2 sentences. Should reach for ## The bet, not just restate the literal job.]

## Core Flow
[3-5 steps]

## Out of Scope
[Everything else. Aggressive.]

## Stack
[Framework + key libs + component library if chosen + database if chosen]

## Validation
[Browser / Run command / Test suite — from Stage 0]

## Cut List
- **[feature]** — [reason]. *Revisit [V1 / V2 / never].*
- **[another feature]** — [reason]. *Revisit [V1 / V2 / never].*
```

Bullets, not a table — Why-Cut reasons routinely wrap and break table rendering.

**The bet anchors Stage 2 build decisions.** When picking a component pattern, library, or scaffold detail, ask: *does this reach for the bet, or just satisfy the literal Job?* If a choice could go either way, lean toward the bet. Direct-`/build new` paths get a synthesized bet at Stage 1 step 0 — weaker than a /start-here-captured bet (where the user picked from 3 framings) but still a useful anchor. If the synthesized bet feels forced during Stage 2, flag in retro.md so /build full can revisit.

**Sync point:** Wait for research/scout/framework (if running). Incorporate findings into spec.

5. **Auto-mode toggle:**

   Call `EnterPlanMode` with spec.md as the plan body (Purpose, Core Flow, Stack, Cut List). The plan mode UI is the **only** programmatic mechanism for a skill to put Claude Code into auto-accept-edits mode — via the "Yes, and use auto mode" exit option. We use plan mode here purely for that bridge, not as exploration ceremony.

   **Frame the plan mode entry honestly in chat** so the user understands what they're actually picking:

   > "This is the auto-mode toggle. Pick *Yes, and use auto mode* to let Stages 2–4 run without permission prompts. Pick *Yes* for manual approval each step. Pick *No* to revise spec.md first."

   When the user exits plan mode:
   - *"Yes, and use auto mode"* → Stages 2-4 run autonomously, no permission prompts. **This is the bridge.**
   - *"Yes"* → Continue in current permission mode (manual approval each edit).
   - *"No, keep planning"* → Update spec.md from their feedback, re-enter plan mode. Max 2 revision rounds, then continue regardless.

   **Why plan mode (and not a plain AskUserQuestion):** plan mode's exit-with-auto-mode option is the only way a skill can flip Claude Code into auto-accept-edits programmatically. AskUserQuestion can only *tell* the user to press Shift+Tab — that loses the bridge. The plan-mode UI is functionally an "execute mode picker" here, just framed as planning. Calling it the auto-mode toggle in the prompt removes the ceremony confusion.

6. **Scaffold + verify (before any code):** Scaffold into a **subdir** of the project — `web/` for Node, `app/` for Python. By Stage 1 step 6 the project dir already contains `CLAUDE.md`, `idea.md`, `spec.md`, and any `/frame` design artifacts; `create-next-app .` and most greenfield scaffolders refuse non-empty dirs. Always scaffold to a subdir. From `{paths.projects_dir}/<slug>`:
   - `npm create svelte@latest web` then `cd web && npm install`
   - `npx create-next-app web`
   - `mkdir app && cd app && python -m venv .venv`

   Run dev server + verification commands from inside the scaffold subdir. Project-level artifacts (`CLAUDE.md`, `spec.md`, `retro.md`, `v1-checklist.md`, `v1-notes.md`) stay at the project root. If the scaffold doesn't load → fix it first; never write app code into a broken scaffold.

   ```bash
   python3 vera-system/scripts/build-state.py <slug> "V0 Stage 1" --substage "scaffold verified"
   ```

**Exception:** If research reveals the idea is fundamentally flawed (e.g., the thing already exists and is free), stop and tell the user.

---

## Stage 2: Build Loop

**Multi-agent, validation-first.** The main thread (you) is the supervisor. You write code one component at a time. After each component, the validator agent independently verifies it works.

```
supervisor (you):
  pick next smallest step from spec
    ↓
  write contract (.build/contract.md):
    what's being built, 3-5 concrete acceptance criteria, what's out of scope
    ↓
  implement one component (you write the code)
    ↓
  spawn validator agent:
    Agent(subagent_type: "validator", prompt: "Validate project at {project_path} using {method} (browser|command|tests). Contract at: {project_path}/.build/contract.md. Check each acceptance criterion. Write results to {project_path}/.build/validation.md")
    ↓
  if validator reports FAIL → fix, re-validate
  if PASS → next component
    ↓
  after core flow complete:
    spawn reviewer agent:
      Agent(subagent_type: "reviewer", prompt: "Review {project_path}. Spec at: {spec_path}. Read all source files, compare against spec, find issues. Write review to {project_path}/.build/review.md")
    ↓
  fix Critical/High findings → Score
```

**Contract format** (`.build/contract.md` — overwritten each step):
```markdown
# Contract: [component name]
## What was built
[1-2 sentences]
## Acceptance criteria
- [ ] [testable — e.g., "clicking Submit sends POST to /api/items"]
- [ ] [testable — e.g., "empty state shows 'No items yet' message"]
- [ ] [testable — e.g., "invalid input shows inline error, doesn't submit"]
## Out of scope
[what this component does NOT do yet]
```

**Validation methods** (from Stage 0 choice):
- **Browser:** Start dev server, verify each route loads, apply design tokens as you build
- **Command:** Get tool runnable first (`--help` works), test each feature
- **Tests:** Write one test for core behavior first, build to make it pass

**The 30-Second Test (after core flow works):**
Before declaring V0 complete, attempt the 30-second test from the Purpose Check. If it fails → fix before Score.

**Rules:**
- One component at a time. Fix before moving on.
- NO features beyond the core flow. Everything else is V1.
- If something is hard to build, it's probably out of scope. Cut it.
- **Wireframe before substantial UI.** Rule lives in `vera-system/memory/patterns.md` "Wireframe UI Before Building". Build-loop note: existing `wireframes.md` entries from `/frame` (Stage 1) ARE the sign-off for planned screens — only sketch when the work isn't already wireframed.

### Aesthetic Floor (UI builds — Shape = Just UI / UI + data / Nice-looking UI + data)

V0 ships shouldn't look ugly. Token cost to do better is small. **Apply DESIGN.md tokens as you write components — never default to bootstrap aesthetic.**

**Mandatory floor for any UI V0 (even when DESIGN.md is thin):**

| Rule | Forbidden | Required instead |
|------|-----------|------------------|
| Background | `bg-white` (pure `#FFFFFF`) | Warm paper (`#faf9f5` or similar — slightly off-white with warmth) |
| Body type | `font-sans` system-ui default | Considered serif for body (Lora, Source Serif, Crimson) OR considered sans (Inter, Geist) — never browser default |
| Accent color | `bg-blue-500`, `bg-indigo-500` (Tailwind defaults) | ONE warm accent picked for the project (coral, terracotta, ochre, sage). Used sparingly. |
| Borders | `border-gray-200`, `border-gray-300` | Warm soft border (`#d6d4ca` or DESIGN.md token) |
| Text color | Pure `#000` or `#111827` (slate-900) | Slightly off-black (`#141413` or warm ink) |
| Shadows | `shadow-md`, `shadow-lg` (default) | Whisper shadow (`0 0.25rem 1.25rem rgba(0,0,0,0.035)`) or none |
| Radius | All `rounded-md` everywhere | Considered radius scale (0.5–1.5rem range) with intent per element |

**If DESIGN.md exists in project root:** read it before each component. Apply its tokens. The supervisor's job is *interpreter*, not *generator* — DESIGN.md is the contract.

**If DESIGN.md is missing or thin** (rare — `/frame --quick --from-spec` ran in Stage 1): apply a palette from the **Vera Considered Palettes rotation set** (full table in `/frame` SKILL.md "Aesthetic Floor" section). Six palettes — Warm Paper/Coral, Linen/Sage, Ivory/Indigo, Bone/Terracotta, Stone/Ochre, Cream/Plum. All share the philosophy (warm bg, soft borders, ONE accent) but rotate hues so V0s have visual variety across builds.

**Pick which palette:**
1. Match `spec.md` mood signals to the palette set: conversational/onboarding → Coral; calm/utility → Sage; thoughtful/serious → Indigo; craft/artisanal → Terracotta; documentary/archival → Ochre; soft/creative → Plum.
2. If ambiguous, hash the slug: `sum(ord(c) for c in slug) % 6` indexes into the set deterministically.

Apply the chosen palette's tokens verbatim — bg, bg-alt, text, text-secondary, border, accent. Plus: serif body (Lora) + utility sans (Inter) + heading geometric (Poppins), radius baseline `1rem`, whisper shadows.

**Implementation pattern:** Define palette tokens as CSS custom properties at `:root` (or under `@theme inline` for Tailwind v4). Layer role tokens on top (`--color-bg: var(--color-paper)`, `--color-foreground: var(--color-ink)`, etc.) so component code references roles, not raw hexes. Mirror this structure across whichever palette gets picked — only the values rotate.

**Token cost note:** the floor adds ~5-10% to V0 build time. The user has explicitly authorized it — don't ship ugly to save tokens.

**Don't always pick coral.** If recent V0s all landed on Warm Paper / Coral, the rotation is broken — re-check mood matching.

---

## Stage 3: Score

Read `.build/validation.md` and `.build/review.md` (if they exist) for evidence. Score the build using the scoring model from config as judge via `openrouter.py`. **Do NOT self-score.** If the OpenRouter call fails (no API key, network error), say "Scoring skipped — no external judge available. Run `python3 vera-system/scripts/openrouter.py --verify` to check your key." Do not fall back to rating your own work.

**Calibration — 4.8 means near-perfect. A working V0 with basic UI is a 3.5, not a 4.5.**

```
python3 vera-system/scripts/openrouter.py \
  --model "{llm.scoring_model}" \
  --system "Score this build CRITICALLY. You are a harsh but fair reviewer. A 3 is 'works but rough.' A 4 is 'solid, minor issues.' A 5 is 'genuinely impressive.' Most V0s should land 3.0-3.8. Return ONLY valid JSON." \
  --prompt "SPEC:\n{spec}\n\nPURPOSE:\n{purpose section}\n\nVALIDATION METHOD:\n{browser|command|tests}\n\nVALIDATION EVIDENCE:\n{what works/broken}\n\nScore each dimension 1-5:\n- Functionality: does the core flow work end-to-end?\n- Architecture: is the code structured well for what it does?\n- UI/Design: does it look good? Is it intuitive? (score 1 if no UI)\n- Completeness: does it cover the spec, or are pieces missing?\n- Polish: error handling, edge cases, loading states, affordances\n\nReturn: {\"dimensions\": [{\"name\": \"...\", \"score\": N, \"reason\": \"...\"}], \"composite\": N.N}"
```

**Scoring calibration:**
- 3.0-3.5 = works but rough (typical V0)
- 3.5-4.0 = solid foundation (good V0 or basic V1)
- 4.0-4.5 = polished (strong V1)
- 4.5-5.0 = exceptional (rare — means design, code, AND UX are all strong)

- Composite >= 3.5 → ship
- Composite < 3.5 → fix outputs (max 2 rounds), then ship imperfect. V0 ships imperfect.

```bash
python3 vera-system/scripts/build-state.py <slug> "V0 Stage 3" --artifact "Build score=X.X/5.0"
python3 vera-system/scripts/telemetry.py build <PASS|SOFT_FAIL> --project <slug> --score X.X --latency <seconds> --cost <usd> --note "<project name>"
```

---

## Stage 4: Ship

**Order matters.** State files (frontmatter, telemetry, any data the V0 reads) must be written BEFORE booting the dev server. Otherwise the first-paint check reads stale data and the user opens a V0 that looks broken (real failure mode from user testing 2026-05-10 — vera-dashboard rendered `Hero: 0 builds shipped` because telemetry was written after server boot).

1. **Verify the core flow works end-to-end** (browser screenshot, command output, or test results — match the validation method from Stage 0).

2. **Update project `CLAUDE.md` frontmatter:** `status: shipped`, `score: X.X`, `updated: <today>`. Update `run:` if it changed.

3. **Update build state:**
   ```bash
   python3 vera-system/scripts/build-state.py <slug> "complete" --artifact "Final score=X.X/5.0"
   ```

4. **Write any telemetry / state rows the V0 reads from filesystem.** Common examples: append to `vera-system/runs/build-telemetry.tsv` for dashboard-style projects; seed any required SQLite rows; write any `.json` state files. Anything the V0 reads at boot must be current BEFORE step 5.

5. **Boot the V0** using the `run:` command from `CLAUDE.md` frontmatter (e.g. `npm run dev`, `open <abs-path>`, `python -m app`). For dev-server projects, capture the resolved port from server output — stack defaults: SvelteKit/Vite `5173`, Next.js `3000`, Astro `4321`, Python (uvicorn/Flask) `8000`.

6. **First-paint verification (Playwright MCP).** For UI projects, open the V0's URL with `browser_navigate`, then `browser_snapshot` to read rendered text. Check the paint against the V0's `spec.md` `## Validation` section:
   - **Pass:** every Validation criterion is satisfied in the paint, OR the criterion is one spec.md explicitly lists as "empty-state OK"
   - **Fail:** at least one Validation criterion not satisfied AND not flagged empty-state-OK
   - **Capture** `.build/screenshots/v0-first-paint.png` regardless of pass/fail (retro evidence)
   - **If Playwright MCP unavailable:** record `first-paint check skipped — Playwright MCP not installed` in `.build/validation.md`, skip to step 7 (same fallback pattern as `phases.md`)
   - **For CLI / API / library projects (no UI):** skip Playwright; instead re-run the validation command and parse its output against spec.md Validation criteria with the same pass/fail rule

   **On fail:** diagnose cause (race condition? broken read? missing data? wrong path?), attempt **one** self-heal — common fixes: re-run step 4 (telemetry write), force frontmatter rewrite, restart dev server, fix a path. Re-run the paint check. Pass on retry → continue to step 7 as normal. Still fail → record fail status + diagnosis + suggested fix in `.build/validation.md`, continue to step 7 (the rich summary in step 9 will surface a "Heads up" section honestly rather than papering over).

7. **Spawn doc-sync as background agent.** Don't wait.

8. **Write `{paths.projects_dir}/<slug>/v1-checklist.md`** (initial best-effort). Mine spec.md + the build loop for what's unverified. Retro insights merge into the Verified column later, when the deferred retro phase runs. Each item = one concrete, runnable test.

   Template (file + chat — same plain markdown):

   ```markdown
   # V1 Checklist — <Project Name>

   ## Verified in V0
   - [x] <thing that worked — from .build/validation.md PASS items>

   ## Unverified — test before /build full
   - [ ] <concrete test — e.g., "Set ANTHROPIC_API_KEY, run 3 descriptions, confirm mode: 'live'">

   ## Cut from V0 (consider for V1)
   - <item from spec.md Cut List + one-liner on why it was cut>

   _Run a few, see what breaks, then:_ `/build full <slug>`
   ```

9. **Print the rich 🐘 ship summary.** ONE message — leads with 🐘 so it visually pops. This replaces what used to be three fragmented prints (viewing block + retro invite + check-in); user-testing 2026-05-10 showed the fragmented version felt thin and missed the forward look.

   **Template (dev-server / UI / static project):**

   ```markdown
   🐘 V0 shipped — <Project Name>. Score <X.X>/5.0.

   **Run it:**
     cd {paths.projects_dir}/<slug>/<scaffold-subdir>
     <run command from CLAUDE.md>
     → http://localhost:<port>

   **What you'll see on first paint** (verified by Vera at <timestamp>):
   - <Hero metric with REAL value from step-6 paint check — e.g. "Hero: 1 build shipped">
   - <Primary list with REAL row count — e.g. "Project list: 6 rows, 1 shipped / 4 building / 1 stalled">
   - <Secondary panel — e.g. "Recent builds: 1 row from today">

   **What got built:**
   - Stack: <one-line summary>
   - Lives at: <abs path>

   **Run `/build full <slug>` next** to upgrade. Top V1 candidates:
   - **<Cut #1>** — <one-line reason this is the top V1 add>
   - **<Cut #2>** — <one-line>
   - **<Cut #3>** — <one-line>

   **Verified in V0:**
   - <2-3 concrete passes from .build/validation.md>

   **Unverified — test before /build full:**
   - <1-2 biggest unknowns from v1-checklist.md>

   Full V1 checklist → <slug>/v1-checklist.md

   When you've had a look, type `retro` and I'll ask a couple quick questions. No rush — minutes, hours, or days from now.
   ```

   **For static / CLI / API / library projects**, swap the "Run it" block to match the project shape:
   - **Static:** `open <absolute path to index.html>` (single line)
   - **CLI / API / library:** `cd {paths.projects_dir}/<slug>` + the run/entry command (e.g. `python -m app`, `./bin/cli`, `npm test`). Omit the localhost URL and "What you'll see on first paint" section; replace with **"What it does when you run it"** (parsed command output preview from step 6's CLI fallback).

   **V1 candidate ranking** (the "Top V1 candidates" section, 3 max):
   1. Items the step-6 paint check exposed as visible gaps go FIRST
   2. Then remaining spec.md Cut List items in their existing order
   3. Cap at 3 — if Cut List has fewer than 3 items, list what exists; if zero, drop the section entirely

   **If first-paint check FAILED** (and self-heal didn't recover), prepend a "Heads up" section ABOVE the "Run it" block — be honest, don't paper over:

   ```markdown
   **⚠ Heads up — first paint check did not fully pass:**
   - **What was off:** <e.g. "Hero showed 0 builds shipped; expected ≥1 (status: shipped count in frontmatter)">
   - **Why:** <diagnosis from step 6 — e.g. "telemetry write happened after dev server boot — race condition">
   - **Fix:** <concrete action the user can take — e.g. "Refresh the page; data is correct now, just stale at first paint">
   ```

   **If scoring was skipped** in Stage 3 (no OpenRouter API key, network error, judge unavailable), prepend ABOVE the 🐘 line:

   ```
   ! Scoring skipped (<one-line reason from build-state.md sub-stage>). Ran <N> validation checks: <N>/<N> PASS.
   ```

   If both scoring AND validation are missing: `! Scoring + validation both skipped — V0 ships unverified, run by hand to confirm.`

   If `run:` is missing from `CLAUDE.md`, fall back to "(no run command set — see project README)" inside the "Run it" block rather than dropping the summary entirely. The summary existing matters more than the command being perfect.

   **Voice rules:** see `vera-system/who-i-am/voice.md` "Onboarding & user-facing surfaces." Factual, observational, not performative. "V0 shipped" — not "congrats you did it!" The summary EARNS attention through detail and forward-look, not through enthusiasm.

   **Why this replaced three prints with one** (2026-05-10): the old fragmented version — viewing block + retro invite + sparse check-in — left users feeling the session "didn't do much" even when artifacts were substantive. Single rich 🐘 message with run instructions, real first-paint preview, /build full forward-look, and verified/unverified delta makes the ship moment feel like a delivery, not three loose echoes.

**Stage 4 Ship Phase ends here.** The user is now using V0. The retro phase below fires only when they signal back.

---

## Stage 4 — Retro Phase (deferred, user-triggered)

When the user later types `retro` (or any message asking about the most-recent V0 build — *"let's do the retro"*, *"I tried it"*, *"let me give you feedback on what we built"*), resume:

1. **Identify the project.** Find the most recent `build-state.md` with status `complete` across `{paths.projects_dir}/*/`. If multiple recent V0s exist (last 7 days), ask which one. Read its `spec.md`, `v1-checklist.md`, and project `CLAUDE.md` for context before firing questions.

2. **Fire the retro — AskUserQuestion:**

   ```
   AskUserQuestion(
     questions: [
       {
         question: "Did the V0 meet what you had in mind?",
         header: "Scope fit",
         options: [
           {label: "Yes, this is it", description: "This is what I wanted"},
           {label: "Close but missed something", description: "Core idea is right, details off"},
           {label: "Missed the mark", description: "Not what I was going for"}
         ]
       },
       {
         question: "How was the build process?",
         header: "Process",
         options: [
           {label: "Smooth", description: "Right speed, right decisions"},
           {label: "Too slow", description: "Too much ceremony or research"},
           {label: "Too fast", description: "Skipped things I cared about"},
           {label: "Wrong direction", description: "Had to course-correct significantly"}
         ]
       }
     ]
   )
   ```

3. **Write retro** to `{paths.projects_dir}/<slug>/retro.md`. This is what `/curate` scans for patterns across builds.

4. **Update `v1-checklist.md` with retro insights.** Move "what worked" items from retro into the Verified column. If retro surfaced new gaps, add them as Unverified items. Re-write the file.

5. **V0 → V1 user interview.** Run the structured interview about the artifact. This produces `v1-notes.md` — the user-perspective complement to `retro.md` (Vera's view) and `v1-checklist.md` (mechanical verification). `/build full` reads all three.

   **Pick ONE specific anchor** from the original session — a concrete decision Vera observed. Not generic "how was it?" Real choice: a Cut List item, the scaffold pick, a key trade-off, a Stage 2 pivot. Examples across different domains:
   - "We cut reroll and kept all 4 vibe tags. Went with streamUI over a custom rendering loop."
   - "We chose SQLite over Postgres for the data layer — no setup friction, easy local dev."

   **Print one open prompt:**

   ```
   > **V1 interview** *(optional — hit Enter to skip)*
   >
   > <anchor sentence>
   >
   > **Walk me through how you used it — and where
   > you'd hit friction first if you used it more.**

   *Just type your answer below ↓*
   ```

   **Listen, then act:**
   - **Empty response or "skip"** → log "interview declined" to `.build/decisions.log`, skip the v1-notes.md write, continue to step 6 (closing). Skip path leaves `retro.md` and `v1-checklist.md` untouched. No regression for users who skip.
   - **Substantial response** → extract silently. Do **not** echo "I heard you say X" — that breaks the flow. One optional follow-up only if friction was named without a "why" OR if the use case was vague. Otherwise close cleanly. No probing.

   **Extract to `{paths.projects_dir}/<slug>/v1-notes.md`:**

   ```markdown
   # V1 Notes — <Project Name>
   *From user interview, <YYYY-MM-DD>, real-use signal after ship.*

   ## Actual use case
   <user's words, lightly cleaned — not Vera's summary. If they said "I'd add 5 tasks for the day," write that, not "intended workflow involves task entry.">

   ## Friction (from real use)
   - <each friction the user named, in their words>
   - <next friction>

   ## V1 candidates
   - <extracted asks, ranked by friction severity. e.g., "Drag-to-reorder cards — named twice, blocks daily flow">
   - <next candidate>

   ## What surprised the user
   - <only if something stood out as better-or-worse-than-expected. Skip this section if nothing surfaced.>
   ```

6. **Spawn doc-sync as background agent** (final state captured — retro.md, v1-notes.md, updated v1-checklist.md).

7. **Print closing message:**

   ```
   Retro captured. v1-checklist.md updated with what worked.
   When you're ready to upgrade: /build full <slug>
   ```

**Frame V0 as validation, not finished product.** The goal was to prove the idea in one session. V1 starts when you have real signal on what's broken.
