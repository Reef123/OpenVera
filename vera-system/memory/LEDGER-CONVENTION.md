# Ledger Convention — reconcile-and-age

*The house rule for any harness ledger: a place where the harness records something that needs to survive a run, get older if unaddressed, and eventually force a human decision. Extracted 2026-07 from two proven instances: the private tree's `curate-flags.md` (tier-1, human-facing) and this tree's `promotions.tsv` (tier-2, machine-facing). Two instances is the anti-premature-abstraction threshold — see `openvera-v1.21-architecture.md` decision 5.*

## Two tiers, one idea

⚠ **OPEN DECISION FOR REVIEWER/SHAREEF — do not treat as settled.** The architecture doc's decision 2 specified a single convention: "md tables + shared lint." This doc instead proposes a **two-tier split**, because `promotions.tsv` already exists in this exact shape and rewriting it as markdown would be pure churn for a script-only consumer. The split below is the honest reconciliation, not a silent substitution — confirm or override at the reviewer gate.

- **Tier 1 — human-facing ledgers.** Flags a person reads and makes park-or-kill calls on. Format: **markdown table**, human-readable in place, boot/cockpit render it directly with no parsing step. Example: `curate-flags.md` (created by a parallel work item, not this one).
- **Tier 2 — machine ledgers.** Rows a script pattern-matches against; humans rarely read the raw file. Format: **tsv + script**, the existing `promotions.tsv` + `curate-mode.py` (`load_ledger` / `record_promotion` / `check_promotions`) precedent. **Stays exactly as-is** — this convention does not change it, only names the pattern it already follows.

Same lifecycle rules apply to both tiers (below); only the substrate and the validator differ. `ledger-lint.py` (this port) validates **tier 1 only** — it reuses nothing from `curate-mode.py`'s tsv path, and the tsv path is not touched by this work item.

## Lifecycle (identical both tiers)

1. **New row** → add it, age (`Runs survived`) starts at 1.
2. **Survives a run** → increment age. **Reconcile against existing rows first — never re-derive from scratch.** The same underlying issue, even reworded by a later run, is the same row: update it, don't append a duplicate.
3. **Resolved** → mark `resolved: <one-line proof>` in Status, the row persists one more run for visibility, then gets deleted.
4. **Row numbers are never reused.** A deleted row retires its number permanently — the numbering is an audit trail, not a compaction target.
5. **Escalation** → age (`Runs survived`) ≥ 3 → the row claims a boot slot as a park-or-kill ask, **subject to the consequence-gate below.**

## The consequence-gate

Every tier-1 row carries a **`Consequence`** column: what it costs the user if the row is left unaddressed. **A row may only claim a boot slot if `Consequence` names a real, concrete cost** (a blank cell or `none — cosmetic` never escalates; the lint requires the cell be non-empty at age ≥3 so the no-consequence call is always explicit, never an omission). Cosmetic or tidiness flags (no real consequence) stay recorded in the ledger and visible in whatever report reads it — they simply never interrupt, no matter how old they get. This is the kill-date rule (`feedback_kill_dates_trigger_urgency`) applied to flags: no named consequence, no nag.

`ledger-lint.py` enforces this mechanically: **a row at age ≥ 3 with an empty `Consequence` is a lint ERROR** — either the row earns a real consequence or it has no business escalating.

⚠ **Honesty note, per independent review 2026-07-03 (§8.5 of the build spec) — do not oversell this as a formalization.** The consequence-gate is a **NEW rule** whose first real test IS this port, not something the private tree's proven run validated. The opposite, in fact: the private `curate-flags.md`'s row #1 (cosmetic MEMORY.md index-link cleanup — no real cost named) reached age 3 on 2026-07-03 and **did** claim a boot slot under the old, gate-less rules. Under this gate, that escalation would have been suppressed. So the ledger here is "extracted from the proven instance, **plus** one new, unproven corrective rule" — not a pure write-down of what already worked.

## Consumer contract

Every ledger names, in its own header, **who reads it and when.** A ledger nothing reads is exactly the failure class this release is fixing (write-only harness output) — it is forbidden. Concretely: `curate-flags.md` is read by `/curate` (writer + reconciler) and by boot (age ≥3 park-or-kill check); `promotions.tsv` is read/written by `curate-mode.py`'s promotion commands only.

## Required tier-1 columns

`ledger-lint.py` requires these columns, in any order, on any tier-1 ledger it validates: **`#`, `Flag`, `First seen`, `Runs survived`, `Consequence`, `Status`, `Notes`.**
