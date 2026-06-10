#!/usr/bin/env python3
"""
vera_config.py — Shared config loader for Vera scripts and hooks.

Reads vera-system/config.json and exposes paths and LLM defaults.
Falls back to sane defaults if the file is missing or malformed —
never crashes the caller.

Usage:
    from vera_config import load_config, get_path, get_llm_model

    cfg = load_config()
    projects_dir = get_path("projects_dir")          # "vera-projects/projects"
    scoring_model = get_llm_model("scoring_model")    # "google/gemini-2.5-pro-preview-03-25"

All paths returned are relative to the repo root unless otherwise noted.
Use `repo_root()` to get the absolute repo root path.
"""
import json
import re
from pathlib import Path

_SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


def validate_slug(slug: str) -> str:
    """Reject slugs that could traverse out of projects_dir or contain
    path separators. Slugs are user-supplied (CLI args, /start-vague input).
    Without this, a tainted slug like "../../etc" would let downstream
    write_text() / mkdir() calls escape the projects directory.

    Pattern: lowercase alphanumeric + hyphens, must start with alphanumeric,
    max 64 chars. Matches kebab-case norm used across /start-vague scaffolding.

    Returns the slug unchanged if valid; raises ValueError otherwise.
    """
    if not isinstance(slug, str) or not slug:
        raise ValueError("Slug cannot be empty")
    if not _SLUG_PATTERN.match(slug):
        raise ValueError(
            f"Invalid slug: {slug!r}. Must be kebab-case "
            "(lowercase alphanumeric + hyphens, start with alphanumeric, "
            "max 64 chars)."
        )
    return slug


def slugify(text: str) -> str:
    """Derive a canonical kebab-case slug from free text, matching the rule
    validate_slug enforces (lowercase alphanumeric + hyphens, starts
    alphanumeric, max 64 chars). Deterministic — same input always yields the
    same slug, so generated slugs won't drift from ones already on disk.

    Lowercases, collapses every run of non-alphanumerics to a single hyphen,
    trims leading/trailing hyphens, truncates to 64. Raises ValueError if no
    slug can be derived (empty or all-punctuation input). The returned slug is
    re-validated through validate_slug so callers get one guarantee.
    """
    if not isinstance(text, str):
        raise ValueError("slugify expects a string")
    s = text.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")[:64].strip("-")
    if not s:
        raise ValueError(f"Could not derive a slug from {text!r}")
    return validate_slug(s)


def safe_project_path(slug: str, *parts: str) -> Path:
    """Build a project-dir path from a slug, validating both the slug and
    that the final resolved path stays under projects_dir. Defense in
    depth — even if validate_slug somehow lets a bad value through, the
    resolve() check catches the escape.
    """
    validate_slug(slug)
    projects_dir = (repo_root() / get_path("projects_dir")).resolve()
    candidate = (projects_dir / slug).joinpath(*parts).resolve()
    try:
        candidate.relative_to(projects_dir)
    except ValueError as exc:
        raise ValueError(
            f"Resolved path {candidate} escapes projects_dir {projects_dir}"
        ) from exc
    return candidate

DEFAULTS = {
    "version": 1,
    "paths": {
        "projects_dir": "vera-projects/projects",
        "research_output_dir": "vera-projects/research-output",
        "conversations_dir": "vera-system/conversations",
        "state_file": "vera-system/state.md",
        "roadmap_file": "vera-system/ROADMAP.md",
        "memory_dir": "vera-system/memory",
    },
    "llm": {
        "provider": "openrouter",
        "default_model": "google/gemini-2.5-flash",
        "scoring_model": "google/gemini-2.5-pro-preview-03-25",
        "video_provider": "google-gemini",
        "video_model": "gemini-2.5-flash",
    },
}


def repo_root() -> Path:
    """Resolve the Vera repo root from this file's location.

    This file lives at vera-system/scripts/vera_config.py, so the repo
    root is two parents up.
    """
    return Path(__file__).resolve().parents[2]


