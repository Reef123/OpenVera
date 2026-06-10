 # 🐘 OpenVera

<p align="center">
  <em>A personal AI workbench that remembers your ideas, researches the space, builds a V0, captures lessons, and carries context forward to v1+.</em>
</p>

<p align="center">
  <em>Vague idea → researched → shipped → remembered</em>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License"></a>
  <img src="https://img.shields.io/badge/Claude_Code-required-purple.svg" alt="Claude Code">
  <img src="https://img.shields.io/badge/Setup-5_min-blue.svg" alt="Setup">
</p>

<p align="center">
  <a href="https://openvera.ai"><strong>openvera.ai</strong></a>
</p>

---

OpenVera is a harness for Claude Code: files, skills, hooks, and scripts that wrap the model so your work compounds.

Most AI coding setups forget everything between sessions. You re-explain context, lose the thread, start cold. OpenVera keeps your work in files on disk: state, decisions, patterns, lessons. Session fifty starts where session one left off, and knows things session one didn't.

It researches before it builds, pushes back before you commit, and writes down what it learns before it lets a session end. The whole loop runs on plain files you can read, grep, and edit.

Two ways in, depending on where you are:

- **`/start-vague`** when the idea isn't sharp yet. It asks a few questions, scouts for tools that already exist, and hands off something you can build.
- **`/build new`** when you can name it in a sentence. A few scoping questions, then it runs on its own: design, build loop, first-paint check, ship summary in ~10-20 min.

## Get Started

