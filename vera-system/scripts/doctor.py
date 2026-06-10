#!/usr/bin/env python3
"""
Vera Doctor — Self-audit the harness state.

Usage:
    python3 vera-system/scripts/doctor.py

Checks: config validity, required directories, skill inventory drift,
secrets format, state.md staleness, bootstrap state.

Exit codes:
    0 = all checks pass
    1 = errors found (something is broken)
    2 = warnings only (drift detected, not broken)
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Resolve paths relative to repo root (script is at vera-system/scripts/)
SCRIPT_DIR = Path(__file__).resolve().parent
SYSTEM_DIR = SCRIPT_DIR.parent
REPO_ROOT = SYSTEM_DIR.parent

errors = []
warnings = []
notes = []


def error(msg):
    errors.append(msg)
    print(f"  ERROR: {msg}")


def warn(msg):
    warnings.append(msg)
    print(f"  WARN:  {msg}")


def note(msg):
    notes.append(msg)
    print(f"  ok:    {msg}")


# --- Check 1: Config validity ---
print("\n[Config]")
config_path = SYSTEM_DIR / "config.json"
if not config_path.exists():
    error("config.json missing — run bootstrap.sh or create manually")
else:
    try:
        config = json.loads(config_path.read_text())
        note("config.json is valid JSON")

        # Check required keys
        for key in ["paths", "llm"]:
            if key not in config:
                error(f"config.json missing top-level key: {key}")

        # Check paths exist
        if "paths" in config:
            for name, rel_path in config["paths"].items():
                full_path = REPO_ROOT / rel_path
                if name.endswith("_dir"):
                    if not full_path.exists():
                        warn(f"config path '{name}' points to missing dir: {rel_path}")
                    else:
                        note(f"paths.{name} exists")
                elif name.endswith("_file"):
                    if not full_path.exists():
                        warn(f"config path '{name}' points to missing file: {rel_path}")
                    else:
                        note(f"paths.{name} exists")

        # Check LLM config
        if "llm" in config:
            for key in ["default_model", "scoring_model"]:
                if key not in config["llm"]:
                    warn(f"config.json llm.{key} not set")
                else:
                    note(f"llm.{key} = {config['llm'][key]}")

    except json.JSONDecodeError as e:
        error(f"config.json is invalid JSON: {e}")


# --- Check 2: Required directories ---
print("\n[Directories]")
required_dirs = [
    ("vera-system/memory", "Memory"),
    ("vera-system/who-i-am", "Identity"),
    ("vera-system/relationships", "Relationships"),
    ("vera-system/conversations", "Conversations"),
    (".claude/skills", "Skills"),
    (".claude/hooks", "Hooks"),
    ("vera-system/scripts", "Scripts"),
    ("vera-projects", "Projects output"),
]
for rel_path, label in required_dirs:
    full = REPO_ROOT / rel_path
    if full.exists():
        note(f"{label} ({rel_path})")
    else:
        error(f"{label} directory missing: {rel_path}")


# --- Check 3: Skill inventory drift ---
print("\n[Skill Inventory]")
skills_dir = REPO_ROOT / ".claude" / "skills"
commands_dir = REPO_ROOT / ".claude" / "commands"
actual_skills = set()
if skills_dir.exists():
    for d in skills_dir.iterdir():
        if d.is_dir() and (d / "SKILL.md").exists():
            actual_skills.add(d.name)

# Slash commands like `/advisor` live in .claude/commands/<name>.md, not in
# .claude/skills/. Both register as invocable, so both count as "registered".
actual_commands = set()
if commands_dir.exists():
    for f in commands_dir.iterdir():
        if f.is_file() and f.suffix == ".md":
            actual_commands.add(f.stem)

registered = actual_skills | actual_commands

# Parse skill tables from CLAUDE.md and .claude/skills/README.md
def extract_skill_commands(filepath):
    """Extract /command names from markdown tables.

    Only counts backtick-wrapped slash commands (e.g., `/doc-sync`). A single
    cell may hold multiple (`/doc-sync`, `/commit`) — handle that. Ignores
    path references like `.claude/skills/<name>/SKILL.md`, which contain
    slashes but aren't standalone commands. Also ignores names appearing only
    inside "renamed from `/X`" parenthetical notes — those are historical.
    """
    import re
    commands = set()
    if not filepath.exists():
        return commands
    # Matches `/name` and `/name <args>` — backticked, starting with slash,
    # alphanumeric name, optionally followed by space + arg-hint inside the
    # same backticks (e.g., `/scout <question>` or `/code-review <path>`).
    backtick_cmd = re.compile(r"`/([A-Za-z][A-Za-z0-9_-]*)(?:\s[^`]*)?`")
    rename_note = re.compile(r"renamed from\s+`/([A-Za-z][A-Za-z0-9_-]*)`", re.IGNORECASE)
    for line in filepath.read_text().splitlines():
        line = line.strip()
        if line.startswith("|") and "/" in line:
            renamed_aliases = {m.group(1) for m in rename_note.finditer(line)}
            for match in backtick_cmd.finditer(line):
                cmd = match.group(1)
                if cmd and cmd not in ("", "-") and cmd not in renamed_aliases:
                    commands.add(cmd)
    return commands

claude_md_skills = extract_skill_commands(SYSTEM_DIR / "CLAUDE.md")
readme_skills = extract_skill_commands(REPO_ROOT / ".claude" / "skills" / "README.md")

# Compare
for skill in sorted(actual_skills):
    note(f"Skill '{skill}' has SKILL.md")
for cmd in sorted(actual_commands):
    note(f"Command '/{cmd}' has commands/{cmd}.md")

documented = claude_md_skills | readme_skills
# Commands referenced as illustrative examples, not real skill directories.
EXAMPLE_COMMANDS = {"commit", "slash-command"}


def _is_internal_skill(skill_name):
    """Skills with `internal: true` in SKILL.md frontmatter have no slash
    command (read inline by other skills, e.g., /tdd by /build full Phase 5).
    These intentionally don't appear in the skills table."""
    skill_md = skills_dir / skill_name / "SKILL.md"
    if not skill_md.exists():
        return False
    in_frontmatter = False
    for line in skill_md.read_text().splitlines()[:30]:
        if line.strip() == "---":
            if in_frontmatter:
                return False  # end of frontmatter, not found
            in_frontmatter = True
            continue
        if in_frontmatter and line.strip() == "internal: true":
            return True
    return False


