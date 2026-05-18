---
name: research
pass_threshold: 4.0
---

## Dimensions

| Dimension | Weight | Floor | Description |
|-----------|--------|-------|-------------|
| accuracy  | 0.35   | 3     | Claims are correct. Sources exist, are real, and say what's quoted. No hallucinated URLs or invented stats. |
| coverage  | 0.25   | 3     | Hits the angles a domain expert would check first. Includes failure modes and adjacent domains, not just the obvious framing. |
| depth     | 0.20   | 3     | Goes beyond surface-level. Specific versions, named tradeoffs, concrete failure modes — not "it depends." |
| utility   | 0.20   | 2     | Output drives a decision. Includes recommendations, decisions to make, hard questions — not just an information dump. |

## Floor logic

A score below a dimension's floor fails the test regardless of composite. Accuracy floor is highest because hallucinated research is worse than no research.

## Scoring guidance

- **5** — near-perfect. Would hand to a senior expert without edits.
- **4** — solid. Ships with minor copy edits. The default for "good research."
- **3** — usable but has gaps. Misses an angle, has 1-2 weak claims, or buries the recommendation.
- **2** — significant rework. Multiple weak sources, missed major angles, or no clear takeaway.
- **1** — unusable. Hallucinated content, generic LLM output, or fundamental misread of the question.
