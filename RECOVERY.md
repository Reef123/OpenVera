# Recovery

When something in the harness breaks. Try the matching path.

---

## SessionStart hook printed an error

Look at the error. The hook checks three things: bootstrap, config, curate timestamp.

```
CONFIG MISSING: ...
```
Run `bash bootstrap.sh` from repo root.

```
CONFIG BROKEN: ... is invalid JSON ...
```
Open `vera-system/config.json`, fix the JSON, save.

```
Curate overdue (N days) — spawn /curate as background agent.
```
Not an error — informational. Run `/curate` when convenient.

---

## `/curate` doesn't resolve / hook can't find timestamp

If `/curate` is missing, you're probably on a fork that pre-dates the 2026-04-21 rename. Pull the latest, or use `git log --all --oneline | grep curate:` to confirm the rename commits are present.

If the hook complains the timestamp file is missing:

```bash
# Seed it to today (replace YYYY-MM-DD)
mkdir -p .claude && date +%Y-%m-%d > .claude/last-curate-date
```

---

## Bootstrap is wedged

If `bash bootstrap.sh` halfway-through-failed and you're in a weird state:

```bash
rm .claude/bootstrapped       # forces first-run.md to load again
bash bootstrap.sh             # re-run cleanly
```

`first-run.md` won't load again until `.claude/bootstrapped` exists. So the order matters.

---

## Doctor says everything's wrong

```bash
python3 vera-system/scripts/doctor.py
```

Read the warnings + errors. Each one names the file or path that's broken. Fix in this order:
1. CONFIG_MISSING / CONFIG_BROKEN first
2. State.md / patterns.md missing
3. Curate timestamp issues
4. Script inventory complaints

Doctor is read-only. It never modifies your files.

---

## Last resort

```bash
# Wipe local state, keep the source
rm -rf .claude/bootstrapped .claude/last-curate-date .claude/settings.local.json
bash bootstrap.sh
```

This rebuilds the per-user state files from the source-tracked templates without touching your project work in `vera-projects/`.
