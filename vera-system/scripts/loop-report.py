#!/usr/bin/env python3
"""
loop-report.py — measure the learning loop.

Answers the question a harness should be able to answer about itself: what
does cycle N know that cycle 1 didn't? Reads the loop's own artifacts
(lessons.md, promotions.tsv, patterns.md, runs/*-telemetry.tsv, git history)
and prints a short markdown report. Also appends one trend row per run to
runs/loop-report.tsv so the numbers accumulate over time.

Usage:
    python3 vera-system/scripts/loop-report.py

No flags. Read-only except the trend row, which soft-fails like telemetry.
Always exits 0.
"""
from __future__ import annotations

import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SYSTEM_DIR = SCRIPT_DIR.parent
REPO_ROOT = SYSTEM_DIR.parent

sys.path.insert(0, str(SCRIPT_DIR))
from vera_config import get_path  # noqa: E402

RUNS_DIR = REPO_ROOT / "vera-system" / "runs"
WINDOW_DAYS = 30
SUMMARY_HEADER = (
    "date\tlessons_total\tlessons_30d\tpromotions_provisional\tpromotions_validated"
    "\tpromotions_failed\ttelemetry_runs_30d\tpass_rate_30d\tharness_commits_30d"
)
LESSON_LINE_RE = re.compile(r"^-\s+(\d{4}-\d{2}-\d{2})\s+(.+)$")
PASS_OUTCOMES = {"PASS", "WIN"}
FAIL_OUTCOMES = {"SOFT_FAIL", "HARD_FAIL", "LOSS"}


def _parse_date(text: str):
    """Tolerant date parse: first 10 chars as YYYY-MM-DD. Handles telemetry
    timestamps with time suffixes, trailing Z, fractional seconds."""
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_lessons(path: Path, today: date):
    """(total, last_30d) dated lesson lines. Malformed lines skipped."""
    try:
        text = path.read_text()
    except OSError:
        return 0, 0
    cutoff = today - timedelta(days=WINDOW_DAYS)
    total = 0
    recent = 0
    for line in text.splitlines():
        match = LESSON_LINE_RE.match(line)
        if not match:
            continue
        when = _parse_date(match.group(1))
        if when is None:
            continue
        total += 1
        if when >= cutoff:
            recent += 1
    return total, recent


def parse_promotions(path: Path):
    """Counts per status. Malformed rows skipped silently (promotions check
    is the place that reports them)."""
    counts = {"PROVISIONAL": 0, "VALIDATED": 0, "FAILED": 0}
    try:
        lines = path.read_text().splitlines()
    except OSError:
        return counts
    for line in lines:
        fields = line.split("\t")
        if len(fields) == 6 and fields[3] in counts and _parse_date(fields[0]):
            counts[fields[3]] += 1
    return counts


def count_patterns(path: Path) -> int:
    try:
        text = path.read_text()
    except OSError:
        return 0
    return sum(1 for line in text.splitlines() if line.startswith("## "))


def telemetry_summary(runs_dir: Path, today: date):
    """Per-skill activity in the window: {skill: (runs_30d, passes, fails)}.
    Malformed rows skipped; SKIP rows excluded from the pass rate."""
    summary = {}
    if not runs_dir.is_dir():
        return summary
    cutoff = today - timedelta(days=WINDOW_DAYS)
    for tsv in sorted(runs_dir.glob("*-telemetry.tsv")):
        skill = tsv.name[: -len("-telemetry.tsv")]
        runs = passes = fails = 0
        try:
            lines = tsv.read_text().splitlines()
        except OSError:
            continue
        for line in lines[1:]:
            fields = line.split("\t")
            if len(fields) < 6:
                continue
            when = _parse_date(fields[0])
            if when is None or when < cutoff:
                continue
            runs += 1
            outcome = fields[5]
            if outcome in PASS_OUTCOMES:
                passes += 1
            elif outcome in FAIL_OUTCOMES:
                fails += 1
        if runs:
            summary[skill] = (runs, passes, fails)
    return summary