API keys are optional. The harness, most skills, and the whole memory loop run on your existing Claude Code subscription; keys add deep research, Reddit and YouTube depth in `/scout`, and an external scoring gate ([details below](#keys-are-optional)).

**One-liner.** Clones into `./openvera`, then runs the interactive bootstrap:

```bash
curl -fsSL https://raw.githubusercontent.com/Reef123/OpenVera/main/install.sh | bash
```

(Append `-s -- ~/some/path` to choose where it lands.)

**Or manual** (if you'd rather inspect the [`install.sh`](install.sh) first, which is recommended):

```bash
git clone https://github.com/Reef123/OpenVera.git openvera
cd openvera
./bootstrap.sh
```

Either way, the bootstrap asks your name and optional API keys, fills in the templates, and runs a health check. At the end it offers to open Claude Code for you, so just press Enter. Once you're in, Claude boots into OpenVera automatically whenever you open this folder.

## Your First Ten Minutes

Here's the shape of a first session (illustrative: your questions, timings, and project will differ):

```text
$ claude

  🐘 OpenVera online. Harness healthy.
  First build: /start-vague (vague idea) or /build new <idea> (clear one)

> /build new a price-per-serving calculator for my recipes

  A few scoping questions, one at a time:
    Who is this for, just you or others too?       → just me
    What's the ONE action that has to work?        → paste ingredients, see cost per serving
  (and a quick pressure-test if your answers leave a risky assumption)

  Then it runs on its own: scope guard (trims to one problem) →
  design tokens → build loop (pass 1 failed the paste handler;
  pass 2 fixed it) → browser first-paint check

  🐘 Shipped: vera-projects/projects/recipe-cost/
     Run it:   cd vera-projects/projects/recipe-cost && npm run dev
     Verified: paste → cost renders in browser
     V1 candidates ranked in handoff.md

> /doc-sync

  state.md updated, session logged to conversations/001-….md
  lesson captured: - 2026-06-10 [build/recipe-cost] textarea paste
    events need explicit handling in Svelte 5
  Safe to close.
```

That last step is not optional politeness. If you try to end a session with unsynced work, a hook blocks it once and points you at `/doc-sync`. That's the harness enforcing its own loop, which is the whole idea:

## The Loop

<p align="center">
  <img src="assets/the-loop.png" alt="The harness loop: BUILD produces work, CAPTURE is forced (a session can't end until lessons are written back), CURATE is judged (only what recurs survives), PROMOTE turns lessons into patterns and patterns into code" width="860">
</p>

Most agent loops automate. Few learn. The difference is whether each cycle changes the loop itself. OpenVera's loop has four organs, and each one is mechanical, not a promise:

- **Capture is forced.** Build failures and course corrections append one dated line to `memory/lessons.md` (`- 2026-06-09 [build/recipe-cost] Vite dev server caches .env, restart after key changes`). A Stop hook blocks the session from ending while harness state is unsynced. There's no quota: zero lessons is a valid session. The gate forces the write-back of state, never the production of wisdom.
- **Curation is judged.** `/curate` runs weekly (`/doc-sync` spawns it in the background when it's overdue) and prunes the lesson lane: one-offs age out, and anything that recurs 3+ times gets flagged for promotion into `patterns.md`. You approve promotions; the machine never edits your patterns file.
- **Promotion is verified.** Every promotion lands in a ledger (`memory/promotions.tsv`). If the lesson stays gone for 14 days, the pattern is validated. If it recurs, the promotion is marked FAILED and flagged as a candidate for mechanical enforcement: a hook, a doctor check, a script gate. Prose that doesn't work graduates into code that does.
- **The loop is measured.** `loop-report.py` answers the question a harness should be able to answer about itself: what does cycle fifty know that cycle one didn't? The report's headline (it also breaks activity down per skill and keeps a trend file):

```text
**Loop report 2026-06-10.** Since cycle 1 the loop has captured 31 lessons
(9 in the last 30 days), promoted 4 into patterns (3 validated, 1 failed),
and run 22 skill invocations in the last 30 days (86% pass).
```

This loop also polices its own quality. When a skill underperforms, `/improve` runs it against tests, scores the output, proposes one change to the skill's own instructions, and re-runs everything to check for regressions before you accept.

Models get replaced. The harness gets smarter.

## Before Code: Research and Pushback

The write-back side is only half the harness. The same skepticism runs upstream, before any code exists, and what it finds feeds the same files the loop learns from:

**It researches before it builds.** `/scout` is a 2-3 minute recon (~$0.10): Reddit and YouTube for what real people hit. `/research` goes deep (~$0.50): 8 steps, multiple models so one model's blind spots get caught, a source registry so claims are checkable. Either way, external findings stay untrusted: extract the technique, verify packages and env vars before you adopt.

**Something that isn't you pushes back.** `/panel` reviews your plan for blind spots before `/build`. Validator and reviewer agents check the code as it's built. A separate model scores the result. A scope guard cuts a V0 to 1-2 problems, because a finished V0 that solves one problem is worth more than a spec for V3 that never gets built.

## Why It's Built This Way

A few decisions that shape everything else:

- **Files over chat.** State, memory, and patterns live as files on disk, not in the conversation. If it's not in a file, it doesn't survive a reboot.
- **Files over a database.** Plain markdown and TSV instead of a vector store: you can read every memory, grep it, edit it, diff it, and carry it anywhere. At personal scale, inspectability beats retrieval cleverness. (If that stops being true, the files are still the export format.)
- **Three-tier context.** Core (~300 lines) loads every session. Recall loads on demand. Archival is search-only. The context window doesn't fill up with things that aren't relevant right now.
- **Skills load lazy.** Each skill sits in the system prompt as just its name and a one-line description. The full instructions load only when you invoke `/<command>`. You can keep 50 skills on hand and pay the token cost for the one you actually run.
- **Enforcement over discipline.** Anything the loop depends on (doc-sync at session end, memory size caps, promotion checks) is a hook or a script, not a reminder. Habits decay; gates don't.

## What's In Here

### Boot Sequence

When Claude opens this workspace, `CLAUDE.md` loads context in three tiers:

<p align="center">
  <img src="assets/boot-sequence.png" alt="Three-tier context loading: Core loads every session, Recall loads on demand, Archival is search-only" width="860">
</p>

### Memory

```
memory/
  patterns.md     <- decision frameworks (you curate these; the machine never edits them)
  lessons.md      <- machine lane: one dated line per failure or correction (created at bootstrap)
  promotions.tsv  <- ledger proving which promoted lessons stopped recurring (created on first promotion)
  MEMORY.md       <- index of things Claude has learned (maintained and pruned by /curate)
```

`MEMORY.md` and `lessons.md` grow automatically; `/curate` prunes them weekly so they hold signal, not sediment. Size caps live in code: the doctor flags any memory file that outgrows what Claude can actually load, because oversized memory silently truncates, and a memory that truncates is a memory that lies. `patterns.md` is yours: rules like "when I get excited about a feature, check for scope creep" that fire as guardrails during real work.

### Conversation History

Every session writes a snapshot to `vera-system/conversations/NNN-YYYY-MM-DD.md`:

- Triggered by `/doc-sync` (run it manually, or get nudged when a session is ending with unsynced work)
- Captures session summary, course corrections, files changed, state at end
- Logs are gitignored, so they stay local to your machine and never get pushed

### Skills

Slash commands that do real things. Their full instructions load only when invoked; until then each is one line in the system prompt. Three layers: entry points, building blocks, and meta.

<p align="center">
  <img src="assets/skills-map.png" alt="OpenVera skills map: entry points (start-vague, build new, build full), building blocks (scout, research, consult, frame, wireframe-first, panel, advisor, code-review), and meta (improve, curate, doc-sync), all over a shared state substrate" width="860">
</p>

Costs below are typical USD ranges per invocation. Paid skills spend on OpenRouter model calls; free skills run through your existing Claude Code subscription.

| Command | What It Does | Cost (USD) |
|---------|--------------|------|
| `/start-vague` | Takes a vague idea and turns it into something buildable | Free |
| `/scout <question>` | Quick research: Reddit, YouTube, web. 2-3 minutes. | $0.00–0.10 |
| `/research <topic>` | Deep multi-model research. 8 steps, source registry, paper output. | $0.15–0.55 |
| `/consult <decision>` | Simulates a panel of domain experts, gives you one recommendation | Free |
| `/frame` | Generates a design system, architecture diagrams, wireframes | Free |
| `/wireframe-first` | Sketches one screen in plain text and gets your sign-off before any code | Free |
| `/panel [path]` | Pressure-test your idea before `/build`. 2 domain reviewers (read-only, clean-context) scan for blind spots: what's stated, missing, assumed. | Free |
| `/advisor [decision]` | Checks a decision against project artifacts, reports mismatches. Auto-fires on scope/depth mismatch in `/build full` Stage 0. | Free |
| `/code-review [path]` | Clean-context reviewer scans a path or diff, returns tiered findings | Free |
| `/build new <idea>` | V0: idea to working app (resumable across sessions via state file) | ~$0.12 (scoring) |
| `/build full <project>` | Full SDLC: PRD, tech spec, arch review, phased builds, QA | Varies (research + scoring) |
| `/improve <skill>` | Runs a skill, scores the output, proposes instruction fixes, verifies no regressions | ~$0.20–0.40 / cycle |
| `/curate` | Weekly memory consolidation: prunes, merges, verifies promotions | Free |
| `/doc-sync` | Updates state file, conversation log, roadmap, lesson capture | Free |

### Hooks

These run mechanically, not by asking Claude to remember. Six files in `.claude/hooks/`:

- **`session-start.py`** runs a boot health check (bootstrap state, config validity, `/curate` freshness), then prints one status line plus a rotating tip
- **`mark-dirty.py`** fires after any harness-file write and flags the session as having unsaved work
- **`pre-compact.py`** blocks context compression while the session has unsaved work, until you run `/doc-sync`
- **`post-compact.py`** re-injects state, patterns, memory index, and your context after compression, so Claude doesn't lose the thread
- **`session-end-reminder.py`** detects "wrapping up" language and arms the session-ending marker
- **`stop-doc-sync-gate.py`** blocks a session from ending with unsynced harness edits: one clear nag pointing at `/doc-sync`, never a trap

All deterministic Python, wired in `.claude/settings.json`, readable in one sitting.

## Two Ways to Build

<p align="center">
  <img src="assets/build-journey.png" alt="V0 vibe codes a working app; V1+ runs full SDLC across multiple sessions" width="860">
</p>

Both start from an idea. If yours is still vague, run `/start-vague` first. It shapes a rough idea into a buildable `idea.md`, then hands it to `/build new`.

### V0: Just Build It (`/build new`)

You have an idea you can describe in a sentence. `/build new` runs the whole pipeline (the one in the walkthrough above): scoping questions, scope guard, design tokens, then a build loop until it works in the browser. The state file persists across sessions, so when context compresses or you stop for the night, `/build continue` picks up exactly where you left off.

### V1+: Full SDLC (`/build full`)

Your V0 works and you want to make it real. `/build full` runs the whole thing: deep research, gap analysis, PRD, tech spec, architecture review, phased builds with tests, code review, QA. This takes multiple sessions. Context is handed off through files, not memory.

Don't start here. Start with V0. If it's worth investing in, you'll know.

## Structure

```
openvera/                          <- you open this in Claude Code
├── CLAUDE.md                      <- points Claude to vera-system/
├── bootstrap.sh                   <- first-time setup
│
├── .claude/                       <- Claude Code reads this at project root
│   ├── settings.json              <- permissions + hooks
│   ├── rules/                     <- safety guardrails
│   ├── hooks/                     <- automation scripts
│   ├── agents/                    <- subagent definitions
│   ├── commands/                  <- slash commands
│   └── skills/                    <- skill definitions
│
├── vera-system/                   <- the harness content
│   ├── CLAUDE.md                  <- boot sequence + rules
│   ├── state.md                   <- where things are right now
│   ├── ROADMAP.md                 <- what's next
│   ├── ideas.md                   <- idea capture
│   ├── config.json                <- paths + model defaults
│   ├── who-i-am/                  <- identity + voice
│   ├── relationships/             <- context about you
│   ├── memory/                    <- patterns, lessons, promotions ledger
│   ├── scripts/                   <- helper scripts (research, telemetry, loop report, doctor)
│   ├── runs/                      <- local telemetry + loop trend (gitignored)
│   └── conversations/             <- session logs
│
└── vera-projects/                 <- output goes here
    ├── projects/                  <- one folder per project
    └── research-output/           <- standalone research papers
```

## Make It Yours

After bootstrap, edit these:

- **`vera-system/who-i-am/voice.md`** sets the tone (direct, casual, formal, whatever you want)
- **`vera-system/relationships/user.md`** is who you are, so Claude can tailor responses
- **`vera-system/memory/patterns.md`** ships with baseline patterns; add your own as you discover them

To add a skill, create `.claude/skills/<name>/SKILL.md` with YAML frontmatter (name + description) and instructions in the body.

To change paths or the default LLM model, edit `vera-system/config.json`.

## What OpenVera Won't Do

Boundaries are enforced in `.claude/settings.json` and the hooks, not promised in prose. Audit them yourself:

- **Won't run `sudo` or `rm -rf`.** Denied outright in permissions.
- **Won't read your secrets.** `.env` files, SSH keys, and cloud credentials are denied outright; `.secrets` requires your explicit approval each time.
- **Won't force-push, hard-reset, or kill processes without asking.** All on the ask list.
- **Won't push anywhere.** Nothing in the harness runs `git push`. Commits stay local until you push them yourself.
- **Won't edit your patterns.** `patterns.md` is hand-curated by rule; the machine lane is separate files.
- **Won't phone home.** After install, no network calls happen on their own. The only scripts that touch the network are `openrouter.py` and `youtube-analyze.py`, and only when a skill you invoked calls them. Run logs stay local in `vera-system/runs/`.

## Keys are Optional

**Works without keys:**
`/start-vague`, `/consult`, `/frame`, `/wireframe-first`, `/panel`, `/advisor`, `/code-review`, `/curate`, `/doc-sync`, and the whole memory loop. `/scout` covers web search with no key (Reddit falls back to lower-fidelity snippets). `/build` ships fine, just unscored: the external judge is skipped, you still get the validator and reviewer agents.

**What needs a key:**
- `/scout`: Reddit and YouTube depth run through OpenRouter. Video analysis needs a Google AI key.
- `/research` and `/improve` need OpenRouter for their multi-model calls.
- `/build`'s external scoring gate needs OpenRouter.

Install-time exceptions: `git clone` pulls the repo, `pip install` fetches Python deps, and if you paste an API key into bootstrap it gets verified with a one-shot call (OpenRouter `GET /auth/key`, Google AI `GET /v1beta/models`). Skip the prompts to skip the calls.

Try OpenVera for a session. Decide if you trust it. Add keys later if you want the scoring gate or deep research.

When you do:
```bash
cp vera-system/.secrets.template vera-system/.secrets
chmod 600 vera-system/.secrets
# edit vera-system/.secrets
```

The `.secrets` file is gitignored and chmod 600. Permissions require Claude to ask before reading it.

## Recommended MCPs

OpenVera's skills work without these, but two MCPs noticeably help:

| MCP | What It Adds | Install |
|-----|-------------|---------|
| **Playwright** | `/build` verifies your app in a real browser instead of jsdom. Catches bugs that pass unit tests. | `claude mcp add playwright -- npx @playwright/mcp@latest` |
| **Context7** | Up-to-date library docs injected into `/research` and `/build`. Prevents Claude from using stale training data for fast-moving libraries. | `claude mcp add context7 -- npx -y @upstash/context7-mcp` |

Run each once. They stick across projects.

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI
- Python 3.8+
- Windows: run bootstrap via Git Bash or WSL (not cmd.exe or PowerShell directly)
- Optional: [OpenRouter](https://openrouter.ai) key (multi-model research)
- Optional: [Google AI](https://aistudio.google.com/apikey) key (YouTube analysis in /scout)

## When Things Break

See [RECOVERY.md](RECOVERY.md), a short guide for hook errors, missing skills, broken bootstrap, doctor warnings.

## License

MIT. See [LICENSE](LICENSE).

Built by [Shareef Ellis](https://x.com/shareefatwork). Changelog updates on [@openveraai](https://x.com/openveraai). Inspirations in [THANKS.md](THANKS.md).
