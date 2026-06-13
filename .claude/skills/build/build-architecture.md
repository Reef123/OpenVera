# /build Architecture

How the build pipeline works — agent topology, state flow, and artifact handoffs.

*Visual reference only. Canonical execution instructions live in `SKILL.md`, `v0-stages.md`, `phases.md`. If a diagram disagrees with those, the source files win.*

---

## V0 Pipeline (`/build new`)

```
USER                          SUPERVISOR (main thread)                    AGENTS (background)
 │                                    │                                        │
 │  /build new <idea>                 │                                        │
 │ ──────────────────────────────────>│                                        │
 │                                    │                                        │
 │                                    ├─ Routing: create dir, init state       │
 │                                    │  build-state.py <slug> "V0 Stage 0"   │
 │                                    │                                        │
 │  ┌─────────────────────────────────┤                                        │
 │  │ STAGE 0 — DESIGN-TREE WALK      │                                        │
 │  │                                  │                                        │
 │  │ Step 1 — Problem (4 Qs):        │                                        │
 │  │   • The Job                     │                                        │
 │  │   • The Pain It Kills           │                                        │
 │  │   • 30-Second Test              │                                        │
 │  │   • Research depth (No/Scout/   │                                        │
 │  │     Research)                   │                                        │
 │  │                                  │                                        │
 │  │ ↓ [Scout gate — signal-driven  │                                        │
 │  │   plain-text recommendation,    │                                        │
 │  │   fires only if user said No   │                                        │
 │  │   AND signals warrant /scout]   │                                        │
 │  │                                  │                                        │
 │  │ Step 2 — Build path (3-4 Qs):  │                                        │
 │  │   • Shape (UI / UI+data / API)  │                                        │
 │  │   • Stack (ordered by Shape)    │                                        │
 │  │   • Validation (ordered by      │                                        │
 │  │     Stack)                      │                                        │
 │  │   • Build vs Use (if scout ran) │                                        │
 │  │                                  │                                        │
 │  │ Step 3 — Surface (1 Q):         │                                        │
 │  │   • Must-have action            │                                        │
 │  │     (options informed by Shape) │                                        │
 │  └────────────────────────────────>│                                        │
 │                                    │                                        │
 │                                    ├─ build-state.py "V0 Stage 1"          │
 │                                    │                                        │
 │  NO MORE STOPS                     │  ┌─── PARALLEL FAN-OUT ──────────────┐│
 │  ═══════════════                   │  │                                    ││
 │                                    │  │  Agent: doc-sync ──────────────────>│ (sonnet, bg)
 │                                    │  │  Agent: scout/research ────────────>│ (bg, if requested)
 │                                    │  │  Agent: framework picker ──────────>│ (bg, if "help me choose")
 │                                    │  │                                    ││
 │                                    │  │  MAIN THREAD (sequential):         ││
 │                                    │  │  ├─ 1. Domain experts (2 min)      ││
 │                                    │  │  ├─ 2. Scope guard (2 min)         ││
 │                                    │  │  ├─ 3. Spec → spec.md              ││
 │                                    │  │  │     (mood signals + components) ││
 │                                    │  │  └─ 4. /frame --quick --from-spec  ││
 │                                    │  │       → arch.md, DESIGN.md         ││
 │                                    │  │       (palette picked from         ││
 │                                    │  │        rotation set), wireframes   ││
 │                                    │  │                                    ││
 │                                    │  │  ← sync: wait for bg agents       ││
 │                                    │  │  incorporate findings into spec     ││
 │                                    │  └────────────────────────────────────┘│
 │                                    │                                        │
 │  (spec flashed to chat)            │  "Building now. Interrupt if wrong."   │
 │                                    │                                        │
 │                                    ├─ SCAFFOLD + VERIFY                     │
 │                                    │  npm create svelte@latest / etc.       │
 │                                    │  start dev server, verify loads        │
 │                                    │  build-state.py "V0 Stage 1"          │
 │                                    │    --substage "scaffold verified"      │
 │                                    │                                        │
 │                                    ├─ build-state.py "V0 Stage 2"          │
 │                                    │                                        │
 │                                    │  ┌─── BUILD LOOP ────────────────────┐│
 │                                    │  │                                    ││
 │                                    │  │  for each component in spec:       ││
 │                                    │  │    │                               ││
 │                                    │  │    ├─ SUPERVISOR writes code        ││
 │                                    │  │    │  (one component at a time)     ││
 │                                    │  │    │                               ││
 │                                    │  │    ├─ Agent: validator ────────────>│ (sonnet)
 │                                    │  │    │  "Validate {path} using        ││
 │                                    │  │    │   {method}. Check {component}" ││
 │                                    │  │    │  → .build/validation.md        ││
 │                                    │  │    │                               ││
 │                                    │  │    ├─ FAIL? fix → re-validate      ││
 │                                    │  │    └─ PASS? next component          ││
 │                                    │  │                                    ││
 │                                    │  │  after core flow complete:          ││
 │                                    │  │    │                               ││
 │                                    │  │    └─ Agent: reviewer ─────────────>│ (sonnet)
 │                                    │  │       "Review {path}. Spec: {spec}" ││
 │                                    │  │       → .build/review.md            ││
 │                                    │  │                                    ││
 │                                    │  │  fix Critical/High findings         ││
 │                                    │  └────────────────────────────────────┘│
 │                                    │                                        │
 │                                    ├─ build-state.py "V0 Stage 3"          │
 │                                    │                                        │
 │                                    ├─ SCORE                                 │
 │                                    │  read .build/validation.md             │
 │                                    │  read .build/review.md                 │
 │                                    │  openrouter.py → external judge        │
 │                                    │  telemetry.py build PASS               │
 │                                    │                                        │
 │                                    │  >= 3.5 → ship                         │
 │                                    │  <  3.5 → fix (max 2 rounds)           │
 │                                    │                                        │
 │                                    ├─ build-state.py "complete"             │
 │                                    │                                        │
 │                                    │  STAGE 4a/4b SHIP                      │
 │                                    │  (rich 🐘 ship summary + handoff.md   │
 │                                    │   contract — see v0-stages.md)         │
 │                                    │     Agent: doc-sync ──────────────────>│ (bg)
 │                                    │                                        │
 │  user uses V0, types `retro` ──────│                                        │
 │                                    │                                        │
 │  ┌─────────────────────────────────┤  RETRO PHASE (deferred)               │
 │  │ AskUserQuestion (retro)         │                                        │
 │  │  • Scope fit                    │                                        │
 │  │  • Process feedback             │                                        │
 │  └────────────────────────────────>│                                        │
 │                                    │  → retro.md                            │
 │                                    │  → v1-notes.md (V0→V1 interview)      │
 │                                    │  → v1-checklist.md (updated)          │
 │                                    │  Agent: doc-sync ──────────────────────>│ (sonnet, bg)
 │                                    │  "Retro captured. /build full <slug>." │
 │                                    │                                        │
```

