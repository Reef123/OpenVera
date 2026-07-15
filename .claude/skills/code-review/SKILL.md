---
name: code-review
description: "Adversarial code review by a clean-context Claude subagent. Read-only. Returns Critical/High/Medium/Low findings against correctness, security, design, reliability, tests, quality. Standalone (no /build pipeline coupling)."
argument-hint: "<path-or-git-range> [--against <spec>] [--write <output-path>]"
allowed-tools: Read, Glob, Grep, Bash(git diff:*) Bash(git show:*) Bash(git log:*) Bash(wc:*) Bash(find:*)
---

# Code Review

Spawn a clean-context Claude subagent (`code-reviewer`) to adversarially review a file, directory, or git diff. The subagent returns findings as YAML; this skill formats them and (optionally) writes a review artifact.

**Use this when:**
- You want a second pair of eyes on a file before committing.
- You finished a build phase outside `/build full` and want a `code-review.md`-shape report.
- You want to review the last commit (`/code-review` with no args defaults to `HEAD~1..HEAD`).

**Don't use this for:**
- `/build full` Phase 6 — that pipeline still uses `Agent(subagent_type: "reviewer", ...)` internally, which writes `.build/review.md` in-flow. This skill is a sibling, not a replacement.
- Reviewing ideas or PRDs — that's the `/build new` Stage 0 interview gate (`vera-system/memory/interview-method.md`), not this skill.

**Cost:** Free-ish. The subagent uses your Claude Code plan tokens, on the same model as your session, so the reviewer is never weaker than the model that wrote the code. No external API. If you want a cheaper pass, ask for the smaller background model when you invoke the skill.

---

## Step 0: Parse arguments

`$ARGUMENTS` shapes:

| Shape | Example | Interpretation |
|-------|---------|----------------|
| File path | `.claude/hooks/pre-compact.py` | Review that file |
| Directory path | `.claude/hooks/` | Review every file in it (cap: 10 files) |
| Git range | `HEAD~1..HEAD`, `main..HEAD`, `<sha>..<sha>` | Review the diff |
| Single ref | `HEAD`, `<sha>` | Review the commit's diff vs its parent |
| Empty | (no args) | Default to `HEAD~1..HEAD` |

Flags (any order):
- `--against <path>` — also pass `<path>` to the reviewer as alignment spec (PRD, tech spec, EARS acceptance criteria, etc.)
- `--write <path>` — after findings come back, render them into `templates/code-review.md` shape at `<path>`. Default: print to chat only.

If you can't tell whether an arg is a path or a git range, prefer path. Then fall back to git if the path doesn't exist.

---

## Step 1: Resolve the target

**For a path:**
- Single file → read the file content.
- Directory → glob `**/*.{py,ts,tsx,js,jsx,svelte,md,sh,yml,yaml,json}` (or anything else obviously code), cap at 10 files. If more, list them in chat and ask the user to narrow.

**For a git range:**
- `git diff <range>` — capture the diff output.
- If the range is a single ref (`HEAD`, `<sha>`), expand to `<ref>~1..<ref>`.

**Size guard:** If the captured content exceeds ~50KB (roughly 1500 lines of source or 1000 lines of diff), warn the user, list the largest files, and ask which subset to review. Do not silently truncate.

---

## Step 2: Spawn the reviewer subagent

```
Agent(
  subagent_type: "code-reviewer",
  description: "Code review <target>",
  prompt: <see below>
)
```

The prompt to the subagent has four parts:

1. **Role primer (one line):** `"You are a clean-context senior code reviewer. Follow the checklist and YAML schema in your agent definition. Return ONLY the YAML block."`
2. **Target context:** `"Target: <path-or-range>. Project: OpenVera (personal AI workbench, Markdown + Python harness scripts + Claude Code skills)."`
3. **The content:** The file content OR the diff output OR (for directories) each file's content concatenated with a `# === <path> ===` separator.
4. **(Optional) Spec:** If `--against <spec>` was provided, append `"Alignment spec follows. Compare the target against this:"` plus the spec content.

Keep the prompt under ~100KB total. The agent's checklist + schema live in its definition file, so don't restate them — just remind it to follow them.

---

## Step 3: Receive + display findings

The subagent returns a YAML block. Parse it.

**Print to chat in this shape:**

```
**Verdict:** <pass | pass-with-findings | fail>  ·  C: <n>  H: <n>  M: <n>  L: <n>
**Summary:** <one_liner from YAML>

### Critical
| # | File:Line | Finding | Fix |
|---|-----------|---------|-----|
| C1 | path:12 | <finding> | <fix> |

### High
... (same shape)

### Medium
...

### Low
...
```

Empty severity sections: omit the heading + table entirely (don't print empty headers).

If the YAML doesn't parse, surface the raw output and a one-line "subagent returned non-YAML — re-run with a smaller target or tighter prompt." Don't try to repair the YAML — the subagent should obey schema; if it doesn't, the prompt needs tightening.

---

## Step 4: Optional `--write`

If `--write <output-path>` was passed, write a Markdown file at that path matching `.claude/skills/build/templates/code-review.md` structure:

- Header (Reviewer: Vera, Date: today's date, Status from verdict)
- Review Summary (one_liner from YAML)
- Files Reviewed table (each file in the target)
- Findings — Critical / High / Medium / Low tables (same shape as Step 3)
- Checklist section: copy the checklist from the agent definition with each category marked ✓ (since the agent walks the full list)

Use the Write tool. Confirm the path is reachable (parent dir exists or is creatable).

---

## Step 5: Gate line

Print a single closing line:

```
Verdict: <pass | pass-with-findings | fail>. <N> Critical, <N> High. Run again on a different target, or fix and re-run on the same one.
```

That's it. No follow-up questions. The skill is one-shot.

---

*Author: Shareef Ellis · [@shareefatwork](https://x.com/shareefatwork)*
