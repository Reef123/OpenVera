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
1. **Check for graduated slug.** If `{paths.projects_dir}/<slug>/` already exists:
   - Read its `CLAUDE.md` frontmatter `status` field.
   - `status: building` → continue at step 2 (user is resuming a half-done V0).
   - `status: shipped` or `status: live` → **refuse + route.** Print: *"`<slug>` is past V0 (`status: <X>`). Use `/build full <slug>` to do V1+ work, or manually edit CLAUDE.md `status: building` if you really want to restart V0."* Do NOT auto-execute `/build full` — the user makes the call.
   - `CLAUDE.md` missing → fall back to today's behavior: use the dir, read `idea.md` for context, continue at step 2.

   If the dir does NOT exist, generate the slug and create the project `CLAUDE.md` in one pair of calls:
   ```bash
   SLUG=$(python3 vera-system/scripts/frontmatter.py slug "<idea>")
   python3 vera-system/scripts/frontmatter.py create --slug "$SLUG" --name "<Project Name>" \
     --status building --origin "/build new" --stack "<framework + key libs>" \
     --run "<dev server command>" --summary "<one line, what this does>"
   ```
   The script writes the frontmatter block (name/slug/status/created/updated/stack/run/score/origin), the dates, and the lifecycle comment. If the stack/run aren't decided yet, omit those two flags (they default to `null`) and fill them later with `frontmatter.py set`. Continue at step 2.
2. **Status lifecycle:** `building` (V0 in active dev) → `shipped` (V0 deployed, set by Stage 4a) → `live` (past V0, in real use, set by `/build full` Phase 8 or manual edit after `/curate` flags as candidate).
3. Create state file at `{paths.projects_dir}/<slug>/build-state.md`.
4. **idea.md handoff:** If `idea.md` exists (project came from `/start-vague`), read its `## What's out there` section. Real signal (scout or WebSearch output) → skip the Research question in Stage 0 — already validated. *"Not checked yet"* or `[pending]` → KEEP the Research question; user hasn't actually validated yet. **If `idea.md` doesn't exist** (direct `/build new` with no prior /start-vague), don't create it now — Stage 1 step 0 synthesizes it from Stage 0 answers + the original `<idea>` argument. This guarantees idea.md is universal: spec.md can pull `## The bet` and `## Original spark` from one place regardless of entry path.
5. Begin V0 pipeline (below).

### `full <project>`
1. Verify `{paths.projects_dir}/<project>/` exists
2. Read `CLAUDE.md` in the project root for context. If missing, create one from spec.md.
3. Initialize state: `python3 vera-system/scripts/build-state.py <project> "Full Stage 0" --mode full`
4. Read existing spec.md (especially Cut List and Purpose section)
5. Begin Upgrade pipeline (below)

### `continue`
Find most recent `build-state.md` across `{paths.projects_dir}/*/`. Read it to recover: slug, mode, current stage, substage, artifacts, and decision log.

**Worktree detection (mode=full only).** Before resuming, run `git worktree list` and grep for `build-full-<slug>-*`:
- **Match found** — call `EnterWorktree(branch: <matched-branch>)` to re-enter. Then read MANIFEST.md (which lives inside the worktree) for current phase. This handles all `/build full` runs uniformly — Targeted, Structured, and Major — without depending on MANIFEST being readable from main.
- **No match** — either a legacy run started before worktree-by-default, or the worktree was already merged/discarded. Continue on the current branch. If `build-state.md` is on main, resume from main; if it was inside a now-discarded worktree, `build-state.md` won't be found by the glob and the project will appear absent (user should re-run `/build full <project>`).

After worktree entry (or skip), read [full-sdlc.md](full-sdlc.md) and resume at the phase recorded in MANIFEST/build-state.md. mode=new uses no worktree — resume V0 pipeline at the recorded stage directly.

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

1. **`handoff.md`** (if exists — V0→V1 contract from Stage 4b). **Read this FIRST.** Outcome, Invariants (DO NOT MODIFY), Anti-patterns, Observable behavior (what V0 demonstrably does), What V0 proved / did NOT prove, Open questions (V1 must resolve), Constraints. This is the codification of V0 evidence. Treat ## Invariants as hard constraints — do not modify without ADR. Treat ## What V0 did NOT prove as the explicit guard against codifying V0 accidents as V1 requirements.
2. `idea.md` — `## The bet` (the category claim from /start-vague Step 4) and `## Original spark`. The bet is what V1 should reach for — V0 may have shipped to spec but missed the bet, and the upgrade is the chance to close that gap.
3. `v1-notes.md` (if exists) — user's real-use perspective from the V0 interview. **Highest-signal input for V1 PRIORITIES** — friction the user actually felt outranks gaps Vera codified at ship time.
4. `spec.md` — Purpose + Cut List + `## The bet` (mirrored from idea.md) from V0
5. `v1-checklist.md` (if exists) — mechanical Verified / Unverified state
6. `retro.md` (if exists) — Vera's self-retrospective on the build
7. Existing code — what actually shipped

Read in this order: handoff first (what V0 proved + invariants), bet second (ambition), v1-notes third (user reality), spec fourth (intent + cut list), then mechanical state, then code.

