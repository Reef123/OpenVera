#!/usr/bin/env python3
"""
curate-mode.py — deterministic helpers for /curate.

Two subcommands cover the mechanical parts of /curate that the model used to
do freehand (and the path resolution it routinely got wrong):

  mode
      Count memory files across both stores (auto-memory under
      ~/.claude/projects/<this repo>/memory/ + harness memory_dir) and print:
        MODE=LIGHT|FULL
        AUTO_MEMORY=<resolved path or NONE>
        AUTO_FILES=<n>
        HARNESS_FILES=<n>
        TOTAL=<n>
      < 10 files -> LIGHT, 10+ -> FULL.  (Decision unchanged from the prose.)

  graduation
      Walk {projects_dir}/*/CLAUDE.md. For each project with status: shipped,
      count commits in the project dir over the last 30 days and the age of
      build-state.md. Print one FLAGGED line per project where commits >= 3 AND
      build-state.md is >= 30 days stale (the "real use without /build full"
      signal). Read-only — never edits status; the user decides per project.

  age
      Print AGE_DAYS=<n> — days since .claude/last-curate-date. -1 if the
      file is missing or unparseable. Used by /doc-sync to decide whether to
      spawn a background /curate (> 7 = overdue).

  sizes
      Check boot-tier files against the line caps in vera_config.SIZE_THRESHOLDS.
      Prints OK, or one "OVER file=<f> lines=<n> cap=<c>" line per breach.
      MEMORY.md over cap means silent truncation at load time — /curate must
      not commit while it's over.

  promotions record --match "<kw>" --pattern "<ref>"
      Record a human promotion (lessons.md group -> patterns.md) in the
      machine ledger memory/promotions.tsv as PROVISIONAL. Idempotent per
      match keyword. Prints RECORDED or EXISTS. Exit 1 on write failure —
      the skill must NOT prune that lesson group when record fails.

  promotions check
      Verify promoted lessons stopped recurring. Case-insensitive literal
      substring match against lessons.md lines dated strictly after the
      promotion date. Prints one line per row: RECURRED / CLEAN / VALIDATED /
      FAILED (or NO_PROMOTIONS). PROVISIONAL rows flip to VALIDATED after
      14 clean days, or to FAILED on recurrence; VALIDATED rows are
      re-checked every run. Always exit 0 — informational, never blocks.

The judgment in /curate (what to prune, dedupe, promote) stays in the skill.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path

from vera_config import repo_root, get_path, check_file_sizes

GRADUATION_COMMITS = 3
GRADUATION_STALE_DAYS = 30
LIGHT_THRESHOLD = 10
VALIDATION_CLEAN_DAYS = 14
PROMOTIONS_HEADER = "date_promoted\tmatch\tpattern_ref\tstatus\tstatus_date\tnote"
PROMOTION_STATUSES = ("PROVISIONAL", "VALIDATED", "FAILED")
LESSON_LINE_RE = re.compile(r"^-\s+(\d{4}-\d{2}-\d{2})\s+(.+)$")


def parse_frontmatter(path: Path) -> dict:
    """Minimal YAML frontmatter reader. Mirrors project-index.py's
    parse_frontmatter (kept inline because that file's hyphenated name can't
    be imported as a module)."""
    text = path.read_text()
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    data = {}
    for line in match.group(1).strip().split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            value = value.split("#", 1)[0].strip()  # drop inline comment
            data[key.strip()] = None if value == "null" else value
    return data


def auto_memory_dir() -> Path | None:
    """Resolve this repo's Claude Code auto-memory dir under ~/.claude/projects/.
    Claude Code encodes the absolute project path by replacing non-alphanumeric
    runs with single dashes. Try that directly, then fall back to matching by
    the repo's leaf directory name. Returns None on a fresh install (no dir)."""
    base = Path.home() / ".claude" / "projects"
    if not base.is_dir():
        return None
    root = repo_root()
    encoded = re.sub(r"[^A-Za-z0-9]+", "-", str(root))
    direct = base / encoded / "memory"
    if direct.is_dir():
        return direct
    leaf = re.sub(r"[^A-Za-z0-9]+", "-", root.name).lower()
    if leaf:
        for d in sorted(base.iterdir()):
            if d.is_dir() and leaf in d.name.lower() and (d / "memory").is_dir():
                return d / "memory"
    return None


def count_md(directory: Path | None) -> int:
    if not directory or not directory.is_dir():
        return 0
    return sum(1 for _ in directory.glob("*.md"))


def cmd_mode(_args) -> None:
    auto = auto_memory_dir()
    auto_n = count_md(auto)
    harness = repo_root() / get_path("memory_dir")
    harness_n = count_md(harness)
    total = auto_n + harness_n
    print(f"MODE={'LIGHT' if total < LIGHT_THRESHOLD else 'FULL'}")
    print(f"AUTO_MEMORY={auto if auto else 'NONE'}")
    print(f"AUTO_FILES={auto_n}")
    print(f"HARNESS_FILES={harness_n}")
    print(f"TOTAL={total}")