for skill in sorted(actual_skills - documented):
    if _is_internal_skill(skill):
        note(f"Skill '{skill}' is internal-only (no slash command)")
    else:
        warn(f"Skill '{skill}' exists on disk but not in any skill table")
for cmd in sorted(documented - registered - EXAMPLE_COMMANDS):
    warn(f"Skill table references '/{cmd}' but no .claude/skills/{cmd}/ or .claude/commands/{cmd}.md exists")


# --- Check 4: Secrets ---
print("\n[Secrets]")
secrets_file = SYSTEM_DIR / ".secrets"
template_file = SYSTEM_DIR / ".secrets.template"

if not template_file.exists():
    warn(".secrets.template missing — new users won't know what keys to set")
else:
    note(".secrets.template exists")

if secrets_file.exists():
    # Check permissions
    mode = oct(secrets_file.stat().st_mode)[-3:]
    if mode == "600":
        note(f".secrets permissions: {mode}")
    else:
        warn(f".secrets permissions are {mode} — should be 600 (run: chmod 600 vera-system/.secrets)")

    # Check for populated keys
    content = secrets_file.read_text()
    has_openrouter = any(
        line.startswith("OPENROUTER_API_KEY=") and len(line.split("=", 1)[1].strip()) > 0
        for line in content.splitlines()
    )
    has_google = any(
        line.startswith("GOOGLE_AI_API_KEY=") and len(line.split("=", 1)[1].strip()) > 0
        for line in content.splitlines()
    )
    if has_openrouter:
        note("OpenRouter API key is set")
    else:
        note("OpenRouter API key not set (optional — needed for /research)")
    if has_google:
        note("Google AI API key is set")
    else:
        note("Google AI API key not set (optional — needed for YouTube analysis)")
else:
    note(".secrets not created yet (optional — run bootstrap.sh or copy from .secrets.template)")


# --- Check 5: Bootstrap state ---
print("\n[Bootstrap]")
bootstrapped = REPO_ROOT / ".claude" / "bootstrapped"
if bootstrapped.exists():
    note("Bootstrap marker exists — first-run.md won't load")
else:
    note("Not yet bootstrapped — first-run.md will guide setup on next session")


# --- Check 6: State freshness ---
print("\n[State]")
state_file = SYSTEM_DIR / "state.md"
if state_file.exists():
    content = state_file.read_text()
    # Check if still has placeholder date
    if "YYYY-MM-DD" in content:
        warn("state.md still has placeholder date — not yet personalized")
    else:
        note("state.md has been personalized")

    # Check modification age
    mtime = datetime.fromtimestamp(state_file.stat().st_mtime)
    age_days = (datetime.now() - mtime).days
    if age_days > 14:
        warn(f"state.md last modified {age_days} days ago — may be stale")
    else:
        note(f"state.md modified {age_days} day(s) ago")
else:
    template = SYSTEM_DIR / "state.md.template"
    if bootstrapped.exists():
        error("state.md missing (harness is bootstrapped — it should exist)")
    elif template.exists():
        note("state.md not created yet (made from state.md.template at bootstrap)")
    else:
        error("state.md missing and no state.md.template to bootstrap from")


# --- Check 7: Curate freshness ---
curate_file = REPO_ROOT / ".claude" / "last-curate-date"
if curate_file.exists():
    try:
        curate_date = datetime.strptime(curate_file.read_text().strip(), "%Y-%m-%d")
        age_days = (datetime.now() - curate_date).days
        if age_days > 7:
            warn(f"Last /curate was {age_days} days ago — due for memory consolidation")
        else:
            note(f"Last /curate: {age_days} day(s) ago")
    except ValueError:
        warn(f"{curate_file.name} has invalid format — expected YYYY-MM-DD")
else:
    note("No curate history yet (normal for new harness)")


