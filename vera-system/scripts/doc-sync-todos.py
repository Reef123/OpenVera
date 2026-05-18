#!/usr/bin/env python3
"""Scan session text for missed TODOs and untracked action items.

Usage: python3 scripts/doc-sync-todos.py <state-file> [roadmap-file]
       echo "session text" | python3 scripts/doc-sync-todos.py <state-file>

Reads session context from stdin (pipe conversation summary).
Checks referenced files exist. Cross-references against state.md NEXT.
"""
import re
import sys
import os
from pathlib import Path

TODO_PATTERNS = [
    (r'\bTODO[:\s]', "explicit TODO"),
    (r'\bneed to\b', "need to"),
    (r'\bstill need\b', "still need"),
    (r'\bblocked on\b', "blocked on"),
    (r'\bbefore we can\b', "dependency"),
    (r'\bnext time\b', "deferred"),
    (r'\bfollow.up\b', "follow-up"),
    (r"(?:I'll|we'll|let me|I should|we should)\s+(?:create|add|build|fix|update|write|make)", "promise"),
    (r'\bpending\b', "pending"),
    (r"don't forget", "reminder"),
    (r'\bwant me to\b.*\?', "open question"),
]

FILE_REF_PATTERN = re.compile(r'`([^`\s]+\.(?:md|json|py|ts|js|yaml|yml|sh|toml))`')

def extract_next_items(state_file):
    """Extract items from state.md NEXT section."""
    try:
        content = Path(state_file).read_text()
        next_match = re.search(r'\*\*NEXT:\*\*\s*(.*?)(?:\n\n|\n##)', content, re.DOTALL)
        if next_match:
            return next_match.group(1).lower()
        return ""
    except Exception:
        return ""

def scan_todos(text):
    """Find potential TODOs in session text."""
    findings = []
    for line_num, line in enumerate(text.split('\n'), 1):
        for pattern, category in TODO_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                clean = line.strip()[:120]
                if clean and not clean.startswith('#') and not clean.startswith('|'):
                    findings.append({
                        "line": line_num,
                        "category": category,
                        "text": clean
                    })
                break  # one match per line
    return findings

def check_referenced_files(text):
    """Find file references and check if they exist."""
    missing = []
    for match in FILE_REF_PATTERN.finditer(text):
        filepath = match.group(1)
        if not filepath.startswith('http') and not filepath.startswith('{'):
            if not os.path.exists(filepath):
                # try with vera-system prefix
                alt = os.path.join("vera-system", filepath)
                if not os.path.exists(alt):
                    missing.append(filepath)
    return missing

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 doc-sync-todos.py <state-file> [roadmap-file]")
        print("Pipe session text via stdin.")
        sys.exit(1)

    state_file = sys.argv[1]
    next_items = extract_next_items(state_file)

    # Read session text from stdin
    if not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        print("No stdin input. Pipe session summary text.")
        sys.exit(1)

    todos = scan_todos(text)
    missing_files = check_referenced_files(text)

    # Filter out TODOs already in NEXT
    untracked = []
    for todo in todos:
        text_lower = todo["text"].lower()
        # crude check: if key words from the TODO appear in NEXT, skip
        words = set(re.findall(r'\w{4,}', text_lower))
        next_words = set(re.findall(r'\w{4,}', next_items))
        overlap = words & next_words
        if len(overlap) < 2:  # fewer than 2 shared words = probably not tracked
            untracked.append(todo)

    # Output
    if not untracked and not missing_files:
        print("No missed TODOs detected.")
        return

    if untracked:
        print(f"POTENTIAL MISSED TODOs ({len(untracked)}):")
        for t in untracked:
            print(f"  [{t['category']}] {t['text']}")

    if missing_files:
        print(f"\nREFERENCED FILES NOT FOUND ({len(missing_files)}):")
        for f in missing_files:
            print(f"  {f}")

if __name__ == "__main__":
    main()
