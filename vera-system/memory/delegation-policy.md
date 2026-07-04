# Delegation Policy - Orchestrator + Subagents

*How OpenVera spawns, scopes, and trusts subagents. Governs `/build` and every skill that spawns agents (`/research`, the `/build new` Stage 0 interview gate, and any future orchestrator). Adapted from the private-Vera policy; verified against Claude Code docs + Anthropic engineering posts (sources at bottom).*

---

## The Three Goals (priority order)

1. **Lead stays context-light.** The lead session holds the thread, gates, and summaries. The actual work happens in subagent windows and returns only summaries + artifact paths.
2. **Tier per task.** Decide at spawn time: cheap tier for mechanical plumbing, capable tier for judgment. This mirrors Anthropic's own production pattern (capable-tier lead + cheap-tier workers in their research system). Actual model IDs are a config/frontmatter detail, not a policy detail - see "Tier language" below.
3. **Max 3 concurrent subagents.** Hard cap. Spawn in waves of 3 or fewer; a wave must drain (and be health-checked) before the next starts. No runaway processes.

One tempering fact from Anthropic: multi-agent work burns roughly 15x the tokens of a single chat, and "most coding tasks involve fewer truly parallelizable tasks than research." So the posture is **selective delegation to keep the lead lean, not spawning armies.**

---

## Tier language (no model names here)

This document, and any `vera-system/` doc like it, talks in tiers only:

| Tier | Use for | Examples |
|------|---------|----------|
| **Cheap tier** | Mechanical, high-volume, low-ambiguity work | doc-sync, scout, research fan-out, routine implementer steps |
| **Capable tier** | Judgment calls, gates, synthesis | the lead itself, review verdicts, ship/no-ship calls |

Actual model IDs (Sonnet, Opus, Haiku, or whatever ships next) live ONLY in `.claude/agents/*.md` frontmatter and skill bodies that call a specific script or API. They never appear in README, `vera-system/` docs, or public copy - that's a separate house rule (generic-model-names), not unique to delegation, but it applies here too.

---

## Lever A - Spawn Mode (fresh vs fork vs worktree)

**Fresh is the default. Fork is the exception.** A fresh child runs in its own window and returns only a summary, so the lead's context barely moves. A fork drags the entire parent conversation into the child.

| Mode | Use ONLY when | In `/build` that means |
|------|---------------|------------------------|
| **Fresh** (default - named agent or general-purpose) | Task is self-contained: role + paths + state file, it reads the rest from disk | doc-sync, scout, research, most build-loop steps |
| **Fork** | The child needs *this conversation's* accumulated reasoning that isn't fully on disk | A mid-build-loop experiment where re-briefing from the state file would be lossy |
| **Worktree-for-parallel-writes** | 2+ children mutate files in the same repo at the same time | Parallel implementers editing different files in the same build phase |

**Fork tripwire:** "Would re-reading the state file lose reasoning that only exists in my current context?" No, then fresh.

**Fork facts (verified against Claude Code docs):**
- Inherits the entire parent conversation, system prompt, tools, model. First call reuses the parent's prompt cache (cheap to start, expensive to run).
- Steerable, not fire-and-forget: forks appear in a panel; follow-ups can be sent.
- A fork cannot spawn another fork (it can spawn other subagent types).
- Verdict for `/build`: rare. Whole-context cost plus the 15x warning make fresh + resume the more reliable default.

**Nesting (verified):** subagents can spawn subagents, fixed depth limit of 5. This legalizes a reviewer spawning a verifier per finding.

**Resume (verified):** resuming an agent by ID continues it with full history. Prefer resume over fork when continuing prior delegated work.

---

## Lever B - Tier Routing (the lead decides per spawn)

| Task class | Tier | Examples |
|------------|------|----------|
| Trivial / mechanical | Cheap | telemetry appends, file moves, registry rows |
| Mechanical / high-volume | Cheap | doc-sync, scaffold, scout, research fan-out, routine build-loop edits |
| Judgment / gates / synthesis | Capable | code-review verdicts, ship/no-ship calls, ambiguous scope calls |

- The lead orchestrator runs on the capable tier, always, but delegates aggressively so its own window stays small.
- Every spawn carries an explicit model choice in the agent's frontmatter or the per-invocation override - never rely on an unstated default, since that can silently route plumbing onto the expensive tier.
- Model resolution order (verified): environment override, then per-invocation param, then agent-file frontmatter, then the main model.

---