# --- Check 8: Doc-sync freshness ---
# Stamped by /doc-sync's final step. Stale = context drift across sessions.
last_sync_file = REPO_ROOT / ".claude" / "last-doc-sync"
if last_sync_file.exists():
    try:
        raw = last_sync_file.read_text().strip()
        # Tolerate trailing 'Z' or fractional seconds
        ts = raw.rstrip("Z").split(".")[0]
        last_sync = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")
        age_days = (datetime.utcnow() - last_sync).days
        if age_days > 7:
            warn(f"Last /doc-sync was {age_days} days ago — docs may be drifting from session state")
        else:
            note(f"Last /doc-sync: {age_days} day(s) ago")
    except ValueError:
        warn(f"{last_sync_file.name} has invalid format — expected ISO timestamp YYYY-MM-DDTHH:MM:SS")
else:
    note("No doc-sync history yet (run /doc-sync at session end)")


# --- Check 9: Script inventory (security) ---
# Skills pre-approve Bash(python3 vera-system/scripts/*) via allowed-tools.
# Any unexpected script in this directory runs WITHOUT user approval.
print("\n[Script Inventory]")
KNOWN_SCRIPTS = {
    "build-state.py",
    "curate-mode.py",
    "doc-sync-cascade.py",
    "doc-sync-gap.py",
    "doc-sync-todos.py",
    "doctor.py",
    "frontmatter.py",
    "manifest-update.py",
    "openrouter.py",
    "palette-pick.py",
    "panel-score.py",
    "project-index.py",
    "stamp.py",
    "telemetry.py",
    "vera_config.py",
    "youtube-analyze.py",
}

scripts_dir = SYSTEM_DIR / "scripts"
if scripts_dir.exists():
    # Only check executables — docs (README.md, etc.) live alongside but aren't auto-approved by Bash(scripts/*).
    actual_scripts = {
        f.name for f in scripts_dir.iterdir()
        if f.is_file() and not f.name.startswith(".") and f.suffix in {".py", ".sh"}
    }
    unexpected = actual_scripts - KNOWN_SCRIPTS
    missing = KNOWN_SCRIPTS - actual_scripts

    if unexpected:
        for s in sorted(unexpected):
            error(f"UNEXPECTED script: {s} — skills auto-approve scripts/*. Review or remove this file.")
    else:
        note(f"All {len(actual_scripts)} scripts are known")

    if missing:
        for s in sorted(missing):
            warn(f"Expected script missing: {s}")
else:
    error("scripts/ directory missing")

# Bootstrap lives at the repo root, not under scripts/. Check separately.
bootstrap_sh = REPO_ROOT / "bootstrap.sh"
if not bootstrap_sh.exists():
    warn("bootstrap.sh missing at repo root")


# --- Check 10: Runtime readiness ---
print("\n[Runtime]")

# Python version — scripts target 3.8+; hooks carry future-imports for 3.9.
if sys.version_info < (3, 8):
    warn(f"Python {sys.version_info.major}.{sys.version_info.minor} — scripts need 3.8+; expect failures")
else:
    note(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

# vera_config importable — most scripts and the hooks' config reads depend on
# it. An import failure here means the harness is broken everywhere at once.
sys.path.insert(0, str(SCRIPT_DIR))
try:
    import vera_config  # noqa: F401
    note("vera_config imports")
except Exception as exc:
    error(f"vera_config failed to import: {exc} — most scripts will fail. Restore vera-system/scripts/vera_config.py.")

# runs/ writable — telemetry soft-fails when it isn't, so builds keep working,
# but the run history silently stops accumulating. Surface it here.
runs_dir = SYSTEM_DIR / "runs"
try:
    runs_dir.mkdir(parents=True, exist_ok=True)
    probe = runs_dir / ".doctor-write-probe"
    probe.touch()
    probe.unlink()
    note("runs/ writable")
except OSError as exc:
    warn(f"runs/ not writable ({exc}) — telemetry rows will be dropped")


# --- Check 11: Boot-tier file sizes ---
print("\n[File sizes]")
try:
    from vera_config import check_file_sizes

    oversized = check_file_sizes(REPO_ROOT)
    if not oversized:
        note("All boot-tier files within line caps")
    for rel, lines, cap in oversized:
        if rel.endswith("memory/MEMORY.md"):
            # Claude Code loads roughly the first 200 lines of MEMORY.md —
            # past the cap, older entries silently vanish from every boot.
            error(f"{rel} is {lines} lines (cap {cap}) — entries past the cap are silently truncated at load. Trim or archive now.")
        else:
            warn(f"{rel} is {lines} lines (cap {cap}) — archive completed items or promote rarely-used content.")
except Exception as exc:
    warn(f"File-size check skipped: {exc}")


# --- Summary ---
print("\n" + "=" * 50)
if errors:
    print(f"  {len(errors)} error(s), {len(warnings)} warning(s)")
    print("  Fix errors before using the harness. See RECOVERY.md for fix paths.")
    sys.exit(1)
elif warnings:
    print(f"  All clear. {len(warnings)} warning(s) to review.")
    sys.exit(2)
else:
    print("  All checks passed. Harness is healthy.")
    sys.exit(0)
