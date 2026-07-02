# Hook Map

_Last update: 2026-07-02 — By: v1.20-ship-sweep_

Inventory of every hook wired in `.claude/settings.json`. All six use the same `python3 → python → py` fallback chain so they run regardless of which interpreter name is on PATH.

## Active hooks

| Event | Script | Purpose | Fail behavior |
|-------|--------|---------|----------------|
| `SessionStart` | `.claude/hooks/session-start.py` | Clears stale runtime markers, checks bootstrap/config health, checks curate freshness (>7d nudges `/curate`), injects a boot tip + STATUS/SPRINT/NEXT summary from `state.md`. | Fail-open — a broken read just skips the injected context, session still starts. |
| `UserPromptSubmit` | `.claude/hooks/session-end-reminder.py` | Regex-matches end-of-session phrases (farewells, "we're done," compact/doc-sync mentions); on match, injects a directive to run `/doc-sync` and sets the `.session-ending` sentinel. | Always exits 0 — never blocks the prompt. |
| `PostCompact` | `.claude/hooks/post-compact.py` | Re-injects Core tier (`state.md`, `patterns.md`, `relationships/user.md`), `MEMORY.md` index, latest conversation-log pointer, and active build-state pointer (if touched <24h) as context after a compact. | Fail-open — missing files are skipped, not fatal. |
| `PreCompact` | `.claude/hooks/pre-compact.py` | Checks the `session-dirty` marker; if set, blocks the compact (`{"decision":"block"}` JSON + exit 2) so unsynced harness state isn't lost to context compression. | **Fail-closed** — also blocks (exit 2 + stderr) if the repo root can't be validated. Deliberate: guards against real data loss. |
| `PostToolUse` (`Write\|Edit\|MultiEdit\|NotebookEdit`) | `.claude/hooks/mark-dirty.py` | Touches `.claude/session-dirty` when a write targets a harness path (`.claude/`, `vera-system/`, or root `CLAUDE.md`/`README.md`/`ROADMAP.md`). Clears stale locks (>1h) so a crashed doc-sync/curate run can't permanently wedge itself. | Always exits 0. |
| `Stop` | `.claude/hooks/stop-doc-sync-gate.py` | Blocks turn-end only if `.session-ending` AND `session-dirty` are both set AND `stop_hook_active` is false. Deletes the sentinel before blocking (one-nag rule) so it can't loop-trap the turn. | **Fail-open** — fires every turn, so a false block would trap every conversation; the deliberate opposite asymmetry from `PreCompact`. |

All six validate the repo root before acting (defends against a poisoned `CLAUDE_PROJECT_DIR`). No dead hooks as of this audit (v1.20 recon, 2026-07-02) — all six read cleanly and their fail-open/fail-closed choices are documented in their own docstrings.

## Evaluated, not adopted

Considered during the v1.20 hooks-effectiveness audit. Not shipped — reasons and reopen triggers below, so these don't get re-litigated from scratch next time.

| Candidate | Verdict | Why not | Reopen trigger |
|-----------|---------|---------|-----------------|
| `state.md`-over-cap warning at `UserPromptSubmit` | Rejected | `doctor.py` (Check 11) and `doc-sync`'s size-check step (`curate-mode.py sizes`) already surface over-cap files every session/doc-sync. A third nudge at every prompt is a tool for a problem already covered twice. | Reopen if users report silent over-cap growth going unnoticed between doc-syncs (i.e., the existing checks aren't actually catching it in practice). |
| `cockpit.md` staleness check | Rejected | Doc-sync regenerates `cockpit.md` every session as part of its normal write path — there's no window for it to go stale between doc-syncs by design. | Reopen if stale cockpits are actually observed (e.g., doc-sync skipped a session and the cockpit visibly lagged state.md). |
| `SubagentStart` hook injecting the spawn-contract reminder | Rejected | `SubagentStart` as a documented Claude Code hook event is unverified — no confirmed support to build against. Building a hook for an event that may not exist is the tool-before-the-problem trap. | Reopen once Claude Code documents a `SubagentStart` (or equivalent subagent-spawn) hook event. Until then, the spawn contract is carried in each agent's own frontmatter/body (`.claude/agents/*.md`) and in `vera-system/memory/delegation-policy.md`. |
