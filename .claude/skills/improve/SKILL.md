---
name: improve
description: "Autonomous improvement loop — run a skill against test inputs, score output via rubric, analyze failures, propose instruction changes to SKILL.md, verify improvement. Human gate on every change."
argument-hint: "<skill-name> [--batch] | status"
allowed-tools: Bash(python3 vera-system/scripts/*) Bash(git *)
---

# /improve — Autonomous Instruction Improvement

Closed loop: run → measure → analyze failure → propose change → apply → re-measure → keep or revert.

## Configuration (auto-loaded)

```!
cat vera-system/config.json
```

Use `llm.scoring_model` for both scoring AND credit assignment (the scorer diagnoses its own scores). If config is missing, fall back to `vera-system/scripts/vera_config.py`.

**Scoring model should differ from the model executing the skill.** Same model family for both = Goodharting risk — the optimizer learns to please the judge rather than genuinely improve.

## Architecture

1. **Editable asset** — the target skill's SKILL.md (modified directly, git history is the log)
2. **Rubric score** — computed by judge model (from `llm.scoring_model` in config)
3. **Time-boxed cycle** — one atomic change per iteration, keep/revert based on score delta

## Routing

### `<skill-name>`
Run one improvement cycle. Requires tests in `.claude/skills/improve/tests/<skill-name>/` — if none exist, prompt user to write them (see Writing Tests below).

### `<skill-name> --batch`
Run up to 5 consecutive cycles. Stop early if: no failures, score plateaus (delta < 0.5 for 2 consecutive cycles), or budget exceeded.

### `status`
Read `vera-system/runs/*-improve.tsv` files, summarize win rates and recent changes.

### No arguments
List all skills, show which have tests in `.claude/skills/improve/tests/`, suggest which to improve based on last scores.

---

## Writing Tests

The eval harness IS the product — the loop itself is trivial. Auto-generating tests from SKILL.md is circular: you'd test what the skill already says, not what it should do. Write tests from real failures.

When no tests exist in `.claude/skills/improve/tests/<skill-name>/`, stop and prompt the user:

1. **What's a query where you'd KNOW if the output was wrong?**
2. **What's a claim a lazy output would make that's actually false?**
3. **What's the thing most people get wrong about this topic?**

Each answer becomes a test file in `.claude/skills/improve/tests/<skill-name>/`:

```markdown
---
name: descriptive-test-name
created: YYYY-MM-DD
---

## Input
[The exact input/scenario to give the skill]

## Expected Qualities
- Should cite at least 8 sources
- Should identify the main tradeoff between X and Y
- Should NOT recommend Z (known bad fit)
```

3-5 tests per skill. Diversity matters more than quantity — different topics, different difficulty levels, different failure modes.

---

## The Loop

```
1. LOAD   — read SKILL.md + tests + rubric
2. RUN    — execute skill against each test input (use subagent for isolation)
3. SCORE  — judge output via rubric (scoring_model)
4. TRIAGE — all pass? done. failures? continue
5. ANALYZE — credit assignment: which section caused failure?
6. PROPOSE — one atomic change
7. APPLY  — edit SKILL.md on a git branch
8. VERIFY — re-run ALL tests, check for improvement AND regression
9. GATE   — keep if improved with no regression, revert otherwise
10. LOG   — append to vera-system/runs/{skill}-improve.tsv
```

### Step 3: SCORE

```
python3 vera-system/scripts/openrouter.py \
  --model "{llm.scoring_model}" \
  --system "Score this skill output using the rubric. Return ONLY valid JSON." \
  --prompt "RUBRIC:\n{rubric}\n\nTEST INPUT:\n{input}\n\nOUTPUT:\n{output}\n\nScore each dimension 1-5. Return: {\"dimensions\": [{\"name\": \"...\", \"score\": N, \"reason\": \"...\"}], \"composite\": N.N, \"floor_violations\": [\"dimensions below minimum\"], \"pass\": true/false}"
```

Pass threshold and dimension floors are defined in each rubric file (`.claude/skills/improve/rubrics/<type>.md` — ships with `research.md`, `code.md`, `prose.md`). Read them from the file — don't hardcode. A floor violation (e.g., `accuracy < 3` on research, `build_succeeds < 4` on code) fails the test regardless of composite score.

### Step 5: ANALYZE (Credit Assignment)

The critical step most systems skip. The scorer diagnoses its own scores:

```
python3 vera-system/scripts/openrouter.py \
  --model "{llm.scoring_model}" \
  --system "You are diagnosing why an AI skill produced poor output. Identify the section of instructions that caused the problem." \
  --prompt "SKILL.md:\n{skill_md}\n\nTEST INPUT:\n{test_input}\n\nOUTPUT:\n{actual_output}\n\nFAILED DIMENSIONS:\n{failed_dimensions}\n\nIdentify the section(s) in SKILL.md responsible. For each:\n1. Quote the relevant section\n2. How it caused the failure\n3. What it SHOULD say\n\nReturn JSON: {\"attributions\": [{\"section\": \"...\", \"problem\": \"...\", \"suggestion\": \"...\"}]}"
```

Section-level attribution, not line-level — rewriting the failing section is more reliable than surgical line edits.

### Step 6: PROPOSE

One atomic change per cycle:

| Operator | When |
|----------|------|
| **ADD** | Uncovered case |
| **DELETE** | Instruction causes harm |
| **EDIT** | Close but wrong |
| **SUMMARIZE** | Growth check triggered |
| **GENERALIZE** | Multiple similar ADDs |
| **REWRITE** | Plateau — 2+ stale cycles on same failure. Rewrite the entire section. |

**Growth check:** If a change increases SKILL.md by more than 5%, apply SUMMARIZE alongside it. Don't compress deliberately-sized skills — only compress growth from the loop.

### Step 8: VERIFY

Re-run **ALL** tests against the modified SKILL.md — not just failures. A fix for one test can degrade another (the Langfuse lesson: optimizers cut anything not covered by tests).

Apply the WIN/LOSS rule deterministically — collect the target's before/after and every previously-passing test's before/after into JSON, and let `score-gate.py` decide (so a hand-computed delta or an overlooked regression can't flip the verdict):

```bash
python3 vera-system/scripts/score-gate.py improve --file .improve/delta.json
# delta.json: {"target":{"old":N,"new":N},"previously_passing":[{"name":"...","old":N,"new":N}, ...]}
# prints TARGET_DELTA=±N  BAND=0.50  [REGRESSION test="..." drop=N]  VERDICT=WIN|LOSS  [PLATEAU=1]
```

- `VERDICT=WIN` → the target improved and nothing previously-passing dropped past the variance band (default 0.5, ~LLM judge noise).
- `VERDICT=LOSS` → no target improvement, or a `REGRESSION` line fired. A regression loses even when the target improved.
- `PLATEAU=1` → the target delta is below the band; in `--batch`, two consecutive plateau cycles is the stop signal.

### Step 9: GATE

Human approves every change.

**If improved with no regression:**

```markdown
## Proposed: {OPERATOR} on {skill-name}

**Test:** {test description}
**Before:** {old_composite} — {failed dimensions}
**After:** {new_composite} — {improved dimensions}
**Delta:** +{delta}

**Change:**
{git diff of SKILL.md}

**Attribution:** {section that caused failure, from Step 5}

[Approve / Reject / Modify]
```

- **Approved:** Merge branch to main. Record as WIN.
- **Rejected:** Record reason in commit message (loop checks git history before re-proposing).
- **Modified:** Apply edit, re-verify, merge. Record as WIN (modified).

**If no improvement or regression:** Revert automatically. Record as LOSS.

---

## Rubrics

Rubrics live in `.claude/skills/improve/rubrics/<type>.md`. Ships with `research.md`, `code.md`, `prose.md`. Each rubric defines its own dimensions, weights, pass threshold, and dimension floors. Add new rubric files for new content types — match the type name to the test file's `rubric:` frontmatter field.

## Cost

Per cycle: ~$0.20-0.40. Batch (5 cycles): ~$1.00-2.00. Varies with model pricing and test count.

## When NOT to Use

- Problem is a bug → fix the bug directly
- Skill needs structural redesign → manual audit with research first
- No real failures to write tests from → use the skill more, collect signal first

---

*Author: Shareef Ellis · [@shareefatwork](https://x.com/shareefatwork)*