# Line caps for the boot-tier files. Claude Code loads roughly the first
# 200 lines / 25KB of memory files automatically — anything past that is
# silently truncated, which is worse than bloat. These were advisory prose
# in .claude/rules/file-size-guard.md; they're enforced here so doctor.py
# and curate-mode.py share one table. Keys are repo-root-relative paths.
SIZE_THRESHOLDS = {
    "vera-system/CLAUDE.md": 150,
    "vera-system/state.md": 100,
    "vera-system/memory/patterns.md": 200,
    "vera-system/memory/MEMORY.md": 200,
    "vera-system/memory/lessons.md": 150,
    "vera-system/ROADMAP.md": 150,
}


def check_file_sizes(root: Path = None) -> list:
    """Check boot-tier files against SIZE_THRESHOLDS.

    Returns a list of (rel_path, line_count, cap) tuples for files OVER
    their cap. Missing files are skipped (fresh installs). Never raises.
    """
    base = root if root is not None else repo_root()
    over = []
    for rel, cap in SIZE_THRESHOLDS.items():
        path = base / rel
        try:
            if not path.is_file():
                continue
            lines = path.read_text().count("\n") + 1
        except (OSError, UnicodeDecodeError):
            continue
        if lines > cap:
            over.append((rel, lines, cap))
    return over


def config_path() -> Path:
    return repo_root() / "vera-system" / "config.json"


def load_config() -> dict:
    """Load config.json with defaults applied for missing keys.

    Never raises — returns DEFAULTS if file missing or malformed.
    Merges loaded values on top of DEFAULTS so partial configs work.
    """
    path = config_path()
    if not path.exists():
        return _deep_copy(DEFAULTS)

    try:
        loaded = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return _deep_copy(DEFAULTS)

    return _merge(DEFAULTS, loaded)


def get_path(key: str, absolute: bool = False) -> str:
    """Get a path from config.paths. Returns DEFAULTS value if key missing.

    Args:
        key: e.g. "projects_dir", "state_file"
        absolute: if True, return absolute path resolved from repo root

    Raises:
        KeyError if key is not a known path key (caller bug, not config issue)
    """
    if key not in DEFAULTS["paths"]:
        raise KeyError(
            f"Unknown path key: {key}. Known keys: {list(DEFAULTS['paths'].keys())}"
        )
    cfg = load_config()
    rel = cfg.get("paths", {}).get(key, DEFAULTS["paths"][key])
    if absolute:
        return str(repo_root() / rel)
    return rel


def get_llm_model(key: str = "default_model") -> str:
    """Get an LLM model name from config.llm. Falls back to DEFAULTS.

    Args:
        key: "default_model" | "scoring_model" | "video_model"
    """
    if key not in DEFAULTS["llm"]:
        raise KeyError(
            f"Unknown llm key: {key}. Known keys: {list(DEFAULTS['llm'].keys())}"
        )
    cfg = load_config()
    return cfg.get("llm", {}).get(key, DEFAULTS["llm"][key])


def get_llm_provider() -> str:
    """Get the LLM provider name (e.g. 'openrouter')."""
    cfg = load_config()
    return cfg.get("llm", {}).get("provider", DEFAULTS["llm"]["provider"])


def _deep_copy(d):
    """Shallow recursive copy of nested dicts/lists. Avoids importing copy."""
    if isinstance(d, dict):
        return {k: _deep_copy(v) for k, v in d.items()}
    if isinstance(d, list):
        return [_deep_copy(v) for v in d]
    return d


def _merge(defaults: dict, loaded: dict) -> dict:
    """Merge loaded values on top of defaults. Loaded wins for leaf values."""
    result = _deep_copy(defaults)
    for key, value in loaded.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = value
    return result


if __name__ == "__main__":
    # CLI usage: python3 vera_config.py [key]
    import sys
    cfg = load_config()
    if len(sys.argv) > 1:
        key = sys.argv[1]
        if key in cfg:
            print(json.dumps(cfg[key], indent=2))
        else:
            print(f"Unknown top-level key: {key}", file=sys.stderr)
            sys.exit(1)
    else:
        print(json.dumps(cfg, indent=2))
