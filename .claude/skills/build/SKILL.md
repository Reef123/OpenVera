---
name: build
description: "Full pipeline orchestrator. Two modes: 'new' for V0 (one user stop → autonomous build → ship), 'full' for complete SDLC. One command: idea to working product."
argument-hint: new <idea> | full <project> | continue | status
allowed-tools: Bash(python3 vera-system/scripts/*)
---

# Build — Pipeline Orchestrator

Two modes: **new** (V0 — get it working) and **full** (complete SDLC — make it good).

---

## Configuration (auto-loaded)

```!
cat vera-system/config.json
```

Use `paths.projects_dir` for project workspace (plans and research live inside each project), `llm.scoring_model` for the build score judge, `llm.default_model` for other LLM calls. Vera is portable — users point at any directory via config.json.

---

## Two Modes

**`/build new <idea>` — V0: get it working.** Ship a working V0. One pre-build phase — 2-3 short AskUserQuestion steps walking the design tree (Problem → Build path → Surface), plus an optional `/scout` recommendation if signals fire. Then autonomous to ship. The state file persists across sessions; `/build continue` resumes after context compresses or after a break. Pipeline diagrams in [build-architecture.md](build-architecture.md).

**`/build full <project>` — V1+: make it good.** Upgrading working products with real user feedback. ONE user stop (trigger + depth), then autonomous SDLC execution. **Read [full-sdlc.md](full-sdlc.md) for detailed instructions.** Do NOT load full-sdlc.md for V0 builds. Use `manifest-update.py` for MANIFEST transitions.

**How to choose:** project exists and works? NO → `new`. YES → `full`.

---

## Routing

### `new <idea-or-slug>`
1. If `{paths.projects_dir}/<slug>/` already exists (e.g., from /start-here), use it. Read `idea.md` for context. Otherwise, generate kebab-case slug and create the dir.
2. Write `CLAUDE.md` in the project root (breadcrumb for Vera + machine-readable for dashboard):
   ```markdown
   ---
   name: <Project Name>
   slug: <slug>
   status: building
   created: <YYYY-MM-DD>
   updated: <YYYY-MM-DD>
   stack: <framework + key libs>
   run: <dev server command>
   score: null
   origin: /build new
   ---
   # <Project Name>
   <one line — what this does>
   ```
3. Create state file at `{paths.projects_dir}/<slug>/build-state.md`.
4. **idea.md handoff:** If `idea.md` exists (project came from `/start-here`), read its `## What's out there` section. Real signal (scout or WebSearch output) → skip the Research question in Stage 0 — already validated. *"Not checked yet"* or `[pending]` → KEEP the Research question; user hasn't actually validated yet. **If `idea.md` doesn't exist** (direct `/build new` with no prior /start-here), don't create it now — Stage 1 step 0 synthesizes it from Stage 0 answers + the original `<idea>` argument. This guarantees idea.md is universal: spec.md can pull `## The bet` and `## Original spark` from one place regardless of entry path.
5. Begin V0 pipeline (below).

### `full <project>`
1. Verify `{paths.projects_dir}/<project>/` exists
2. Read `CLAUDE.md` in the project root for context. If missing, create one from spec.md.
3. Initialize state: `python3 vera-system/scripts/build-state.py <project> "Full Stage 0" --mode full`
4. Read existing spec.md (especially Cut List and Purpose section)
5. Begin Upgrade pipeline (below)

### `continue`
Find most recent `build-state.md` across `{paths.projects_dir}/*/`. Read it to recover: slug, mode, current stage, substage, artifacts, and decision log. If mode=new → resume V0 pipeline at the recorded stage. If mode=full → read MANIFEST.md for current phase, then read [full-sdlc.md](full-sdlc.md) and resume at that phase.

### `status`
Show all build state files. Summary table.

---

## State File

**Location:** `{paths.projects_dir}/<slug>/build-state.md` — managed by script:

```bash
python3 vera-system/scripts/build-state.py <slug> "<stage>" [--mode new|full] [--substage "desc"] [--artifact "key=path"] [--decision "text"]
```

Call at EVERY stage transition. Script validates stages, timestamps automatically, and tracks decision log.

---

## V0 Pipeline (`/build new`)

**V0 is a proof of concept.** Ship a barebones version to validate the idea works. Resumable across sessions via the state file when context compresses or you stop and come back. Not production — just enough to use it, break it, and learn what it actually needs. `/build full` is where it becomes real.

**Principles:**
- **Senior Frame first:** Before building, identify the domain. What would a 10-year expert check first?
- **Validation-first:** Start with the validation method chosen in Stage 0 (browser/command/tests). Verify after every change.
- **Scaffold then verify:** After the user picks a stack, initialize it using the stack's standard tooling (e.g., `npm create svelte@latest`, `npx create-next-app`, `mkdir + venv`). Verify the scaffold runs before writing any code.
- One component at a time. Never batch-write 40 files.

### 🐘 Vera Check-ins

Format, voice rules, and fire points (V0 + full SDLC) live in [`vera-checkins.md`](vera-checkins.md). Read it before Stage 0 so you know when to surface and how to format.

### V0 Stages 0-4 → see [`v0-stages.md`](v0-stages.md)

Stage 0 (Kickoff + Purpose), Stage 1 (Parallel Sprint), Stage 2 (Build Loop), Stage 3 (Score), Stage 4 (Ship) — full detail (AskUserQuestion blocks, spec/contract/V1-checklist templates, scoring rubric, retro flow) lives in `v0-stages.md`. Read it before starting Stage 0 and follow it stage by stage.

---

## Upgrade Pipeline (`/build full`)

**Philosophy:** The user already has a working product. They know what needs to change. One kickoff, then execute.

### 🐘 Vera Check-ins (full SDLC)

Format + fire points: see [`vera-checkins.md`](vera-checkins.md) "Full SDLC" section.

### Stage 0: Kickoff (ONE stop)

```bash
python3 vera-system/scripts/build-state.py <slug> "Full Stage 0" --substage "kickoff"
```

Read the project's existing artifacts first, in this order:

1. `idea.md` — `## The bet` (the category claim from /start-here Step 4) and `## Original spark`. The bet is what V1 should reach for — V0 may have shipped to spec but missed the bet, and the upgrade is the chance to close that gap.
2. `spec.md` — Purpose + Cut List + `## The bet` (mirrored from idea.md) from V0
3. `v1-notes.md` (if exists) — user's real-use perspective from the V0 interview. **Highest-signal input** for V1 priorities — the only artifact that captures friction in the user's own words.
4. `v1-checklist.md` (if exists) — mechanical Verified / Unverified state
5. `retro.md` (if exists) — Vera's self-retrospective on the build
6. Existing code — what actually shipped

Read in this order: bet first (ambition), spec second (intent), v1-notes third (user reality), then mechanical state, then code. The bet anchors V1 — if shipped V0 missed it, that gap is the highest-priority upgrade. Then:

```
AskUserQuestion(
  questions: [
    {
      question: "What's broken or missing? What made you run /build full instead of just using it?",
      header: "The Trigger",
      multiSelect: true,
      options: [
        // GENERATE 3-4 from v1-notes.md ## Friction FIRST (user's real-use words),
        // then fill remaining slots from spec.md Cut List. v1-notes friction
        // outranks deferred features — the user already told us what hurt.
        {label: "[Gap A — top friction from v1-notes.md, in user's words]", description: "[the friction they named, why it matters now]"},
        {label: "[Gap B — second friction OR top deferred feature]", description: "[why this is likely the trigger]"},
        {label: "[Gap C — another deferred feature from Cut List]", description: "[why now]"},
        {label: "Something else", description: "I'll tell you what needs to change."}
      ]
    },
    {
      question: "How deep should we go?",
      header: "Depth",
      options: [
        {label: "Targeted fix", description: "Add/change specific features. No full SDLC. Half a session."},
        {label: "Structured upgrade", description: "Research → plan → build phases → QA. Full SDLC. 1-2 sessions."},
        {label: "Major rework", description: "Architecture changes, new data model. Multi-session."}
      ]
    },
    {
      question: "Research?",
      header: "Research",
      options: [
        {label: "No — I know what I want", description: "Skip straight to planning."},
        {label: "Quick scout", description: "Reddit + web for gotchas on the specific thing (~2 min, free)"},
        {label: "Full research", description: "Deep dive on the upgrade domain (~15 min, ~$0.40)"}
      ]
    }
  ]
)
```

**Generate options from real context.** Source priority: `v1-notes.md ## Friction` (user's actual friction in their own words) FIRST → `spec.md` Cut List (deferred features) → `spec.md` Purpose section (what V0 promised). The friction the user named at ship time outranks anything Vera deferred — they already told us what hurt. If `v1-notes.md` is missing (skipped at ship or legacy V0), fall back to Cut List + Purpose only.

### Stage 0.5: Advisor Auto-Check (scope-depth mismatch)

After the user's kickoff answers come in, BEFORE the final review/submit screen renders, scan the combined trigger list (checkbox labels + any "Type something" free text) for new-system keywords:

`scraper, scraping, crawl, auth, authentication, oauth, persistence, database, storage layer, tenant, multi-tenant, upload, file ingest, streaming, websocket, cron, schedule, background job, new API, new integration, new input modality`

**If any keyword matches AND depth is `Targeted fix`:** auto-invoke the `/advisor` command with the current selections. The advisor agent (see `.claude/agents/advisor.md`) reads only the project artifacts — no session context — and returns either a mismatch report or "no mismatch found."

Display the advisor's output verbatim. Then let the user either revise their picks or submit as-is. Do not summarize, soften, or pre-empt the advisor.

**If no keywords match OR depth is Structured/Major:** skip the advisor. Silence is correct when there's nothing to surface.

The user can also invoke `/advisor` manually at any decision point — the slash command is always available.

### Stage 1: Autonomous Sprint

```bash
python3 vera-system/scripts/build-state.py <slug> "Full Stage 1" --substage "autonomous sprint"
```

After kickoff, everything runs with NO user stops:

**Background agents (launch simultaneously):**
1. **Doc-sync start** (always)
2. **Research/Scout** (if requested — same rule as V0: if API key is missing and full research was requested, ask before downgrading. Never silently substitute scout for research.)
3. **Domain expert analysis** (if "Structured upgrade" or "Major rework")

**Main thread — scope + plan:**

1. **Read existing project state:** spec.md, Cut List, Purpose section, existing code structure.

2. **Route by depth:**

#### Targeted Fix
Write a focused change list. Flash it to chat. Start building immediately. Browser-verify each change. Spawn validator agent after each change. Score when done. Ship.

#### Structured Upgrade
```bash
python3 vera-system/scripts/manifest-update.py <slug> init --tier structured
```
Read [full-sdlc.md](full-sdlc.md) for detailed phase instructions. Use `manifest-update.py` at each phase transition. Key rule: **SDLC phases run autonomously.** If a phase asks a question and the answer exists in an artifact (spec.md, research paper, Purpose section), answer it yourself. Only stop for decisions where the user has context you genuinely don't have. Flash each artifact to chat as it's produced. Spawn reviewer agent for Phase 6.

#### Major Rework
```bash
python3 vera-system/scripts/manifest-update.py <slug> init --tier major
```
Same as Structured but with ONE extra stop after research completes: present the architectural decisions that need resolution as an AskUserQuestion. Architecture decisions are irreversible — the user needs to weigh in. After that, proceed autonomously through SDLC.

### Stage 2: Score + Complete

1. **Score** using the same method as V0 Stage 3 (see [`v0-stages.md`](v0-stages.md) "Stage 3: Score") — read `.build/validation.md` and `.build/review.md`, call `openrouter.py` with `{llm.scoring_model}` as judge. Same calibration scale.
2. **Run the 30-second test** from spec.md. Does the upgrade actually address the Trigger from Stage 0?
3. **If score < 3.5:** Fix cascade — max 2 rounds, then complete with score noted.
   ```bash
   python3 vera-system/scripts/build-state.py <slug> "complete" --artifact "Build score=X.X/5.0"
   python3 vera-system/scripts/telemetry.py build <PASS|SOFT_FAIL> --project <slug> --score X.X --latency <seconds> --cost <usd> --note "<project> full"
   ```
4. **Spawn doc-sync as background agent.** Don't wait.
5. Update state file, report summary.
6. **Surface what's next.** Mine SDLC artifacts (PRD non-goals, Tech Spec rejected alternatives, Arch/Code Review deferred issues, Cut List, scout/research signals not acted on) for unfinished business. Output format:

   > "V1 shipped. Score: X.X. Here's what's still on the table:"
   > - **Deferred:** [2-3 specific items from Cut List / PRD with why they were cut]
   > - **Worth exploring:** [1-2 scout/research findings that weren't addressed]
   > - **Design question:** [any open decision from tech spec or arch review]
   >
   > Next moves:
   > - `/research [topic]` — [why this would help]
   > - `/build full` — [which deferred items to tackle]
   > - `/consult [decision]` — [tradeoff to think through]
   > - Or just use it. Come back when you know what's missing.

   Be specific — *"Interactive filters when you hit 10+ projects"* beats *"consider adding features."*


---

*Author: Shareef Ellis · [@shareefatwork](https://x.com/shareefatwork)*