---

## Full SDLC Pipeline (`/build full`)

```
USER                          SUPERVISOR (main thread)                    AGENTS
 │                                    │                                        │
 │  /build full <project>             │                                        │
 │ ──────────────────────────────────>│                                        │
 │                                    ├─ build-state.py "Full Stage 0"        │
 │                                    │  read kickoff sources (see SKILL.md)   │
 │                                    │                                        │
 │  ┌─────────────────────────────────┤                                        │
 │  │ AskUserQuestion (ONE stop)      │                                        │
 │  │  • The Trigger (from Cut List)  │                                        │
 │  │  • Depth (targeted/struct/major)│                                        │
 │  │  • Research?                    │                                        │
 │  └────────────────────────────────>│                                        │
 │                                    │                                        │
 │                                    ├─ EnterWorktree("build-full-<slug>-...") │
 │                                    │  all Stage 1/2 work runs on branch     │
 │                                    │  main stays clean until ExitWorktree   │
 │                                    │                                        │
 │                                    ├─ build-state.py "Full Stage 1"        │
 │                                    │  (writes inside worktree from here on) │
 │                                    │                                        │
 │  NO MORE STOPS                     │  ┌─── PARALLEL FAN-OUT ──────────────┐│
 │  (except Major arch decision)      │  │  Agent: doc-sync ─────────────────>│ (bg)
 │                                    │  │  Agent: scout/research ───────────>│ (bg, if req)
 │                                    │  │  Agent: domain experts ───────────>│ (bg, if struct/major)
 │                                    │  └────────────────────────────────────┘│
 │                                    │                                        │
 │                                    ├─ ROUTE BY DEPTH                        │
 │                                    │                                        │
 │                          ┌─────────┼─────────┬──────────────────┐           │
 │                          │         │         │                  │           │
 │                          ▼         │         ▼                  ▼           │
 │                     TARGETED       │    STRUCTURED          MAJOR           │
 │                     ─────────      │    ──────────          ─────           │
 │                     change list    │    manifest init       manifest init   │
 │                     build+validate │         │              research wait   │
 │                     score+ship     │         │                  │           │
 │                                    │         │    ┌─────────────┤           │
 │                                    │         │    │ AskUser:    │           │
 │                                    │         │    │ arch choice │           │
 │                                    │         │    └────────────>│           │
 │                                    │         │                  │           │
 │                                    │         ▼                  ▼           │
 │                                    │    ┌──────────────────────────┐        │
 │                                    │    │   SDLC PHASES           │        │
 │                                    │    │                          │        │
 │                                    │    │   P1: PRD agent          │        │
 │                                    │    │     manifest phase-start │        │
 │                                    │    │     manifest phase-done  │        │
 │                                    │    │         ↓                │        │
 │                                    │    │   P2: Tech Spec          │        │
 │                                    │    │     + arch diagram       │        │
 │                                    │    │         ↓                │        │
 │                                    │    │   P3: Arch Review        │        │
 │                                    │    │         ↓                │        │
 │                                    │    │   P4: Phase Plan         │        │
 │                                    │    │     + UI wireframes      │        │
 │                                    │    │     + DESIGN.md          │        │
 │                                    │    │         ↓                │        │
 │                                    │    │   for each build phase:  │        │
 │                                    │    │   ┌─────────────────┐    │        │
 │                                    │    │   │ P5: Build N     │    │        │
 │                                    │    │   │  (main writes)  │    │        │
 │                                    │    │   │  validator ─────│───────────>│ (sonnet)
 │                                    │    │   │       ↓         │    │        │
 │                                    │    │   │ P6: Review N    │    │        │
 │                                    │    │   │  reviewer ──────│───────────>│ (sonnet)
 │                                    │    │   │       ↓         │    │        │
 │                                    │    │   │ manifest update │    │        │
 │                                    │    │   └─────────────────┘    │        │
 │                                    │    │         ↓                │        │
 │                                    │    │   P6.5: Simplification   │        │
 │                                    │    │         ↓                │        │
 │                                    │    │   P6.7: Security (OWASP) │        │
 │                                    │    │    reviewer ─────────────│───────>│ (sonnet)
 │                                    │    │         ↓                │        │
 │                                    │    │   P7: QA                 │        │
 │                                    │    │         ↓                │        │
 │                                    │    │   P8: Ship               │        │
 │                                    │    └──────────────────────────┘        │
 │                                    │                                        │
 │                                    ├─ SCORE (same as V0)                    │
 │                                    │  build-state.py "complete"             │
 │                                    │  telemetry.py build PASS               │
 │                                    │                                        │
 │                                    ├─ ExitWorktree(keep), then git merge    │
 │                                    │  score ≥ 3.5 or ship-accepted → merge  │
 │                                    │  declined → keep branch for review     │
 │                                    │                                        │
 │                                    ├─ SURFACE WHAT'S NEXT                   │
 │                                    │  (mine PRD, Cut List, research)        │
 │                                    │  Agent: doc-sync ──────────────────────>│ (bg)
 │                                    │                                        │
```

