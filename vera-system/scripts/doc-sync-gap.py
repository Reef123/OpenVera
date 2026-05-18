#!/usr/bin/env python3
"""Detect if there's a gap since the last session.

Usage: python3 scripts/doc-sync-gap.py <conversations-dir>
Output: gap info or "no gap"
"""
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 doc-sync-gap.py <conversations-dir>")
        sys.exit(1)

    conv_dir = Path(sys.argv[1])
    if not conv_dir.exists():
        print("NO_HISTORY")
        return

    # Find latest conversation file (NNN-YYYY-MM-DD.md format)
    pattern = re.compile(r'^(\d{3})-(\d{4}-\d{2}-\d{2})\.md$')
    latest_num = 0
    latest_date = None

    for f in conv_dir.iterdir():
        match = pattern.match(f.name)
        if match:
            num = int(match.group(1))
            if num > latest_num:
                latest_num = num
                latest_date = match.group(2)

    if not latest_date:
        print("NO_HISTORY")
        return

    last = datetime.strptime(latest_date, "%Y-%m-%d")
    today = datetime.now()
    gap_days = (today - last).days

    next_session = latest_num + 1

    if gap_days <= 1:
        print(f"NO_GAP session={next_session}")
    elif gap_days <= 3:
        print(f"SHORT_GAP days={gap_days} session={next_session}")
    elif gap_days <= 7:
        print(f"MEDIUM_GAP days={gap_days} session={next_session} last_date={latest_date}")
    else:
        print(f"LONG_GAP days={gap_days} session={next_session} last_date={latest_date}")

if __name__ == "__main__":
    main()
