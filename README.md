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

OpenVera is a personal AI workbench you open in [Claude Code](https://docs.anthropic.com/en/docs/claude-code). It keeps a running memory of your work, researches before it builds, ships a first version you can use the same day, and carries what it learns into the next session.

It runs on persistent memory, reusable skills, research tools, and behavioral patterns. Your fiftieth coding session is better than your first.

**Two entry points, depending on where you are:**

- **`/start-vague <vague idea>`** when the idea isn't sharp yet. Walks scoping questions, scouts the space for existing tools, hands off a buildable bet.
- **`/build new <ready idea>`** when you know what you want. 2-4 short scoping questions, then autonomous: research → design → build loop → first-paint check → 🐘 ship summary in ~10-20 min.

Most Claude Code setups are stateless. Every conversation starts cold. OpenVera doesn't. Four things keep the build flow getting better session after session:

- **Running state file** that picks up where the last session ended
- **Pattern library** that grows from real mistakes, so the same gotcha doesn't bite twice
- **Skills that improve their own instructions** over time
- **Standardized output** so every build produces the same files (idea, spec, working code, screenshot) and you always know where to look

The model is the same. The workbench is what wins.

## Get Started

**One-liner.** Clones into `./openvera`, then runs the interactive bootstrap:

```bash
curl -fsSL https://raw.githubusercontent.com/Reef123/OpenVera/main/install.sh | bash
```

Pass a custom path:

```bash
curl -fsSL https://raw.githubusercontent.com/Reef123/OpenVera/main/install.sh | bash -s -- ~/projects/my-harness
```

**Or manual** (if you'd rather inspect the [`install.sh`](install.sh) first, which is recommended):

```bash
git clone https://github.com/Reef123/OpenVera.git openvera
cd openvera
./bootstrap.sh
```

Either way, the bootstrap asks your name and optional API keys, fills in the templates, runs a health check, and prints next steps. After that, Claude boots into OpenVera automatically whenever you open this folder with `claude`.

## Why It's Built This Way

A few choices drive the rest:

- **Files over chat.** State, memory, and patterns live as files on disk, not in the conversation. If it's not in a file, it doesn't survive a reboot.
- **Three-tier context.** Core (~300 lines) loads every session. Recall loads on demand. Archival is search-only. The context window doesn't fill up with stuff that isn't relevant right now.
- **Skills load lazy.** A skill is just a name and a one-line description in the system prompt. The full instructions only load when you invoke `/<command>`. You can have 50 skills without paying token cost for the 49 you didn't use.
- **State on disk, not in the model.** Every skill reads and writes the same files (`state.md`, `ROADMAP.md`, `MEMORY.md`, `patterns.md`). Session 50 sees what session 1 wrote.
- **Research before code, not as code.** Most "build it" tools start coding immediately. OpenVera runs `/scout` or `/research` first. Reddit and YouTube for what real people actually hit, multi-model synthesis via OpenRouter for blind spots a single model misses, sourced paper output so claims are checkable. Cheap when a quick recon is enough (~$0.10 scout, 2-3 min), thorough when the decision deserves it (~$0.50 research with 8 steps and a source registry). External findings are treated as untrusted data: extract techniques, not artifacts. Verify packages and env vars before adopting anything a model recommends.

## What's In Here

### Boot Sequence

When Claude opens this workspace, `CLAUDE.md` loads context in three tiers:

<p align="center">
  <img src="assets/boot-sequence.png" alt="Three-tier context loading: Core loads every session, Recall loads on demand, Archival is search-only" width="860">
</p>

Core loads every session (~300 lines). Recall loads when relevant. Archival stays on disk until you search for it. This keeps the context window from filling up with stuff Claude doesn't need right now.

### Memory

```
memory/
  MEMORY.md      <- things Claude has learned (appended at session end by /doc-sync, pruned weekly by /curate)
  patterns.md    <- decision frameworks (you curate these)
```

`MEMORY.md` grows automatically. Claude writes down operational gotchas, your preferences, project decisions. `patterns.md` is where you put the rules you want enforced: "when I get excited about a feature, check for scope creep" or "external advice means verify first, implement second." These fire as guardrails during actual work.

### Conversation History

Every session writes a snapshot to `vera-system/conversations/NNN-YYYY-MM-DD.md`:

- Triggered by `/doc-sync` (run it manually, or get auto-nudged before context compression)
- Captures session summary, course corrections, files changed, state at end
- Logs are gitignored, so they stay local to your machine and never get pushed
- Fresh installs start at session 1; history grows session-by-session

### Skills

Slash commands that do real things, in two kinds:

- **Skills** live in `.claude/skills/<name>/SKILL.md`. Their full instructions only load when you invoke them; until then they're just a name and one-liner in the system prompt.
- **Commands** live in `.claude/commands/<name>.md`. Short, focused prompt templates that orchestrate skills.

Three layers: entry points, building blocks, and meta.

<p align="center">
  <img src="assets/skills-map.png" alt="OpenVera skills map: entry points (start-vague, build new, build full), building blocks (scout, research, consult, frame, wireframe-first, panel, advisor, code-review), and meta (improve, curate, doc-sync), all over a shared state substrate" width="860">
</p>

Costs below are typical USD ranges per invocation. Paid skills spend on OpenRouter model calls; free skills run on Claude subagents through your existing Claude Code subscription.

| Command | What It Does | Cost (USD) |
|---------|--------------|------|
| `/start-vague` | Takes a vague idea and turns it into something buildable | Free |
| `/scout <question>` | Quick research: Reddit, YouTube, web. 2-3 minutes. | $0.00–0.10 |
| `/research <topic>` | Deep multi-model research. 8 steps, source registry, paper output. | $0.23–0.63 |
| `/consult <decision>` | Simulates a panel of domain experts, gives you one recommendation | Free |
| `/frame` | Generates a design system, architecture diagrams, wireframes | Free |
| `/wireframe-first` | Sketches one screen in plain text and gets your sign-off before any code | Free |
| `/panel [path]` | Pressure-test the bet before `/build`. 2 domain reviewers (read-only, clean-context) scan for blind spots: what's stated, missing, assumed. Confirmation-bias prevention. | Free |
| `/advisor [decision]` | Checks a decision against project artifacts, reports mismatches. Auto-fires on scope/depth mismatch in `/build full` Stage 0. | Free |
| `/code-review [path]` | Clean-context reviewer scans a path or diff, returns tiered findings | Free |
| `/build new <idea>` | V0: idea to working app (resumable across sessions via state file) | ~$0.12 (scoring) |
| `/build full <project>` | Full SDLC: PRD, tech spec, arch review, phased builds, QA | Varies (research + scoring) |
| `/improve <skill>` | Runs a skill, scores the output, proposes instruction fixes | $0.28–0.48 / cycle |
| `/curate` | Weekly memory cleanup: prunes stale stuff, merges duplicates | Free |
| `/doc-sync` | Updates state file, conversation log, roadmap | Free |

`/advisor` is a command. Everything else above is a skill.

### Hooks

These run mechanically, not by asking Claude to remember. Five files in `.claude/hooks/`:

- **`session-start.py`** runs a boot health check (bootstrap state, config validity, `/curate` freshness), then prints one status line plus a rotating tip
- **`mark-dirty.py`** fires after any harness-file write and flags the session as having unsaved work, which is what the pre-compact gate reads
- **`pre-compact.py`** is the gate: when the session has unsaved work, it blocks context compression until you run `/doc-sync`
- **`post-compact.py`** re-injects state, patterns, and your context after compression, so Claude doesn't lose the thread
- **`session-end-reminder.py`** nudges you to run `/doc-sync` before you quit

The pre-compact gate is deterministic Python, wired under `PreCompact` in `.claude/settings.json`.

## Two Ways to Build

<p align="center">
  <img src="assets/build-journey.png" alt="V0 vibe codes a working app; V1+ runs full SDLC across multiple sessions" width="860">
</p>

### V0: Just Build It (`/build new`)

You have an idea. Maybe it's half-formed. `/build new` runs the whole pipeline: quick research, scope guard (cuts you to 1-2 problems), design tokens, then a build loop until it works in the browser. The state file persists across sessions, so when context compresses or you stop for the night, `/build continue` picks up exactly where you left off.

You answer 2-4 short scoping questions before it goes autonomous: what's the job, what pain does this solve, what's the one action that has to work, and (if any of those leave gaps) a quick pressure-test on what Vera is about to assume. After that, it runs without interruption.

A finished V0 that solves one problem is worth more than a spec for V3 that never gets built.

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
│   ├── memory/                    <- patterns + auto-memory
│   ├── scripts/                   <- helper scripts (OpenRouter, Reddit, YouTube, etc.)
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
- **`vera-system/memory/patterns.md`** starts empty; add patterns as you discover them

To add a skill, create `.claude/skills/<name>/SKILL.md` with YAML frontmatter (name + description) and instructions in the body.

To change paths or the default LLM model, edit `vera-system/config.json`.

### Keys are Optional

**After install, OpenVera makes no network calls on its own.** No phone-home, and nothing leaves your machine (any run logs stay local in `vera-system/runs/`). Hooks and the harness itself are local-only. Audit them yourself in `.claude/hooks/` and `vera-system/scripts/`.

The only scripts that touch the network are the three you'd expect: `openrouter.py` (multi-model research), `reddit-fetch.py` (community recon), `youtube-analyze.py` (video analysis). All run only when a skill you invoked calls them.

Install-time exceptions: `git clone` pulls the repo, `pip install` fetches Python deps, and if you paste an API key into bootstrap it gets verified with a one-shot call (OpenRouter `GET /auth/key`, Google AI `GET /v1beta/models`). Skip the prompts to skip the calls.

**Works without keys:**
`/start-vague`, `/consult`, `/frame`, `/advisor`, `/curate`, `/doc-sync`. `/scout` works for Reddit + web with no key. YouTube discovery needs OpenRouter; YouTube video analysis needs a Google AI key.

**What degrades without keys:**
- `/build` still ships, but the external scoring step is skipped (the rival-model quality gate). You still get validator + reviewer agents.
- `/improve` needs OpenRouter for its scoring loop.
- `/research` needs OpenRouter for its multi-model calls.

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