---

## Agent Topology

```
                    ┌─────────────────────────┐
                    │   /build (supervisor)    │
                    │   role: orchestrator     │
                    │   owns: state, routing,  │
                    │   user stops, sequencing │
                    └────────┬────────────────┘
                             │
            ┌────────────────┼────────────────┬──────────────────┐
            │                │                │                  │
            ▼                ▼                ▼                  ▼
   ┌────────────────┐ ┌────────────┐ ┌──────────────┐ ┌──────────────┐
   │ doc-sync       │ │ scout      │ │ validator    │ │ reviewer     │
   │ role: docs     │ │ role: recon│ │ role: test   │ │ role: review │
   │ when: start,   │ │ when: if   │ │ when: after  │ │ when: after  │
   │       end      │ │ requested  │ │ each build   │ │ core flow or │
   │ bg: always     │ │ bg: always │ │ component    │ │ each phase   │
   └────────────────┘ └────────────┘ │ writes to:   │ │ writes to:   │
                                     │ .build/      │ │ .build/      │
                                     │ validation.md│ │ review.md    │
                                     └──────────────┘ └──────────────┘
```

---

## Canonical Project Folder

Every `/build` output lands under `{paths.projects_dir}/<slug>/`. Never at the repo root. Never mixed with harness files in `vera-system/`.