## Lever C - Concurrency: MAX 3

- Never more than 3 subagents in flight. Waves of 3 or fewer; wait for the wave to drain before the next.
- **Wave health-check before proceeding:** every agent in the wave either returned a valid contract (Lever D) or is explicitly logged as failed. Confirm expected artifacts exist on disk. A hard failure stops the pipeline; do not drift past it.
- Encode the cap as an instruction in each orchestrating skill so it is a house rule, not a harness accident.
- Anthropic's own guidance is "3-5 in parallel"; 3 is the conservative end, chosen deliberately.

---

## Lever D - Reliability Contracts (the real fix)

The weakest link is not spawn mode, it is the lead trusting a subagent's prose. These rules close that gap:

1. **Spawn contract (every delegation, no free-text briefs).** Every spawn prompt contains exactly:
   - **Objective** - one sentence, what done means
   - **Output** - the declared artifact path it must write, plus the return shape (see item 2)
   - **Tools/sources** - what to read (paths), what to use, what NOT to touch
   - **Boundaries** - what is out of scope

   Subagents still read from disk themselves - the contract carries role, paths, and boundaries, never pre-chewed content summaries.

2. **Contracts over prose.** Subagents return structured output - minimally `STATUS: done|partial|failed`, `ARTIFACT: <path>`, `NOTES: <3 lines max>` - not an essay. The lead parses state, not vibes.

3. **Fail-closed artifact verification.** The lead re-reads the declared artifact before trusting the summary, and checks the specific expected identity (right path, non-empty, expected section or marker present). "Done" without a verifiable artifact counts as a fail.

4. **Declared path plus idempotent resume.** Output paths are declared before spawning. If an agent dies or returns nothing, respawn or resume; work already on disk is skipped, not redone.

5. **Guards.** A max-turns limit on every agent definition; retry once then escalate to the lead; a hard-failure signal from one agent stops the wave.

6. **Adversarial second pass, gates only.** For judgment gates (code review, ship decisions): a cheap skeptic pass tries to refute the verdict before the lead accepts it. Legal to nest (a reviewer may spawn a verifier per finding, depth 5 max). Not for plumbing - tokens matter.

---

## Persistent Agent Definitions (`.claude/agents/`)

Define once, reuse across skills. Only roles used by 2+ skills earn a file; one-offs stay inline in the spawning skill.

| Agent | Tier | Tools (scoped) | Used by |
|-------|------|-----------------|---------|
| `researcher` | Cheap | Read, Write, Glob, Grep, WebSearch, WebFetch, Bash | `/build`, `/research`, `/build new` Stage 0 interview gate (evidence-gathering lenses) |
| `implementer` | Cheap | Read, Write, Edit, Glob, Grep, Bash | `/build` loop (worktree isolation when running in parallel) |
| `reviewer` | Capable | Read, Glob, Grep, Bash, Write, Edit | `/build` review step, ship/no-ship gates |
| `doc-sync` | Cheap | Read, Glob, Grep, Edit, Write, Bash | every skill's end-of-session doc-sync spawn |

The contract rules from Lever D are baked into each agent file's body, not just referenced - a subagent receives only its own system prompt plus basic environment, not the full harness system prompt or conversation history. Anything it must obey has to live in the agent file or the spawn contract itself.

---

## What This Explicitly Rejects

| Rejected | Why | Reopen trigger |
|----------|-----|-----------------|
| Fork-by-default | Fights goal 1 (whole-context copy), 15x cost warning | A build stage shows repeated lossy re-briefing from state files, with fork no longer experimental |
| Managed-agent backend services (coordinator/threads-style APIs) | Different runtime than the interactive harness OpenVera runs in | OpenVera moves to an always-on/background runtime |
| Workflow engine for autonomous stages | Deterministic control flow and real caps, but token-heavy and removes interactive gates | Contract discipline (Lever D) proves out AND an autonomous stage still shows orchestration drift |
| More than 3 concurrent, with queueing | Complexity without demonstrated need | A build stage demonstrably starves on 3 |

---

## Sources

- [Claude Code: Create custom subagents](https://code.claude.com/docs/en/sub-agents) - frontmatter fields, model resolution, fork behavior, depth limit 5, resume-by-ID
- [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) - simplest-thing-first, orchestrator-workers, complexity warnings
- [Anthropic: How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) - capable-tier lead + cheap-tier workers, delegation contract (objective/output/tools/boundaries), 3-5 parallel, 15x token economics