def cmd_graduation(_args) -> None:
    projects_dir = repo_root() / get_path("projects_dir")
    if not projects_dir.is_dir():
        return
    now = time.time()
    flagged = 0
    for pd in sorted(projects_dir.iterdir()):
        if not pd.is_dir():
            continue
        claude_md = pd / "CLAUDE.md"
        if not claude_md.exists():
            continue
        if parse_frontmatter(claude_md).get("status") != "shipped":
            continue
        try:
            out = subprocess.run(
                ["git", "log", "--since=30 days ago", "--oneline", "--", str(pd)],
                cwd=str(repo_root()), capture_output=True, text=True, timeout=15,
            )
            commits = sum(1 for line in out.stdout.splitlines() if line.strip())
        except (subprocess.SubprocessError, OSError) as exc:
            # Narrow catch: a real bug (TypeError etc.) should surface, not
            # masquerade as "no commits."
            print(f"graduation: git log failed for {pd.name}: {exc} — treating as 0 commits", file=sys.stderr)
            commits = 0
        build_state = pd / "build-state.md"
        age_days = int((now - build_state.stat().st_mtime) // 86400) if build_state.exists() else 0
        if commits >= GRADUATION_COMMITS and age_days >= GRADUATION_STALE_DAYS:
            slug = parse_frontmatter(claude_md).get("slug") or pd.name
            print(
                f"{slug}: status: shipped, {commits} commits in last 30d, "
                f"build-state.md last touched {age_days} days ago. "
                f"Consider /build full {slug} (sets status: live) or edit CLAUDE.md status: live."
            )
            flagged += 1
    if flagged == 0:
        print("No V0-graduation candidates.", file=sys.stderr)


def cmd_age(_args) -> None:
    curate_file = repo_root() / ".claude" / "last-curate-date"
    age = -1
    if curate_file.exists():
        try:
            from datetime import datetime
            curate_date = datetime.strptime(curate_file.read_text().strip(), "%Y-%m-%d")
            age = (datetime.now() - curate_date).days
        except (ValueError, OSError):
            age = -1
    print(f"AGE_DAYS={age}")


def cmd_sizes(_args) -> None:
    over = check_file_sizes()
    if not over:
        print("OK")
        return
    for rel, lines, cap in over:
        print(f"OVER file={rel} lines={lines} cap={cap}")
    # Nonzero exit so skill steps and CI can gate on it mechanically.
    sys.exit(1)


# --- promotions: the validated-promotion ledger -----------------------------
# Pure functions take explicit paths + today so tests can point them at
# tempfile fixtures (this script resolves repo_root() from its own location).


def promotions_path() -> Path:
    return repo_root() / get_path("memory_dir") / "promotions.tsv"


def lessons_path() -> Path:
    return repo_root() / get_path("memory_dir") / "lessons.md"


def sanitize_field(value: str) -> str:
    """TSV field hygiene: collapse tabs/newlines to spaces, strip."""
    return re.sub(r"[\t\r\n]+", " ", value).strip()


def parse_lesson_line(line: str):
    """`- YYYY-MM-DD [context] lesson` -> (date, text). None for anything
    malformed (undated prose, impossible dates) — never raises."""
    match = LESSON_LINE_RE.match(line)
    if not match:
        return None
    try:
        when = datetime.strptime(match.group(1), "%Y-%m-%d").date()
    except ValueError:
        return None
    return when, match.group(2)


def read_lessons(path: Path) -> list:
    try:
        text = path.read_text()
    except OSError:
        print("promotions: lessons.md unreadable, treating as no recurrences", file=sys.stderr)
        return []
    parsed = (parse_lesson_line(line) for line in text.splitlines())
    return [entry for entry in parsed if entry]


def load_ledger(path: Path):
    """Returns (raw_lines, rows) — rows maps raw-line index to a parsed dict.
    Malformed rows are skipped with a stderr note but preserved verbatim on
    any rewrite. Never raises on content; OSError means no ledger."""
    try:
        raw = path.read_text().splitlines()
    except OSError:
        return [], {}
    rows = {}
    for i, line in enumerate(raw):
        if not line.strip():
            continue
        if i == 0 and line.startswith("date_promoted"):
            continue
        fields = line.split("\t")
        if len(fields) != 6 or fields[3] not in PROMOTION_STATUSES:
            print(f"promotions: skipped malformed ledger row {i + 1}", file=sys.stderr)
            continue
        try:
            promoted = datetime.strptime(fields[0], "%Y-%m-%d").date()
        except ValueError:
            print(f"promotions: skipped malformed ledger row {i + 1}", file=sys.stderr)
            continue
        rows[i] = {
            "date_promoted": promoted,
            "match": fields[1],
            "pattern_ref": fields[2],
            "status": fields[3],
            "status_date": fields[4],
            "note": fields[5],
        }
    return raw, rows


def record_promotion(ledger: Path, match: str, pattern: str, today: date) -> str:
    """Append a PROVISIONAL row. Idempotent: an existing PROVISIONAL or
    VALIDATED row with the same match (case-insensitive) is left alone —
    curate re-detects the same promotion weekly and double rows would
    double-count. OSError propagates to the caller."""
    _, rows = load_ledger(ledger)
    for row in rows.values():
        if row["match"].lower() == match.lower() and row["status"] in ("PROVISIONAL", "VALIDATED"):
            return f'EXISTS match="{match}" status={row["status"]}'
    ledger.parent.mkdir(parents=True, exist_ok=True)
    write_header = not ledger.exists()
    with ledger.open("a") as handle:
        if write_header:
            handle.write(PROMOTIONS_HEADER + "\n")
        handle.write(f"{today.isoformat()}\t{match}\t{pattern}\tPROVISIONAL\t-\t-\n")
    return f'RECORDED match="{match}" pattern="{pattern}" date={today.isoformat()}'


def check_promotions(ledger: Path, lessons_file: Path, today: date):
    """Returns (output_lines, ledger_changed). Recurrence = a lessons.md line
    dated STRICTLY AFTER the promotion date whose text contains the match
    (case-insensitive). Same-day lines are the promoted group itself —
    counting them would self-flag every promotion FAILED on day one."""
    if not ledger.exists():
        return ["NO_PROMOTIONS"], False
    raw, rows = load_ledger(ledger)
    lessons = read_lessons(lessons_file)
    out = []
    changed = False
    for row in rows.values():
        needle = row["match"].lower()
        hits = [when for when, text in lessons
                if when > row["date_promoted"] and needle in text.lower()]
        since = row["date_promoted"].isoformat()
        if row["status"] == "PROVISIONAL":
            if hits:
                out.append(f'RECURRED match="{row["match"]}" n={len(hits)} since={since} last={max(hits).isoformat()}')
                row.update(status="FAILED", status_date=today.isoformat(), note="recurred")
                changed = True
            else:
                days = (today - row["date_promoted"]).days
                if days >= VALIDATION_CLEAN_DAYS:
                    out.append(f'VALIDATED match="{row["match"]}" days={days}')
                    row.update(status="VALIDATED", status_date=today.isoformat())
                    changed = True
                else:
                    out.append(f'CLEAN match="{row["match"]}" days={days}')
        elif row["status"] == "VALIDATED":
            # Re-checked every run: cheap, and catches late regressions.
            if hits:
                out.append(f'RECURRED match="{row["match"]}" n={len(hits)} since={since} last={max(hits).isoformat()} late=1')
                row.update(status="FAILED", status_date=today.isoformat(), note="recurred after validation")
                changed = True
        else:  # FAILED — resurfaces every run until the human acts.
            out.append(f'FAILED match="{row["match"]}" since={row["status_date"]}')
    if changed:
        for idx, row in rows.items():
            raw[idx] = "\t".join([
                row["date_promoted"].isoformat(), row["match"], row["pattern_ref"],
                row["status"], row["status_date"], row["note"],
            ])
        try:
            ledger.write_text("\n".join(raw) + "\n")
        except OSError as exc:
            print(f"WARNING: ledger not updated ({exc}), statuses will be re-derived next run", file=sys.stderr)
    return out, changed


def cmd_promotions_record(args) -> None:
    match = sanitize_field(args.match)
    pattern = sanitize_field(args.pattern)
    if not match:
        print("ERROR: match is empty after sanitization", file=sys.stderr)
        sys.exit(1)
    try:
        print(record_promotion(promotions_path(), match, pattern, date.today()))
    except OSError as exc:
        # Deliberately NOT a soft-fail: the skill skips pruning the lesson
        # group when record fails, so the nonzero exit is load-bearing.
        print(f"ERROR: promotion not recorded ({exc})", file=sys.stderr)
        sys.exit(1)


def cmd_promotions_check(_args) -> None:
    lines, _ = check_promotions(promotions_path(), lessons_path(), date.today())
    for line in lines:
        print(line)


def main() -> None:
    parser = argparse.ArgumentParser(description="Deterministic /curate helpers")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("mode", help="count memory files -> LIGHT/FULL").set_defaults(func=cmd_mode)
    sub.add_parser("graduation", help="flag shipped projects in real use").set_defaults(func=cmd_graduation)
    sub.add_parser("age", help="days since last curate -> AGE_DAYS=<n>").set_defaults(func=cmd_age)
    sub.add_parser("sizes", help="boot-tier file line caps -> OK or OVER lines").set_defaults(func=cmd_sizes)
    promo = sub.add_parser("promotions", help="promotion ledger: record + verify")
    promo_sub = promo.add_subparsers(dest="promo_cmd", required=True)
    rec = promo_sub.add_parser("record", help="record a human promotion to patterns.md")
    rec.add_argument("--match", required=True, help="literal keyword that identifies the recurring lesson")
    rec.add_argument("--pattern", required=True, help="patterns.md heading or short ref")
    rec.set_defaults(func=cmd_promotions_record)
    chk = promo_sub.add_parser("check", help="verify promoted lessons stopped recurring")
    chk.set_defaults(func=cmd_promotions_check)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
