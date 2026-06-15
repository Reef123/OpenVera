# scripts/

Helper scripts called by skills, hooks, and the bootstrap.

| Script | Purpose |
|--------|---------|
| `vera_config.py` | Shared config loader — paths, LLM defaults. Used by hooks and other scripts. |
| `openrouter.py` | Multi-model queries via OpenRouter API. Reads default model from `config.json`. Supports `--search` for web grounding and `--verify` to check your key. |
| `youtube-analyze.py` | Analyze YouTube videos via native Gemini API. Reads video model from `config.json`. |
| `doctor.py` | Self-audit — config, dirs, skill drift, secrets, state freshness. |
| `telemetry.py` | Append a row to `vera-system/runs/<skill>-telemetry.tsv`. |
| `project-index.py` | Build a JSON index of `vera-projects/projects/` for the dashboard. |
| `build-state.py` | State machine for `/build` (Stage 0 → Ship). `status` lists every build-state.md; `continue [<slug>]` recovers resume context and the worktree to re-enter. |
| `manifest-update.py` | Edit `MANIFEST.md` files in `/build full` projects. |
| `artifact-lint.py` | Mandatory-section check for build artifacts (`--profile idea|handoff|contract`). Exit 1 on a missing or empty required section so the skill HARD_FAILs. |
| `score-gate.py` | Deterministic ship/regression verdict from judge JSON. `build` recomputes the composite vs the floor (catches an inflated composite); `improve` applies the WIN/LOSS + regression-band rule. |
| `gate-scan.py` | Canonical scout-gate keyword scan (`scout`). One keyword list so `/build` and `/start-vague` fire identically. |
| `doc-sync-cascade.py` | Detect file changes and which docs need cascade updates. |
| `doc-sync-gap.py` | Detect time gap since last session. |
| `doc-sync-todos.py` | Surface unfinished TODOs from conversation logs. |
| `curate-mode.py` | Deterministic /curate helpers: mode, graduation, age, sizes, promotions record/check (the promotion ledger in `memory/promotions.tsv`). |
| `loop-report.py` | Print a learning-loop report (lessons, promotions, telemetry, harness commits) and append a trend row to `runs/loop-report.tsv`. |

`bootstrap.sh` lives at the repo root, not here — it bootstraps the entire workspace, not just `vera-system/`.

## Why these are scripts, not skills

Skills are instructions for the model. Scripts are deterministic code that doesn't need model judgment — file scanning, JSON parsing, API calls with fixed shapes. Anything that would be wasteful to ask the model to do step-by-step belongs here.

Skills pre-authorize `Bash(python3 vera-system/scripts/*)`, so adding a new script makes it instantly callable without changing settings.json. Treat that as a security boundary: only put scripts here that are safe to run with that blanket permission.