**Legacy V0 fallback:** If `handoff.md` is missing (project shipped via `/build new` before Stage 4b existed), read in the old order (idea → spec → v1-notes → v1-checklist → retro → code) and treat spec.md ## Out of Scope as the closest analog to ## Open questions. Flag in MANIFEST that handoff was missing so future passes know the constraints were inferred, not codified.

Then:

```
AskUserQuestion(
  questions: [
    {
      question: "What's broken or missing? What made you run /build full instead of just using it?",
      header: "The Trigger",
      multiSelect: true,
      options: [
        // GENERATE 3-4 options. Source priority:
        //   1. v1-notes.md ## Friction (user's real-use words — highest signal)
        //   2. handoff.md ## Open questions (V0-codified V1 decisions)
        //   3. spec.md Cut List (deferred features)
        // Fill from source 1 first, then 2, then 3. User friction outranks
        // codified gaps which outrank deferred features.
        {label: "[Gap A — top friction from v1-notes.md, in user's words]", description: "[the friction they named, why it matters now]"},
        {label: "[Gap B — second friction OR top handoff.md ## Open question]", description: "[why this is likely the trigger]"},
        {label: "[Gap C — another open question OR deferred feature from Cut List]", description: "[why now]"},
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

If `v1-notes.md` is missing (skipped at ship or legacy V0), promote `handoff.md ## Open questions` to source 1. If both are missing (pre-Stage-4b legacy V0), fall back to Cut List + Purpose only.

### Stage 0.5: Advisor Auto-Check (scope-depth mismatch)

After the user's kickoff answers come in, BEFORE the final review/submit screen renders, scan the combined trigger list (checkbox labels + any "Type something" free text) for new-system keywords:

`scraper, scraping, crawl, auth, authentication, oauth, persistence, database, storage layer, tenant, multi-tenant, upload, file ingest, streaming, websocket, cron, schedule, background job, new API, new integration, new input modality`

**If any keyword matches AND depth is `Targeted fix`:** auto-invoke the `/advisor` command with the current selections. The advisor agent (see `.claude/agents/advisor.md`) reads only the project artifacts — no session context — and returns either a mismatch report or "no mismatch found."

Display the advisor's output verbatim. Then let the user either revise their picks or submit as-is. Do not summarize, soften, or pre-empt the advisor.

**If no keywords match OR depth is Structured/Major:** skip the advisor. Silence is correct when there's nothing to surface.

The user can also invoke `/advisor` manually at any decision point — the slash command is always available.

### Stage 1: Autonomous Sprint

**0. Enter worktree.** Before any agents launch:

```
EnterWorktree(branch: "build-full-<slug>-<YYYYMMDD>")
```

All Stage 1 work — SDLC artifacts, code, MANIFEST, `.build/` files, build-state.md updates from this point on — lives on this branch. Main stays clean until Stage 2 merges. The Stage 0 `build-state.md` already exists on main from the kickoff step, so `/build continue` can still find the project slug by globbing main. From the slug, `git worktree list` reveals any active `build-full-<slug>-*` branch for re-entry. If the run is abandoned mid-flight, discard the worktree; no rollback needed.

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

**0. Score first, merge after.** Stage 2 still runs inside the Stage 1 worktree. Score, run the 30-second test, and complete the fix cascade before exiting. The merge happens only after score lands and the user (or auto-pass on score ≥ 3.5) accepts the ship.

1. **Score** using the same method as V0 Stage 3 (see [`v0-stages.md`](v0-stages.md) "Stage 3: Score") — read `.build/validation.md` and `.build/review.md`, call `openrouter.py` with `{llm.scoring_model}` as judge. Same calibration scale.
2. **Run the 30-second test** from spec.md. Does the upgrade actually address the Trigger from Stage 0?
3. **If score < 3.5:** Fix cascade — max 2 rounds, then complete with score noted.
   ```bash
   python3 vera-system/scripts/build-state.py <slug> "complete" --artifact "Build score=X.X/5.0"
   python3 vera-system/scripts/telemetry.py build <PASS|SOFT_FAIL> --project <slug> --score X.X --latency <seconds> --cost <usd> --note "<project> full"
   ```
4. **Exit worktree.** Decide merge vs. preserve, then exit so subsequent doc-sync writes land on main:
   - **Score ≥ 3.5 OR user accepts ship-with-caveat** → `ExitWorktree(merge: true)`. All Stage 1/2 commits land on main as one atomic merge.
   - **Score < 3.5 AND user declines to ship** → `ExitWorktree(merge: false)`. Branch stays in `git worktree list` for `/build continue` to find on re-entry. Main stays clean.
5. **Spawn doc-sync as background agent.** Don't wait. Doc-sync writes to `conversations/`, `state.md`, and MANIFEST on main — those reflect ship state (or paused state if merge:false).
6. Update state file, report summary.
7. **Surface what's next.** Mine SDLC artifacts (PRD non-goals, Tech Spec rejected alternatives, Arch/Code Review deferred issues, Cut List, scout/research signals not acted on) for unfinished business. Output format:

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
