---
description: Spawn the detached advisor to check a decision against project artifacts. Use when you want an outside perspective on scope, depth, or framing.
argument-hint: "[optional: the decision or question to check]"
---

# Advisor

Spawn the advisor agent with the current project's artifacts and the decision in question. The advisor has no session context — it reads only the artifacts and reports mismatches.

## How to invoke

1. Identify the current project slug (read `build-state.md` or check recent `{paths.projects_dir}/*/` by mtime)
2. Collect relevant artifact paths from that project: `idea.md`, `spec.md`, `retro.md`, `v1-checklist.md`, `build-state.md` (skip any that don't exist)
3. Package the decision into a prompt. Include:
   - The artifacts (as file references, not pasted content — the agent will Read them)
   - The decision to check (from `$ARGUMENTS` or from current conversation state)
4. Spawn the advisor agent:

```
Agent(
  subagent_type: "advisor",
  description: "Check decision for mismatches",
  prompt: "Artifacts to read: <paths>\n\nDecision to check: <decision>\n\nReport any mismatches between the artifacts and the decision. If none, say so."
)
```

5. Report the advisor's output verbatim. Do not summarize, interpret, or soften. The user sees exactly what the detached agent produced.

## Auto-invocation in /build full

Auto-fire logic (keyword list + stage timing) lives in `.claude/skills/build/SKILL.md` Stage 0.5 — single source of truth. This command file covers manual `/advisor [decision]` invocation only.