```
vera-projects/projects/<slug>/
├── CLAUDE.md               # frontmatter: name, slug, status, stack, run, score
├── build-state.md          # state machine (build-state.py only)
├── idea.md                 # universal — /start-vague OR synthesized at Stage 1 step 0
├── spec.md                 # V0 spec
├── arch.md, wireframes.md, DESIGN.md
├── retro.md, v1-checklist.md
│
├── .build/                 # V0 ephemeral — overwritten each cycle
│   ├── contract.md, validation.md, review.md
│   └── screenshots/        # Playwright captures
│
├── plans/                  # V1+ durable SDLC artifacts
│   ├── MANIFEST.md         # PRD reqs ↔ phases ↔ files
│   ├── 01-PRD.md, 02-TECH-SPEC.md, 03-ARCH-REVIEW.md
│   ├── 04-PHASE-PLAN.md, 05-QA-REPORT.md, 06-SHIP-LOG.md
│   └── build/              # phase-N-spec.md + phase-N-review.md per phase
│
├── research/               # /research output routed here when project active
│
└── <scaffolded code>/      # npm create / npx create-next-app / etc.
```

**Two build-artifact conventions, on purpose:**
- `.build/` is **ephemeral** — overwritten every loop, hidden like any build output, not part of the durable record.
- `plans/build/` is **durable** — each SDLC phase gets its own numbered spec + review, committed for audit.

**Harness-level (stays at `vera-system/`, never per-project):** state.md, ROADMAP.md, ideas.md, memory/, conversations/, runs/\*.tsv. Cross-project analytics + global state live here by design.

**Standalone research** (no project context) routes to `{paths.research_output_dir}/<topic>-research.md` instead of a project's `research/`.

---

## State Transitions (build-state.py)

```
V0:     "V0 Stage 0" → "V0 Stage 1" → "V0 Stage 2" → "V0 Stage 3" → "V0 Stage 4" → "complete"
Full:   "Full Stage 0" → "Full Stage 1" → "Phase 1" → "Phase 2" → ... → "Phase 8" → "complete"

Each transition: python3 vera-system/scripts/build-state.py <slug> "<stage>" [--substage "..."]
```

---

## Scripts

| Script | Purpose | Called by |
|--------|---------|----------|
| `build-state.py` | State transitions, decision log, artifacts | Every stage boundary |
| `frontmatter.py` | Slug gen + project `CLAUDE.md` frontmatter (create / set status,score,updated) | V0 step 1 create, Stage 4a ship; Full Phase 8 |
| `manifest-update.py` | MANIFEST.md for Full SDLC (init, phase-start, phase-complete, build-phase, complete) | Structured/Major routes |
| `palette-pick.py` | Deterministic palette pick + `:root` token block | Stage 2 styling (DESIGN.md thin/missing) |
| `telemetry.py` | Log build outcome, score, cost, latency | After scoring |
| `openrouter.py` | External judge scoring | Stage 3 |
