#!/usr/bin/env python3
"""
frontmatter.py — deterministic project CLAUDE.md frontmatter writer.

The MODEL supplies every judgment value (name, stack, run, score, summary) as
an argument. This script handles the mechanical assembly only: slug, dates,
YAML block, directory creation, and in-place field updates. It NEVER touches
idea.md or any body content beyond the project CLAUDE.md it owns.

Subcommands:

  slug "<free text>"
      Print a canonical kebab-case slug derived from text. No side effects.

  create --slug S --name N [--status building] [--origin "/build new"]
         [--stack "..."] [--run "..."] [--score null] [--summary "one line"]
      mkdir {projects_dir}/<slug>/ and write CLAUDE.md with the standard
      frontmatter block + lifecycle comment + H1 + summary. Refuses if
      CLAUDE.md already exists (never clobbers). Prints the path written.

  set <file> key=value [key=value ...]
      Update fields inside the file's --- frontmatter block, in place.
      Preserves inline comments, the body, and any unlisted fields. The
      special value "today" expands to the current date (YYYY-MM-DD), e.g.
      `updated=today`. A key not already present is appended inside the block.

Usage from skills:
  python3 vera-system/scripts/frontmatter.py slug "Track my reading list"
  python3 vera-system/scripts/frontmatter.py create --slug reading-tracker \
      --name "Reading Tracker" --status building --origin "/build new" \
      --stack "Next.js + Tailwind" --run "npm run dev"
  python3 vera-system/scripts/frontmatter.py set \
      vera-projects/projects/reading-tracker/CLAUDE.md status=shipped score=8.5 updated=today
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

from vera_config import slugify, validate_slug, safe_project_path

FIELD_ORDER = ["name", "slug", "status", "created", "updated", "stack", "run", "score", "origin"]
LIFECYCLE_COMMENT = "# lifecycle: exploring -> building -> shipped -> live  (parked/declined = terminal)"


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def cmd_slug(args) -> None:
    print(slugify(args.text))


def cmd_create(args) -> None:
    slug = validate_slug(args.slug)
    proj_dir = safe_project_path(slug)
    proj_dir.mkdir(parents=True, exist_ok=True)
    claude_md = proj_dir / "CLAUDE.md"
    if claude_md.exists():
        sys.exit(f"frontmatter: {claude_md} already exists - refusing to overwrite")

    today = _today()
    values = {
        "name": args.name,
        "slug": slug,
        "status": args.status,
        "created": today,
        "updated": today,
        "stack": args.stack if args.stack is not None else "null",
        "run": args.run if args.run is not None else "null",
        "score": args.score if args.score is not None else "null",
        "origin": args.origin,
    }

    lines = ["---"]
    for key in FIELD_ORDER:
        if key == "status":
            lines.append(f"status: {values[key]}   {LIFECYCLE_COMMENT}")
        else:
            lines.append(f"{key}: {values[key]}")
    lines.append("---")
    lines.append(f"# {args.name}")
    lines.append(args.summary if args.summary else "<one line - what this does>")
    lines.append("")
    claude_md.write_text("\n".join(lines) + "\n")
    print(str(claude_md))


_FENCE_RE = re.compile(r"^(---\s*\n)(.*?\n)(---\s*\n?)(.*)$", re.DOTALL)
_FIELD_RE = re.compile(r"^(\s*)([A-Za-z0-9_-]+)(\s*:\s*)([^#]*?)(\s*#.*)?$")


def cmd_set(args) -> None:
    path = Path(args.file)
    if not path.exists():
        sys.exit(f"frontmatter: {path} does not exist")

    text = path.read_text()
    m = _FENCE_RE.match(text)
    if not m:
        sys.exit(f"frontmatter: no --- frontmatter block in {path}")
    open_fence, body, close_fence, rest = m.group(1), m.group(2), m.group(3), m.group(4)
    fm_lines = body.splitlines()

    updates = {}
    for pair in args.pairs:
        if "=" not in pair:
            sys.exit(f"frontmatter: expected key=value, got {pair!r}")
        key, _, value = pair.partition("=")
        key, value = key.strip(), value.strip()
        if value == "today":
            value = _today()
        updates[key] = value

    seen = set()
    for i, line in enumerate(fm_lines):
        fm = _FIELD_RE.match(line)
        if not fm:
            continue
        key = fm.group(2)
        if key in updates:
            indent, colon, comment = fm.group(1), fm.group(3), (fm.group(5) or "")
            fm_lines[i] = f"{indent}{key}{colon}{updates[key]}{comment}"
            seen.add(key)

    for key, value in updates.items():
        if key not in seen:
            fm_lines.append(f"{key}: {value}")

    path.write_text(open_fence + "\n".join(fm_lines) + "\n" + close_fence + rest)
    print(f"frontmatter: set {', '.join(updates)} in {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Project CLAUDE.md frontmatter writer")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_slug = sub.add_parser("slug", help="derive a kebab-case slug from text")
    p_slug.add_argument("text")
    p_slug.set_defaults(func=cmd_slug)

    p_create = sub.add_parser("create", help="create project dir + CLAUDE.md")
    p_create.add_argument("--slug", required=True)
    p_create.add_argument("--name", required=True)
    p_create.add_argument("--status", default="building")
    p_create.add_argument("--origin", default="/build new")
    p_create.add_argument("--stack", default=None)
    p_create.add_argument("--run", default=None)
    p_create.add_argument("--score", default=None)
    p_create.add_argument("--summary", default=None)
    p_create.set_defaults(func=cmd_create)

    p_set = sub.add_parser("set", help="update frontmatter fields in place")
    p_set.add_argument("file")
    p_set.add_argument("pairs", nargs="+", metavar="key=value")
    p_set.set_defaults(func=cmd_set)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
