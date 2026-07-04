#!/usr/bin/env python3
"""
ledger-lint.py — validator for tier-1 (markdown-table) ledgers.

Per LEDGER-CONVENTION.md: tier-1 ledgers (curate-flags.md and any future
human-facing reconcile-and-age ledger) are markdown tables. Checks: required
columns present, no duplicate row numbers, no malformed age/status values, no
row escalating past age 3 without a named Consequence, relative markdown
links resolve on disk. MD-TIER ONLY — does not touch promotions.tsv/curate-mode.py.

Usage: python3 vera-system/scripts/ledger-lint.py <path/to/ledger.md>
Output: "OK ledger=<path>" or one "ERROR <problem>" line per issue.
Exit 0 clean / 1 on any error.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED_COLUMNS = ["#", "Flag", "First seen", "Runs survived", "Consequence", "Status", "Notes"]
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def _split_row(line: str) -> list:
    """Split a markdown table row into trimmed cells, dropping the leading
    and trailing empty cells produced by the outer pipes."""
    cells = line.strip().split("|")
    if cells and cells[0].strip() == "":
        cells = cells[1:]
    if cells and cells[-1].strip() == "":
        cells = cells[:-1]
    return [c.strip() for c in cells]


def _is_separator(cells: list) -> bool:
    return all(re.fullmatch(r":?-+:?", c) for c in cells if c)


def find_table(lines: list):
    """Returns (header_cells, data_rows) for the first markdown table found,
    or (None, []) if no table is present. data_rows is a list of
    (line_no, cells) for every row after the header/separator pair."""
    for i, line in enumerate(lines):
        if line.strip().startswith("|") and i + 1 < len(lines):
            header = _split_row(line)
            sep = _split_row(lines[i + 1])
            if sep and _is_separator(sep):
                rows = []
                for j in range(i + 2, len(lines)):
                    if not lines[j].strip().startswith("|"):
                        break
                    rows.append((j + 1, _split_row(lines[j])))
                return header, rows
    return None, []


def lint_file(path: Path) -> list:
    """Returns a list of human-readable ERROR strings. Empty = clean.
    Never raises: unreadable file is itself an error, not a crash."""
    try:
        text = path.read_text()
    except OSError as exc:
        return [f"cannot read {path}: {exc}"]

    lines = text.splitlines()
    header, rows = find_table(lines)
    if header is None:
        return ["no markdown table found in ledger"]

    problems = []
    missing = [c for c in REQUIRED_COLUMNS if c not in header]
    for col in missing:
        problems.append(f'missing_column="{col}"')
    if missing:
        return problems  # can't map columns to indices reliably

    idx = {col: header.index(col) for col in REQUIRED_COLUMNS}
    seen_numbers = set()
    base_dir = path.parent

    for line_no, cells in rows:
        if len(cells) < len(header):
            problems.append(f"malformed_row line={line_no} (expected {len(header)} columns, got {len(cells)})")
            continue

        num_raw = cells[idx["#"]]
        if num_raw and num_raw in seen_numbers:
            problems.append(f"duplicate_row_number={num_raw}")
        elif num_raw:
            seen_numbers.add(num_raw)

        runs_raw = cells[idx["Runs survived"]]
        runs_match = re.search(r"\d+", runs_raw)
        if not runs_match:
            problems.append(f'malformed_runs_survived row={num_raw or line_no} value="{runs_raw}"')
            runs = None
        else:
            runs = int(runs_match.group())

        status = cells[idx["Status"]]
        if not status or not re.match(r"(?i)^(open|resolved|killed)\b", status):
            problems.append(f'malformed_status row={num_raw or line_no} value="{status}"')

        consequence = cells[idx["Consequence"]].strip()
        if runs is not None and runs >= 3 and not consequence:
            problems.append(f"escalation_without_consequence row={num_raw or line_no} runs_survived={runs}")

        for cell in cells:
            for link in LINK_RE.findall(cell):
                if link.startswith(("http://", "https://", "#")):
                    continue
                target = (base_dir / link.split("#")[0]).resolve()
                if not target.exists():
                    problems.append(f'broken_link row={num_raw or line_no} link="{link}"')

    return problems


def main():
    parser = argparse.ArgumentParser(description="Validate a tier-1 markdown ledger")
    parser.add_argument("path", help="path to the ledger .md file")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"ERROR no_file path={path}")
        sys.exit(1)

    problems = lint_file(path)
    if not problems:
        print(f"OK ledger={path}")
        sys.exit(0)
    for p in problems:
        print(f"ERROR {p}")
    sys.exit(1)


if __name__ == "__main__":
    main()
