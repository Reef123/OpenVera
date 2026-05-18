---
name: prose
pass_threshold: 4.0
---

## Dimensions

| Dimension       | Weight | Floor | Description |
|-----------------|--------|-------|-------------|
| signal_density  | 0.35   | 3     | Every sentence carries weight. No filler, no restating, no AI-tone hedges. |
| accuracy        | 0.25   | 3     | Facts and references are correct. No hallucinated file paths, function names, or session numbers. |
| structure       | 0.20   | 3     | Right shape for the format (terse log vs. structured spec vs. narrative). |
| voice_match     | 0.20   | 2     | Matches the project's existing voice. Doesn't sound like a fresh LLM. |

## Floor logic

`signal_density` floor is 3 because bloated docs waste tokens every session and rot fast. `accuracy` floor is 3 because a doc with wrong file paths is worse than no doc.

## Scoring guidance

- **5** — near-perfect. Reads like the project author wrote it on a sharp day.
- **4** — solid. Minor edits. The default for "good doc-sync output."
- **3** — usable but bloated, hedge-y, or structurally off.
- **2** — significant rework. Long, generic, or factually loose.
- **1** — unusable. Fabricated content, AI-tone dump, or wrong format entirely.
