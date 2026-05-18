#!/usr/bin/env python3
"""
Stamp a harness doc with a "last update" line right under the H1 title.

Usage:
  python3 vera-system/scripts/stamp.py <file> <tool>

Example:
  python3 vera-system/scripts/stamp.py vera-system/state.md /curate

Behavior:
- Inserts `_Last update: YYYY-MM-DD HH:MM — By: <tool>_` as the line after the H1.
- If a stamp already exists in that position, overwrites it.
- If no H1 is found, prepends a stamp at the top.
- Idempotent: running twice in the same minute is a no-op.

Use from any automation that writes harness docs (curate, doc-sync, future tools).
"""
import re
import sys
from datetime import datetime
from pathlib import Path

STAMP_RE = re.compile(r"^_Last update: .+ — By: .+_\s*$")
H1_RE = re.compile(r"^# .+")


def stamp(path: Path, tool: str) -> None:
    if not path.exists():
        sys.exit(f"stamp: {path} does not exist")

    lines = path.read_text().splitlines()
    new_stamp = f"_Last update: {datetime.now().strftime('%Y-%m-%d %H:%M')} — By: {tool}_"

    h1_idx = next((i for i, l in enumerate(lines) if H1_RE.match(l)), None)

    if h1_idx is None:
        lines = [new_stamp, ""] + lines
    else:
        insert_at = h1_idx + 1
        # Skip a single blank line after the H1 if present, then check for an existing stamp
        probe = insert_at
        if probe < len(lines) and lines[probe].strip() == "":
            probe += 1
        if probe < len(lines) and STAMP_RE.match(lines[probe]):
            lines[probe] = new_stamp
        else:
            lines = lines[: h1_idx + 1] + ["", new_stamp] + lines[h1_idx + 1 :]

    path.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: stamp.py <file> <tool>")
    stamp(Path(sys.argv[1]), sys.argv[2])