def harness_commits():
    """Commits touching the harness in the window, or None if git is
    unavailable. Narrow catch: a real bug should surface."""
    try:
        out = subprocess.run(
            ["git", "log", f"--since={WINDOW_DAYS} days ago", "--oneline",
             "--", "vera-system", ".claude", "tests"],
            cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=15,
        )
        return sum(1 for line in out.stdout.splitlines() if line.strip())
    except (subprocess.SubprocessError, OSError):
        return None


def _pass_rate(summary):
    """Overall pass rate across skills, or None when nothing is scoreable."""
    passes = sum(p for _, p, _ in summary.values())
    fails = sum(f for _, _, f in summary.values())
    if passes + fails == 0:
        return None
    return round(100 * passes / (passes + fails))


def build_report(today, lessons_total, lessons_recent, promos, patterns_n, summary, commits):
    validated = promos["VALIDATED"]
    failed = promos["FAILED"]
    promoted = promos["PROVISIONAL"] + validated + failed
    runs_total = sum(r for r, _, _ in summary.values())
    rate = _pass_rate(summary)
    rate_text = f"{rate}% pass" if rate is not None else "no scoreable runs"
    lines = [
        f"**Loop report {today.isoformat()}.** Since cycle 1 the loop has captured "
        f"{lessons_total} lessons ({lessons_recent} in the last {WINDOW_DAYS} days), "
        f"promoted {promoted} into patterns ({validated} validated, {failed} failed), "
        f"and run {runs_total} skill invocations in the last {WINDOW_DAYS} days ({rate_text}).",
        "",
        f"- Lessons: {lessons_total} captured, {lessons_recent} in the window.",
        f"- Promotions: {promos['PROVISIONAL']} provisional, {validated} validated, "
        f"{failed} failed. Patterns on file: {patterns_n}.",
    ]
    if summary:
        lines.append("")
        lines.append("| Skill | Runs (30d) | Pass rate |")
        lines.append("|-------|-----------|-----------|")
        for skill in sorted(summary):
            runs, passes, fails = summary[skill]
            scoreable = passes + fails
            skill_rate = f"{round(100 * passes / scoreable)}%" if scoreable else "n/a"
            lines.append(f"| {skill} | {runs} | {skill_rate} |")
    lines.append("")
    if commits is None:
        lines.append("- Harness changes: git unavailable.")
    else:
        lines.append(f"- Harness changes: {commits} commits in the last {WINDOW_DAYS} days.")
    return "\n".join(lines)


def append_summary_row(today, lessons_total, lessons_recent, promos, summary, commits):
    rate = _pass_rate(summary)
    row = "\t".join([
        today.isoformat(),
        str(lessons_total),
        str(lessons_recent),
        str(promos["PROVISIONAL"]),
        str(promos["VALIDATED"]),
        str(promos["FAILED"]),
        str(sum(r for r, _, _ in summary.values())),
        str(rate) if rate is not None else "-",
        str(commits) if commits is not None else "-",
    ])
    tsv_path = RUNS_DIR / "loop-report.tsv"
    try:
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        if not tsv_path.exists():
            tsv_path.write_text(SUMMARY_HEADER + "\n")
        with open(tsv_path, "a") as handle:
            handle.write(row + "\n")
    except OSError as exc:
        print(f"WARNING: loop-report row not logged ({exc}), continuing", file=sys.stderr)


def main():
    today = date.today()
    memory_dir = REPO_ROOT / get_path("memory_dir")
    lessons_total, lessons_recent = parse_lessons(memory_dir / "lessons.md", today)
    promos = parse_promotions(memory_dir / "promotions.tsv")
    patterns_n = count_patterns(memory_dir / "patterns.md")
    summary = telemetry_summary(RUNS_DIR, today)
    commits = harness_commits()
    print(build_report(today, lessons_total, lessons_recent, promos, patterns_n, summary, commits))
    append_summary_row(today, lessons_total, lessons_recent, promos, summary, commits)


if __name__ == "__main__":
    main()
