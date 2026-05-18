---
name: code
pass_threshold: 4.0
---

## Dimensions

| Dimension       | Weight | Floor | Description |
|-----------------|--------|-------|-------------|
| build_succeeds  | 0.30   | 4     | Code runs. `npm run dev` / equivalent works without errors. |
| spec_match      | 0.25   | 3     | Implementation matches the PRD/wireframe. Visible deviations are documented. |
| code_quality    | 0.20   | 3     | Readable, no obvious anti-patterns, sensible naming, no dead code. |
| test_coverage   | 0.15   | 2     | Tests exist for the core flow. Not 100% coverage — coverage of what matters. |
| design_fidelity | 0.10   | 2     | UI matches the design system (colors, typography, spacing). |

## Floor logic

`build_succeeds` floor is 4 because broken code is unshippable regardless of other strengths. `spec_match` floor is 3 because building the wrong thing well is still wrong.

## Scoring guidance

- **5** — near-perfect. Ship as-is. Working V0 deployed to production.
- **4** — solid. Minor fixes in a follow-up PR. The default for "good V0."
- **3.5** — working V0 with rough UI. The honest score for most fast V0s.
- **3** — runs, but design or quality has noticeable gaps.
- **2** — partial functionality, broken edge cases, or visible bugs.
- **1** — doesn't run, or fundamentally diverges from the spec.

**Calibration:** A working V0 with basic UI is a 3.5, not a 4.5. Don't inflate.
