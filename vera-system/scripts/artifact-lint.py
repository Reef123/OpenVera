#!/usr/bin/env python3
"""
artifact-lint.py — deterministic mandatory-section check for build artifacts.

The skills already tell the model "this artifact MUST contain these sections" and
then trust the model to self-check. Self-checks drift: a missing `## What V0 did
NOT prove` slips through, an idea.md reaches the /build new Stage 0 interview gate
without `## The bet`. This script does the mechanical part — does the file exist,
and does it contain each required section heading with non-empty content under
it — so the HARD_FAIL has teeth instead of being a sentence the model can skip.

It checks STRUCTURE, not judgment: the model still writes the prose and decides
whether the content is good. This only catches the artifact shipping without a
mandatory section, or with the heading present but nothing under it.

Profiles (the `--profile` argument):

  idea      — idea.md before the /build new Stage 0 interview gate.
              Required: ## The bet, ## Who it's for, ## The problem
  handoff   — handoff.md, the V0->V1 contract written at Stage 4b.
              Required: ## Outcome, ## Observable behavior, ## What V0 proved,
                        ## What V0 did NOT prove, ## Open questions
  contract  — .build/contract.md, the Stage 2 build-loop contract.
              Required: ## What was built, ## Acceptance criteria, ## Out of scope
              Plus: at least one EARS `shall` clause under acceptance criteria
              (the validator greps for `shall`; no shall = nothing to verify).

Usage:
    python3 vera-system/scripts/artifact-lint.py --profile idea <path>
    python3 vera-system/scripts/artifact-lint.py --profile handoff <path>
    python3 vera-system/scripts/artifact-lint.py --profile contract <path>

Output:
    OK profile=<p> file=<path>
  or one line per problem:
    MISSING profile=<p> section="## The bet"
    EMPTY   profile=<p> section="## The problem"
    NO_FILE profile=<p> file=<path>
    NO_SHALL profile=contract                 (contract only)

Exit 0 when clean, exit 1 on any problem — the nonzero exit is load-bearing:
the calling skill HARD_FAILs (does not advance the stage) when it fires.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Each profile: ordered list of required section headings (matched
# case-insensitively, ignoring trailing parenthetical notes on the heading so
# "## Invariants (DO NOT MODIFY)" still matches "## Invariants").
PROFILES = {
    "idea": ["## The bet", "## Who it's for", "## The problem"],
    "handoff": [
        "## Outcome",
        "## Invariants",      # /build full reads these; v0-stages requires 3-7
        "## Observable behavior",
        "## What V0 proved",
        "## What V0 did NOT prove",
        "## Constraints",
        "## Open questions",
    ],
    "contract": ["## What was built", "## Acceptance criteria", "## Out of scope"],
}


def heading_key(text: str) -> str:
    """Normalize a heading for comparison: drop leading/closing hashes and a
    trailing parenthetical, collapse whitespace, lowercase.
    '## Outcome ' -> 'outcome'; '## The bet ##' -> 'the bet' (closing ATX run
    is valid CommonMark); '## Invariants (DO NOT MODIFY)' -> 'invariants'."""
    text = text.strip()
    text = re.sub(r"^#+\s*", "", text)         # strip leading hashes
    text = re.sub(r"\s+#+\s*$", "", text)      # strip optional closing ATX run
    text = re.sub(r"\s*\(.*\)\s*$", "", text)  # strip trailing (note)
    # Normalize smart punctuation (editors / OneDrive auto-convert apostrophes):
    # "## Who it’s for" must still match the straight-quote requirement.
    text = text.replace("’", "'").replace("‘", "'")
    return " ".join(text.split()).lower()


# A fence opener may carry an info string (```python); a closer may not — it is
# a same-or-longer run of the opener char followed by only whitespace.
_FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_FENCE_CLOSE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})\s*$")
# Level-2 ATX heading: up to 3 spaces indent, exactly `##` (not `###`).
_H2_RE = re.compile(r"^ {0,3}##(?!#)\s+\S")


def split_sections(text: str) -> dict:
    """Map normalized heading -> body text (everything until the next heading).
    Only level-2 (`## `) headings start a section; the `#` title and deeper
    `###` subheadings are ignored as section starts (a `### The problem` nested
    elsewhere must NOT satisfy a required `## The problem`). Up to 3 spaces of
    indent are allowed on headings and fences, per CommonMark.

    Headings inside fenced code blocks are NOT section starts — these artifacts
    embed fenced examples of their own headings (a template's `## Out of scope`
    sample), and counting those would let an artifact that pasted the template
    but never filled the real section pass clean. Fence state tracks the opener
    char + length and closes only on a same-or-longer run of the same char with
    NO info string, so a nested inner fence (``` inside ````, or a ```python
    line inside a ``` block) does not prematurely reopen the doc.

    Note: ATX headings only. Setext headings (underlined with === / ---) are not
    recognized; the failure direction is conservative (a required section would
    read as MISSING, failing closed)."""
    sections = {}
    current = None
    buf = []
    fence = None  # (char, length) of the open fence, or None
    for line in text.splitlines():
        if fence is None:
            m = _FENCE_OPEN_RE.match(line)
            if m:
                marker = m.group(1)
                fence = (marker[0], len(marker))
                if current is not None:
                    buf.append(line)
                continue
        else:
            m = _FENCE_CLOSE_RE.match(line)
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= fence[1]:
                fence = None
            if current is not None:
                buf.append(line)
            continue
        if _H2_RE.match(line):
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            current = heading_key(line)
            buf = []
        elif current is not None:
            buf.append(line)
    if current is not None:
        sections[current] = "\n".join(buf).strip()
    return sections


def strip_fences(text: str) -> str:
    """Return text with fenced code blocks removed, for keyword checks that must
    not count a keyword appearing only inside a pasted example (the NO_SHALL
    check: a `shall` inside a fenced template example does not make the real
    acceptance criteria verifiable)."""
    out = []
    fence = None
    for line in text.splitlines():
        if fence is None:
            m = _FENCE_OPEN_RE.match(line)
            if m:
                fence = (m.group(1)[0], len(m.group(1)))
                continue
            out.append(line)
        else:
            m = _FENCE_CLOSE_RE.match(line)
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= fence[1]:
                fence = None
    return "\n".join(out)


def _has_content(body: str) -> bool:
    """True if a section body has real content. A body that is only HTML
    comments (`<!-- TODO -->`) is structurally empty. Placeholder PROSE like
    "[pending]" is NOT detected here — judging whether content is good is the
    model's job; this gate only checks the section isn't structurally hollow."""
    stripped = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
    return bool(stripped.strip())


def lint(profile: str, path: Path) -> list:
    """Return a list of problem lines (empty = clean)."""
    required = PROFILES[profile]
    try:
        text = path.read_text()
    except (OSError, UnicodeDecodeError):
        return [f"NO_FILE profile={profile} file={path}"]

    sections = split_sections(text)
    problems = []
    for heading in required:
        key = heading_key(heading)
        if key not in sections:
            problems.append(f'MISSING profile={profile} section="{heading}"')
        elif not _has_content(sections[key]):
            problems.append(f'EMPTY profile={profile} section="{heading}"')

    if profile == "contract":
        # Acceptance criteria are only mechanically verifiable if they use the
        # EARS `shall` keyword (the validator greps for it). Heading present but
        # no `shall` underneath = nothing the validator can check.
        ac = sections.get(heading_key("## Acceptance criteria"), "")
        if ac and not re.search(r"\bshall\b", strip_fences(ac), re.IGNORECASE):
            problems.append("NO_SHALL profile=contract")

    return problems


def main() -> None:
    ap = argparse.ArgumentParser(description="Mandatory-section check for build artifacts")
    ap.add_argument("--profile", required=True, choices=sorted(PROFILES), help="artifact type")
    ap.add_argument("path", help="path to the artifact file")
    args = ap.parse_args()

    problems = lint(args.profile, Path(args.path))
    if not problems:
        print(f"OK profile={args.profile} file={args.path}")
        return
    for line in problems:
        print(line)
    sys.exit(1)


if __name__ == "__main__":
    main()
