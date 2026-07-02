 # 🐘 OpenVera

<p align="center">
  <em>A personal AI workbench that remembers your context, researches before building, ships a prototype, and reviews its own code. Work carries forward instead of starting over.</em>
</p>

<p align="center">
  <em>Idea → researched → shipped → remembered. In one session or many.</em>
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

OpenVera is a harness for [Claude Code](https://docs.anthropic.com/en/docs/claude-code): files, skills, hooks, and scripts that wrap the model so a project picks up where you left it, session after session.

It runs the whole arc, not just one trick: it remembers your context between sessions, researches the space before it writes code, ships a working prototype, reviews what it built, and carries the lessons into the next run. Most AI coding setups forget everything between sessions; OpenVera keeps state, decisions, patterns, and lessons in plain files on disk, so session fifty starts where session one left off. The whole loop runs on files you can read, grep, and edit.

Every session opens with what moved and what's next: a cockpit view of recent momentum, the next action per open thread, and anything genuinely blocked on you, so you never open a project cold. A running `inbox.md` catches whatever you paste in mid-thought; the next session routes it to an idea, a roadmap item, or the trash instead of it disappearing into scrollback.

## Get Started

```bash
curl -fsSL https://raw.githubusercontent.com/Reef123/OpenVera/main/install.sh | bash
```

Clones into `./openvera` and runs the interactive bootstrap. (Append `-s -- ~/some/path` to choose where it lands.) Prefer to inspect first? Clone and run `./bootstrap.sh` by hand:

```bash
git clone https://github.com/Reef123/OpenVera.git openvera
cd openvera
./bootstrap.sh
```

Either way, bootstrap asks your name and optional API keys, fills the templates, and runs a health check. At the end it offers to open Claude Code, so just press Enter. Once you're in, Claude boots into OpenVera automatically whenever you open the `openvera/` folder. API keys are optional: the harness, most skills, and the whole memory loop run on your existing Claude Code subscription; keys add deep research, `/scout` depth, and an external scoring gate ([details](#keys-are-optional)).

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

That last step is not optional politeness. If you try to end a session with unsynced work, a hook blocks it once and points you at `/doc-sync`. That's the harness enforcing its own loop, which is the whole idea.

## The Loop

<p align="center">
  <img src="assets/the-loop.png" alt="The harness loop: BUILD produces work, CAPTURE is forced (a session can't end until lessons are written back), CURATE is judged (only what recurs survives), PROMOTE turns lessons into patterns and patterns into code" width="860">
</p>

Most agent loops automate. Few learn. The difference is whether each cycle changes the loop itself. OpenVera's loop has four organs, and each one is mechanical, not a promise:

- **Capture is forced.** Failures and course corrections append one dated line to `memory/lessons.md`. A Stop hook blocks a session from ending while harness state is unsynced. Zero lessons is a valid session: the gate forces write-back, never wisdom.
- **Curation is judged.** `/curate` runs weekly: one-offs age out, and anything that recurs 3+ times gets flagged for promotion into `patterns.md`. You approve; the machine never edits your patterns file.
- **Promotion is verified.** Every promotion lands in `memory/promotions.tsv`. Gone for 14 days: validated. Recurs: marked failed and flagged for mechanical enforcement, a hook or a doctor check or a script gate. Prose that doesn't work graduates into code that does.
- **The loop is measured.** `loop-report.py` answers what cycle fifty knows that cycle one didn't, and keeps a trend file.

```text
**Loop report 2026-06-10.** Since cycle 1 the loop has captured 31 lessons
(9 in the last 30 days), promoted 4 into patterns (3 validated, 1 failed),
and run 22 skill invocations in the last 30 days (86% pass).
```

When a skill underperforms, `/improve` runs it against tests, scores the output, proposes one change to the skill's own instructions, and re-runs everything to check for regressions before you accept. Models get replaced. The harness gets smarter.

## Before Code: Research and Pushback

The same skepticism runs upstream, before any code exists.

**Research.** `/scout` is a 2-3 minute recon: Reddit and YouTube for what real people hit. `/research` goes deep, across multiple models so one model's blind spots get caught, with a source registry so claims are checkable. External findings stay untrusted: extract the technique, verify packages and env vars before you adopt.

**Pushback.** `/panel` reviews the plan for blind spots before `/build`. Validator and reviewer agents check the code as it's built. A scope guard cuts a prototype to one or two problems, because a finished prototype that solves one problem beats a spec for V3 that never ships. Before any build even starts, a quick check asks whether the next decision is easy to undo; if it's a one-way door, you get a nudge to think it through first instead of discovering the cost after it's built.

## Skills

Slash commands that do real things. Each sits in the system prompt as one line until you invoke it; the full instructions load only then, so you can keep dozens on hand and pay the token cost only for the one you run. Most are free on your existing Claude Code subscription; paid skills spend on OpenRouter calls.

| Command | What It Does | Cost (USD) |
|---------|--------------|------|
| `/start-vague` | Takes a vague idea and turns it into something buildable | Free |
| `/scout <question>` | Quick research: Reddit, YouTube, web. 2-3 minutes. | $0.00–0.10 |
| `/research <topic>` | Deep multi-model research. 8 steps, source registry, paper output. | $0.15–0.55 |
| `/consult <decision>` | Simulates a panel of domain experts, gives you one recommendation | Free |
| `/frame` | Generates a design system, architecture diagrams, wireframes | Free |
| `/wireframe-first` | Sketches one screen in plain text and gets your sign-off before any code | Free |
| `/panel [path]` | Pressure-test your idea before `/build`. 2 domain reviewers scan for blind spots: what's stated, missing, assumed. | Free |
| `/advisor [decision]` | Checks a decision against project artifacts, reports mismatches | Free |
| `/code-review [path]` | Clean-context reviewer scans a path or diff, returns tiered findings | Free |
| `/build new <idea>` | First version: idea to working prototype (resumable across sessions via state file) | Free (~$0.12 scored) |
| `/build full <project>` | Full SDLC: PRD, tech spec, arch review, phased builds, QA | Varies (research + scoring) |
| `/improve <skill>` | Runs a skill, scores the output, proposes instruction fixes, verifies no regressions | ~$0.20–0.40 / cycle |
| `/curate` | Weekly memory consolidation: prunes, merges, verifies promotions | Free |
| `/doc-sync` | Updates state file, conversation log, roadmap, lesson capture | Free |

## Two Ways to Build

<p align="center">
  <img src="assets/build-journey.png" alt="Two build paths: one session ships a working prototype; multiple sessions run full SDLC" width="860">
</p>

Both start from an idea; if yours is still vague, run `/start-vague` first to shape it into a buildable `idea.md`.

- **`/build new`: one session, idea to prototype.** Scoping questions, scope guard, design tokens, then a build loop until it works in the browser. The state file persists, so `/build continue` picks up exactly where you left off when context compresses or you stop for the night. A feature only counts as done once it's actually verified working, tracked in a ledger the model can't quietly edit; and resuming a build re-checks the app still runs before any new work starts, so a broken session boundary gets caught instead of built on top of.
- **`/build full`: multi-session, prototype to production.** Deep research, gap analysis, PRD, tech spec, architecture review, phased builds with tests, code review, QA. Context is handed off through files, not memory. Don't start here; start with `/build new`. If it's worth investing in, you'll know.

## Why It's Built This Way

- **Files over a database.** State, memory, and patterns are plain markdown and TSV, not a vector store. You can read, grep, diff, and carry every memory anywhere. At personal scale, inspectability beats retrieval cleverness.
- **Three-tier context.** Core (~300 lines) loads every session, Recall loads on demand, Archival is search-only. The window doesn't fill with what isn't relevant right now.
- **Skills load lazy.** Each skill is one line in the system prompt until invoked. Keep 50 on hand, pay for the one you run.
- **Enforcement over discipline.** Anything the loop depends on is a hook or a script in `.claude/hooks/`, not a reminder. Deterministic Python, readable in one sitting. Habits decay; gates don't.
- **Cheap tier for plumbing, capable tier for judgment.** Subagents that fetch, format, or sync run on a cheaper model tier; the calls that decide scope, review code, or gate a release stay on the capable one. You get parallel throughput without paying model cost for work that doesn't need it.

## What OpenVera Won't Do

Enforced in `.claude/settings.json` and the hooks, not promised in prose. Audit them yourself.

- **Won't run `sudo` or `rm -rf`, or read your secrets.** `.env` files, SSH keys, and cloud credentials are denied outright; `.secrets` requires your explicit approval each time.
- **Won't force-push, hard-reset, or kill processes without asking.**
- **Won't push anywhere.** Nothing in the harness runs `git push`. Commits stay local until you push them yourself.
- **Won't edit your patterns.** `patterns.md` is hand-curated by rule; the machine lane is separate files.
- **Won't phone home.** After install, the only scripts that touch the network are `openrouter.py` and `youtube-analyze.py`, and only when a skill you invoked calls them. Run logs and session conversation logs stay local.

## Keys are Optional

The whole memory loop and most skills (`/start-vague`, `/consult`, `/frame`, `/wireframe-first`, `/panel`, `/advisor`, `/code-review`, `/curate`, `/doc-sync`) run with no key. `/scout` covers web search keyless; `/build` ships fine, just unscored (you still get the validator and reviewer agents, only the external judge is skipped).

Keys add the depth: `/research` and `/improve` need OpenRouter for their multi-model calls, `/scout`'s Reddit and YouTube depth runs through OpenRouter (video analysis needs a Google AI key), and `/build`'s external scoring gate needs OpenRouter. At install time, `git clone` pulls the repo, and if you paste a key into bootstrap it gets verified with one call; skip the prompts to skip the calls. There is no `pip install` step: OpenVera runs on the Python standard library alone.

To add keys later:
```bash
cp vera-system/.secrets.template vera-system/.secrets
chmod 600 vera-system/.secrets
# edit vera-system/.secrets
```

The `.secrets` file is gitignored and chmod 600; permissions require Claude to ask before reading it.

## Make It Yours

After bootstrap: set the tone in `vera-system/who-i-am/voice.md`, tell Claude who you are in `vera-system/relationships/user.md`, and add your own rules to `vera-system/memory/patterns.md`. Change paths or the default model in `vera-system/config.json`. To add a skill, drop a `.claude/skills/<name>/SKILL.md` with YAML frontmatter (name + description) and instructions in the body.

Bootstrap also asks if you want a working-style profile kept in `relationships/user.md`. It learns how to work with you, without keeping a dossier on you: preferences and patterns get written down, never health, family, employer, finances, or location. You can read it, edit it, or turn it off any time by flipping `user_memory` in `config.json`.

## Recommended MCPs

Optional, but two noticeably help:

| MCP | What It Adds | Install |
|-----|-------------|---------|
| **Playwright** | `/build` verifies your app in a real browser instead of jsdom. Catches bugs that pass unit tests. | `claude mcp add playwright -- npx @playwright/mcp@latest` |
| **Context7** | Up-to-date library docs injected into `/research` and `/build`. Prevents stale training data for fast-moving libraries. | `claude mcp add context7 -- npx -y @upstash/context7-mcp` |

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI · Python 3.8+ · git
- Windows: run bootstrap via Git Bash or WSL (not cmd.exe or PowerShell directly)
- Optional: [OpenRouter](https://openrouter.ai) key (multi-model research) · [Google AI](https://aistudio.google.com/apikey) key (YouTube analysis in `/scout`)

<details>
<summary><strong>Repo structure</strong></summary>

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
│   └── conversations/             <- session logs (gitignored, local only)
│
└── vera-projects/                 <- output goes here
    ├── projects/                  <- one folder per project
    └── research-output/           <- standalone research papers
```

</details>

## When Things Break

See [RECOVERY.md](RECOVERY.md) for hook errors, missing skills, broken bootstrap, and doctor warnings.

## License

MIT. See [LICENSE](LICENSE).

Built by [Shareef Ellis](https://x.com/shareefatwork). Changelog on [@openveraai](https://x.com/openveraai). Inspirations in [THANKS.md](THANKS.md).
