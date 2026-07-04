# Inspirations

Vera didn't emerge in a vacuum. These ideas, projects, and people shaped how we think about AI harnesses.

---

**Andrej Karpathy**: The "March of Nines" and AutoResearch work crystallized why compound reliability matters in multi-step AI workflows, and why self-improvement loops are the path forward.

**Anthropic**: Claude Code is the foundation Vera builds on. The hooks, skills, and MCP ecosystem made a compounding harness possible without building a runtime from scratch.

**Nate B. Jones**: Early articulation of why the same model scores differently in different harnesses. The insight that the harness is the compounding asset, not the model.

**The AI Automators**: Clear breakdown of harness engineering as a discipline, with practical architectural patterns for deterministic execution around probabilistic models.

**SuperContext** (sms021): Independent convergence on tiered knowledge architecture. Their "only store what the AI would get wrong without it" principle is one of the sharpest filters we've seen.

**Holaboss**: Sophisticated memory governance with typed staleness policies and recall boosting. Showed what a productized AI worker platform looks like.

**Chachamaru127** ([claude-code-harness](https://github.com/Chachamaru127/claude-code-harness)): Settings.json deny/ask patterns for safe defaults, and the self-audit concept of monitoring whether safety constraints get relaxed. The insight that deny rules are "chains constraining the agent itself" shaped our safety starter.

**OpenClaw**: An open-source AI assistant runtime with skills, cron jobs, and memory. Proved that persistent AI assistants are buildable today.

**shanraisshan** ([claude-code-best-practice](https://github.com/shanraisshan/claude-code-best-practice)): The Agents/Commands/Skills taxonomy for naming the three architectural primitives of a Claude Code harness. Clean framing that we adopted for our own orchestration documentation.

**GitHub Spec Kit** ([spec-kit](https://github.com/github/spec-kit)): Spec-driven development with traceability mapping and multi-agent QA. We adapted their Trace Map (spec-to-code traceability) and MAQA (parallel worktree QA agents) patterns into lighter versions for our SDLC pipeline.

**Russell Barkley**: ADHD research that changed how we think about execution gaps. "Do the work, don't remind about the work" comes directly from understanding ADHD as a performance disorder, not a knowledge disorder.

**Philip Tetlock**: Superforecasting research on why multi-perspective thinkers (foxes) outperform single-theory experts (hedgehogs). The foundation for "The Panel, Not The Expert."

**Matt Pocock** ([grill-me](https://github.com/mattpocock/skills/blob/main/skills/productivity/grill-me/SKILL.md)): The one-question-at-a-time interview that walks down the design tree, resolves dependencies between decisions one by one, and gives a recommended answer for each, until you reach shared understanding. We adapted it into the `/build new` Stage 0 interview gate (`vera-system/memory/interview-method.md`). It started as `/panel`'s "Deeper understanding" verdict path and was promoted to the default gate in v1.21.

---

*If your work influenced Vera and isn't listed here, open an issue. I like to fix that.*
