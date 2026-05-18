# Skills

Each skill is a folder with a `SKILL.md` (instructions) and optional supporting files. Skills load their full body only when invoked via `/<command>` — the system prompt sees only the name and description.

## How they fit together

<p align="center">
  <img src="../../assets/skills-map.png" alt="Vera skills map: entry points (start-here, build new, build full) call building blocks (scout, research, consult, frame, advisor); meta skills (improve, curate, doc-sync) operate on the harness itself; all skills share state via state.md, ROADMAP.md, MEMORY.md, patterns.md, conversations/." width="860">
</p>

Three layers: **entry points** (what the user invokes), **building blocks** (called by `/build`, also runnable standalone), and **meta** (operate on the harness, not on a project). Everything reads and writes through a shared state substrate so context survives session boundaries.

## Index

| Skill | Command | Purpose |
|-------|---------|---------|
| Scout | `/scout <question>` | Quick answers — Reddit + YouTube + web, 2-3 min. **Default for most questions.** |
| Consult | `/consult <decision>` | Decision accelerator — domain expert tradeoffs + recommendation. Free (no API calls). |
| Research | `/research <topic> [--quick]` | Multi-model research with paper artifact. `--quick` skips scoping + adversarial review. Use when `/scout` isn't enough. |
| Frame | `/frame [--quick \| --deep]` | Design system (DESIGN.md), architecture diagrams, wireframes. Called by `/build` or standalone. |
| Build | `/build new <idea>` | V0 pipeline — ship in one session. |
| Build Full | `/build full <project>` | Full SDLC — PRD → tech spec → arch review → build → QA → ship. |
| Improve | `/improve <skill>` | Autonomous skill improvement loop with rubric scoring. |
| Curate | `/curate` | Weekly memory consolidation. |
| Doc-Sync | `/doc-sync` | Session documentation — state, logs, alignment. **Run every session.** |
| Start Here | `/start-here [optional: idea]` | Guided idea exploration — vague spark to buildable concept. |
| Panel | `/panel [optional: idea.md path]` | Pressure-test the bet before `/build`. 2 domain reviewers scan for blind spots (clean-context). Confirmation-bias prevention. |
| Advisor | `/advisor [decision]` | Detached agent — checks a decision against project artifacts, reports mismatches. Auto-fires on scope/depth mismatch in `/build full` Stage 0. |

## Cost awareness

| Skill | Typical Cost |
|-------|-------------|
| `/research` | $0.23-0.33 (`--quick`) / $0.43-0.63 (deep) |
| `/improve` | $0.28-0.48 per cycle |
| `/build` (scoring) | ~$0.12 per score |
| `/scout` | $0.08-0.18 (depends on YouTube usage) |
| `/panel` | $0.13-0.23 (2 Explore subagents reading idea.md) |
| `/curate`, `/consult`, `/doc-sync`, `/build full` (excluding research/scoring) | Free |

**Rule:** Don't call Claude via OpenRouter — you ARE Claude.

## Adding your own skills

Create `.claude/skills/<name>/SKILL.md`:

```markdown
---
name: my-skill
description: "What this skill does and when to invoke it."
allowed-tools: Bash(python3 vera-system/scripts/*) Bash(git *)
---

# My Skill

Instructions for when this skill is invoked via `/my-skill`.
```

Restart Claude Code (or run `/skills`) so the new skill registers.

## Bridge skills (external tool integrations)

Want to mirror Vera state to Obsidian, sync ROADMAP.md with Notion, or post to Slack? Build a regular skill that does it. No special infrastructure needed — a skill is a skill.

**Pattern:** Create `.claude/skills/<tool>-bridge/SKILL.md` with instructions for what to read, where to write, and when to run. Add it to `/doc-sync` or `/curate` as a post-completion step if you want it to fire automatically.

**Example — Obsidian state mirror:**
```
.claude/skills/obsidian-mirror/SKILL.md:
  Read vera-system/state.md, copy to $OBSIDIAN_VAULT_PATH/Vera/state.md.
  Run after /doc-sync completes.
```

**Security note:** Bridge skills run with full local permissions (same as any Claude Code skill). Only use skills you wrote or have personally reviewed. There is no sandbox.
