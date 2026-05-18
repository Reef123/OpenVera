# tests/

Test inputs for `/improve`. One subdirectory per target skill: `tests/<skill-name>/`.

Each test is a Markdown file with frontmatter and two sections:

```markdown
---
name: descriptive-test-name
created: YYYY-MM-DD
rubric: research   # which file in ../rubrics/ to score against
---

## Input
[Exact input/scenario to give the skill]

## Expected Qualities
- Should cite at least 8 sources
- Should identify the main tradeoff between X and Y
- Should NOT recommend Z (known bad fit)
```

3-5 tests per skill is enough. Diversity beats quantity — different topics, difficulty levels, failure modes.

The eval harness IS the product. Don't auto-generate tests from SKILL.md — that just tests what the skill already says. Write tests from real failures you've seen.
