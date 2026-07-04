# Curate Flags — persistent ledger

*Tier-1 ledger per `LEDGER-CONVENTION.md`. Written by `/curate` each run — the flag channel; flags live HERE, not written once into a report and forgotten. A flag carries over run to run until resolved (with proof) or killed.*

**Consumer contract:** read by `/curate` (writer + reconciler, every run) and by boot (`vera-system/CLAUDE.md` step — any row at `Runs survived` ≥ 3 with a non-empty `Consequence` claims a boot slot as a park-or-kill ask). The doc-sync cockpit health line counts rows here at read time. A ledger nothing reads is the failure class this exists to prevent.

**Rules (reconcile-and-age, identical to every tier-1 ledger):**
- New flag → add row, `Runs survived: 1`.
- Still unresolved at next run → increment `Runs survived`. Reconcile against this table first — never re-derive from scratch. Same underlying issue, even reworded, is the same row.
- Resolved → `resolved: <one-line proof>` in Status, row stays one more run for visibility, then delete.
- Recurring HALTs → one named escalating row (`HALT recurred Nx: <reason>`), never a fresh flag per run.
- **Consequence-gate (required):** every row names what it costs the user if left unaddressed. `Runs survived ≥ 3` claims a boot slot ONLY if `Consequence` is non-empty — cosmetic/tidiness flags stay recorded and visible here but never interrupt, no matter how old. `ledger-lint.py` enforces this: an escalating row with an empty `Consequence` is a lint error.
- Row numbers are never reused — a deleted row retires its number permanently.

| # | Flag | First seen | Runs survived | Consequence | Status | Notes |
|---|------|-----------|---------------|--------------|--------|-------|

*Seeded empty at v1.21 (2026-07-04) — this is a new ledger, not a migration. The first row lands on the next `/curate` run.*
