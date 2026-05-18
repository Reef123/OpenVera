# rubrics/

Scoring rubrics for `/improve`. One file per content type. Each test in `../tests/` declares which rubric to use via frontmatter (`rubric: research`).

## Rubric file format

```markdown
---
name: research
pass_threshold: 4.0
---

## Dimensions

| Dimension | Weight | Floor | Description |
|-----------|--------|-------|-------------|
| accuracy  | 0.4    | 3     | Claims are factually correct, sources cited |
| coverage  | 0.3    | 3     | Hits the angles a domain expert would expect |
| utility   | 0.3    | 2     | Output is actionable, not just informational |

## Floor violations

A score below a dimension's floor fails the test regardless of composite. Floors prevent reward hacking — you can't trade off a critical dimension for a strong one.

## Scoring guidance

- 5 = near-perfect, would publish
- 4 = solid, ships with minor edits
- 3 = usable, has gaps
- 2 = significant rework needed
- 1 = unusable
```

## Files

- `research.md` — for `/research`, `/scout`
- `code.md` — for `/build`
- `prose.md` — for `/doc-sync`, `/curate`, conversation logs

Add new rubric files as you add new skill types. Match the type name to the test frontmatter `rubric:` field.
