#!/usr/bin/env python3
"""
palette-pick.py — deterministic palette selection + token-block emission for
/frame and /build V0 styling.

Mood-matching stays in the skill (model judgment): the model reads spec.md,
extracts mood signals, and matches against the rotation set's "mood" column.
This script handles the mechanical half only:
  - the ambiguous-case hash (sum(ord) % 6), and
  - emitting the verbatim DESIGN.md token recipe for the chosen palette.

  palette-pick.py <slug>                 hash the slug -> pick palette -> emit tokens
  palette-pick.py <slug> --palette NAME  emit tokens for an explicitly matched palette
  palette-pick.py --list                 list palette names + mood signals

Rotation-set order is load-bearing (the hash indexes into it) — do not reorder.
"""
from __future__ import annotations

import argparse
import sys

PALETTES = [
    {"name": "Warm Paper / Coral", "bg": "#faf9f5", "bg_alt": "#e8e6dc", "text": "#141413",
     "text_secondary": "#b0aea5", "border": "#d6d4ca", "accent": "#d97757",
     "mood": "Conversational, reading-room, friendly. Trainer/coach/onboarding."},
    {"name": "Linen / Sage", "bg": "#f5f3ed", "bg_alt": "#e0ddd1", "text": "#1c1c1c",
     "text_secondary": "#8a877c", "border": "#cdc9bc", "accent": "#5b8474",
     "mood": "Calm, document-y, utility. Notes, writing tools, planners."},
    {"name": "Ivory / Indigo", "bg": "#f8f6ef", "bg_alt": "#e9e5d8", "text": "#161618",
     "text_secondary": "#8e8a82", "border": "#d2cdbf", "accent": "#5c6e95",
     "mood": "Thoughtful, library, quietly serious. Research, knowledge tools."},
    {"name": "Bone / Terracotta", "bg": "#f4ede1", "bg_alt": "#e3d8c6", "text": "#1a1614",
     "text_secondary": "#8a7d6e", "border": "#cfc1ad", "accent": "#c1614a",
     "mood": "Handmade, earthy-confident. Craft tools, makers, artisanal."},
    {"name": "Stone / Ochre", "bg": "#efece6", "bg_alt": "#d9d4c8", "text": "#14140e",
     "text_secondary": "#807c70", "border": "#c9c2b0", "accent": "#c79a44",
     "mood": "Documentary, archival, considered. Reference, finance, records."},
    {"name": "Cream / Plum", "bg": "#faf6ef", "bg_alt": "#ebe3d3", "text": "#1a1518",
     "text_secondary": "#8c8076", "border": "#d2c8b6", "accent": "#7c5876",
     "mood": "Soft, refined, slightly unexpected. Creative tools, journals."},
]


def find_by_name(name: str):
    needle = name.strip().lower()
    for p in PALETTES:
        if p["name"].lower() == needle:
            return p
    for p in PALETTES:  # loose match on a word, e.g. "coral", "sage"
        if needle and needle in p["name"].lower():
            return p
    return None


def emit(p: dict, selected_by: str) -> None:
    print(f"# Palette: {p['name']}  (selected by: {selected_by})")
    print("# Apply verbatim in DESIGN.md. Single accent, used sparingly.")
    print()
    print(":root {")
    print(f"  --color-bg: {p['bg']};")
    print(f"  --color-bg-subtle: {p['bg_alt']};")
    print(f"  --color-text: {p['text']};")
    print(f"  --color-text-secondary: {p['text_secondary']};")
    print(f"  --color-border: {p['border']};")
    print(f"  --color-brand: {p['accent']};")
    print("  --font-serif: 'Lora', Georgia, serif;          /* body text */")
    print("  --font-sans: 'Inter', system-ui, sans-serif;    /* UI labels */")
    print("  --font-heading: 'Poppins', sans-serif;          /* h1-h4 */")
    print("  --radius: 1rem;                                 /* 0.5-1.5rem scale */")
    print("  --shadow: 0 0.25rem 1.25rem rgba(0,0,0,0.035);  /* whisper, not slap */")
    print("}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Deterministic palette pick + token block")
    ap.add_argument("slug", nargs="?", help="project slug (hashed when no --palette)")
    ap.add_argument("--palette", help="explicit palette name (model already matched mood)")
    ap.add_argument("--list", action="store_true", help="list palettes + mood signals")
    args = ap.parse_args()

    if args.list:
        for i, p in enumerate(PALETTES):
            print(f"{i}  {p['name']:20}  {p['mood']}")
        return

    if args.palette:
        p = find_by_name(args.palette)
        if not p:
            print(f"palette-pick: unknown palette {args.palette!r}. Use --list.", file=sys.stderr)
            sys.exit(1)
        emit(p, f"mood match ({args.palette})")
        return

    if not args.slug:
        ap.error("provide a <slug>, or --palette NAME, or --list")
    idx = sum(ord(c) for c in args.slug) % 6
    emit(PALETTES[idx], f"hash of slug '{args.slug}' -> index {idx}")


if __name__ == "__main__":
    main()
