#!/usr/bin/env python3
"""
build-state.py — Manage build-state.md transitions deterministically.

Usage (set — the default form):
    python3 vera-system/scripts/build-state.py <slug> <stage> [--substage STEP] [--mode MODE] [--artifact KEY=PATH] [--decision TEXT]

Usage (resume helpers — first arg is a command word):
    python3 vera-system/scripts/build-state.py status            # summary table of every build-state.md
    python3 vera-system/scripts/build-state.py continue [<slug>] # resume context for one project

Examples:
    python3 vera-system/scripts/build-state.py my-app "V0 Stage 0" --mode new
    python3 vera-system/scripts/build-state.py my-app "V0 Stage 2" --substage "build component 3"
    python3 vera-system/scripts/build-state.py my-app "V0 Stage 3" --artifact "Build score=3.8/5.0"
    python3 vera-system/scripts/build-state.py my-app "complete"
    python3 vera-system/scripts/build-state.py status
    python3 vera-system/scripts/build-state.py continue my-app

`continue` is the wrong-branch-resume guard: after a compact it deterministically
recovers the active project's mode/stage/substage AND, for mode=full, greps
`git worktree list` for the matching `build-full-<slug>-*` worktree and prints the
exact `EnterWorktree(path: ...)` to re-enter — instead of the model globbing and
grepping by hand (which landed resumes on the wrong branch).

Reads config.json for projects_dir. Creates file if missing. Validates stage transitions.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Resolve paths
SCRIPT_DIR = Path(__file__).resolve().parent
SYSTEM_DIR = SCRIPT_DIR.parent
REPO_ROOT = SYSTEM_DIR.parent

sys.path.insert(0, str(SCRIPT_DIR))
from vera_config import get_path, safe_project_path, validate_slug  # noqa: E402

V0_STAGES = [
    "V0 Stage 0",    # Kickoff + Purpose
    "V0 Stage 1",    # Parallel Sprint
    "V0 Stage 2",    # Build Loop
    "V0 Stage 3",    # Score
    "V0 Stage 4",    # Ship (4a)
    "V0 Stage 4a",   # Ship (explicit alias for the 4a/4b split in v0-stages.md)
    "V0 Stage 4b",   # Handoff codification (writes handoff.md)
    "complete",
]

FULL_STAGES = [
    "Full Stage 0",  # Kickoff
    "Full Stage 1",  # Autonomous Sprint
    "Phase 1",       # PRD
    "Phase 2",       # Tech Design
    "Phase 3",       # Arch Review
    "Phase 4",       # Phase Planning
    "Phase 5",       # Build Phase N
    "Phase 6",       # Code Review N
    "Phase 6.5",     # Simplification
    "Phase 6.7",     # Security Review (OWASP Top 10)
    "Phase 7",       # QA
    "Phase 8",       # Ship
    "complete",
]

ALL_STAGES = set(V0_STAGES + FULL_STAGES)


def state_file_path(slug: str) -> Path:
    return safe_project_path(slug, "build-state.md")


def read_state(path: Path) -> dict:
    """Parse existing build-state.md into a dict."""
    state = {"mode": "", "stage": "", "substage": "", "artifacts": [], "decisions": []}
    if not path.exists():
        return state

    section = None
    # errors="replace": one corrupt/non-UTF-8 state file (OneDrive sync can
    # produce them) must not traceback `status`, which walks every project.
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line_stripped = line.strip()
        if line_stripped.startswith("**Mode:**"):
            state["mode"] = line_stripped.split("**Mode:**")[1].strip()
        elif line_stripped.startswith("**Stage:**"):
            state["stage"] = line_stripped.split("**Stage:**")[1].strip()
        elif line_stripped.startswith("**Sub-stage:**"):
            state["substage"] = line_stripped.split("**Sub-stage:**")[1].strip()
        elif line_stripped == "## Artifacts":
            section = "artifacts"
        elif line_stripped == "## Decision Log":
            section = "decisions"
        elif line_stripped.startswith("## "):
            section = None
        elif section == "artifacts" and line_stripped.startswith("- "):
            state["artifacts"].append(line_stripped[2:])
        elif section == "decisions" and line_stripped.startswith("- "):
            state["decisions"].append(line_stripped[2:])

    return state


def write_state(path: Path, state: dict, slug: str):
    """Write build-state.md from state dict."""
    path.parent.mkdir(parents=True, exist_ok=True)

    artifacts_lines = "\n".join(f"- {a}" for a in state["artifacts"]) if state["artifacts"] else "- (none yet)"
    decisions_lines = "\n".join(f"- {d}" for d in state["decisions"]) if state["decisions"] else ""

    content = f"""# Build State: {slug}

**Mode:** {state['mode']}
**Stage:** {state['stage']}
**Sub-stage:** {state['substage']}
**Last updated:** {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}

## Artifacts
{artifacts_lines}

## Decision Log
{decisions_lines}
"""
    path.write_text(content.strip() + "\n")


def projects_root() -> Path:
    return REPO_ROOT / get_path("projects_dir")


def find_state_files() -> list:
    """Every {projects_dir}/<slug>/build-state.md, newest first by mtime."""
    root = projects_root()
    if not root.is_dir():
        return []
    files = list(root.glob("*/build-state.md"))
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files


def git_lines(args: list) -> list:
    """Run a read-only git command at the repo root. Returns stdout lines, or
    [] on any failure (no git, not a repo, timeout) — resume must never crash
    on a git hiccup."""
    try:
        out = subprocess.run(
            ["git", *args], cwd=str(REPO_ROOT),
            capture_output=True, text=True, timeout=15,
        )
    except (subprocess.SubprocessError, OSError):
        return []
    return [line for line in out.stdout.splitlines() if line.strip()]


def git_ok() -> bool:
    """True if git is usable here. Used to distinguish "no matching worktree"
    from "worktree detection couldn't run" — the latter must not be reported as
    a confident "resume on current branch" for a full build."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--git-dir"], cwd=str(REPO_ROOT),
            capture_output=True, text=True, timeout=15,
        )
    except (subprocess.SubprocessError, OSError):
        return False
    return out.returncode == 0


def current_branch() -> str:
    """Active branch name, or 'DETACHED' if HEAD is detached, '?' if unknown."""
    lines = git_lines(["symbolic-ref", "--short", "-q", "HEAD"])
    if lines:
        return lines[0].strip()
    # symbolic-ref fails (rc 1) on detached HEAD; distinguish from no-git.
    return "DETACHED" if git_lines(["rev-parse", "HEAD"]) else "?"


def worktree_for(slug: str) -> str | None:
    """Path of an active `build-full-<slug>-<date>` worktree, or None. Parses
    `git worktree list --porcelain` (stable, machine-readable) so a worktree
    path with spaces can't confuse the grep the prose used to do by hand.

    The branch is `build-full-<slug>-<YYYYMMDD>`, so the slug must be followed
    by a hyphen and a DIGIT — otherwise slug `demo` would match the worktree of
    `demo-app` (its prefix), re-entering the wrong project."""
    pattern = re.compile(r"^build-full-" + re.escape(slug) + r"-\d")
    current_path = None
    for line in git_lines(["worktree", "list", "--porcelain"]):
        if line.startswith("worktree "):
            current_path = line[len("worktree "):]
        elif line.startswith("branch ") and current_path:
            branch = line[len("branch "):].rsplit("/", 1)[-1]
            if pattern.match(branch):
                return current_path
    return None


def cmd_status() -> None:
    """Summary table of every build-state.md (the old glob-and-eyeball step)."""
    files = find_state_files()
    if not files:
        print("No build-state.md files found.")
        return
    print(f"{'SLUG':<28} {'MODE':<6} {'STAGE':<16} SUBSTAGE")
    for path in files:
        state = read_state(path)
        slug = path.parent.name
        print(f"{slug:<28} {state['mode']:<6} {state['stage']:<16} {state['substage']}")


def cmd_continue(slug: str | None) -> None:
    """Recover resume context for one project (most-recent if slug omitted).
    Prints a RESUME block plus, for mode=full, the exact worktree to re-enter."""
    if slug:
        try:
            validate_slug(slug)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(1)
        path = state_file_path(slug)
        if not path.exists():
            print(f"ERROR: no build-state.md for '{slug}' under {projects_root()}", file=sys.stderr)
            sys.exit(1)
    else:
        files = find_state_files()
        if not files:
            print(f"ERROR: no build-state.md found under {projects_root()}", file=sys.stderr)
            sys.exit(1)
        path = files[0]
        slug = path.parent.name

    state = read_state(path)
    print(f"SLUG={slug}")
    print(f"MODE={state['mode']}")
    print(f"STAGE={state['stage']}")
    print(f"SUBSTAGE={state['substage']}")
    print(f"STATE_FILE={path}")
    for artifact in state["artifacts"]:
        if artifact != "(none yet)":  # the write_state placeholder, not a real artifact
            print(f"ARTIFACT={artifact}")

    # Only an explicit mode=new skips worktree detection. An empty/corrupt mode
    # is treated as full (worktree-checking) — resuming a full build on the
    # wrong branch is the exact failure continue exists to prevent.
    if state["mode"] == "new":
        print("WORKTREE=n/a (mode=new uses no worktree)")
        print(f"ACTION=resume V0 pipeline at '{state['stage']}' on current branch ({current_branch()})")
    else:
        if state["mode"] != "full":
            print(f"WARN=mode is '{state['mode']}' (expected new|full); treating as full and checking for a worktree")
        wt = worktree_for(slug)
        if wt:
            print(f"WORKTREE={wt}")
            print(f"ACTION=EnterWorktree(path: \"{wt}\")  # re-enter, then read MANIFEST.md")
        elif not git_ok():
            print("WORKTREE=unknown")
            print(f"ACTION=worktree detection could not run (git unavailable) — verify the branch before resuming {slug}")
        else:
            print("WORKTREE=none")
            print(f"ACTION=resume on current branch ({current_branch()}); no build-full-{slug}-* worktree found")


def cmd_set():
    parser = argparse.ArgumentParser(description="Manage build-state.md transitions")
    parser.add_argument("slug", help="Project slug (kebab-case)")
    parser.add_argument("stage", help="Target stage (e.g., 'V0 Stage 2', 'Phase 5', 'complete')")
    parser.add_argument("--substage", default="", help="Sub-stage description")
    parser.add_argument("--mode", choices=["new", "full"], help="Build mode (required on first call)")
    parser.add_argument("--artifact", action="append", default=[], help="Add artifact (KEY=PATH)")
    parser.add_argument("--decision", action="append", default=[], help="Add decision log entry")
    args = parser.parse_args()

    try:
        validate_slug(args.slug)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    # Accept short stage names ("Stage 0") when --mode is set; infer the prefix.
    # SKILL.md naturally writes "Stage 0" without remembering which mode it's in;
    # this lets the script meet that ergonomic instead of crashing on it.
    if args.stage not in ALL_STAGES and args.mode:
        prefix = "V0" if args.mode == "new" else "Full"
        candidate = f"{prefix} {args.stage}"
        if candidate in ALL_STAGES:
            args.stage = candidate

    if args.stage not in ALL_STAGES:
        print(f"ERROR: Unknown stage '{args.stage}'", file=sys.stderr)
        print(f"Valid V0 stages: {', '.join(V0_STAGES)}", file=sys.stderr)
        print(f"Valid Full stages: {', '.join(FULL_STAGES)}", file=sys.stderr)
        sys.exit(1)

    path = state_file_path(args.slug)
    state = read_state(path)

    # Set or validate mode
    if args.mode:
        state["mode"] = args.mode
    elif not state["mode"]:
        # Infer from stage name
        if args.stage.startswith("V0"):
            state["mode"] = "new"
        elif args.stage.startswith(("Full", "Phase")):
            state["mode"] = "full"
        else:
            print("ERROR: No mode set. Use --mode on first call.", file=sys.stderr)
            sys.exit(1)

    # Update stage
    old_stage = state["stage"]
    state["stage"] = args.stage
    state["substage"] = args.substage

    # Add artifacts
    for artifact in args.artifact:
        state["artifacts"].append(artifact)

    # Add decisions with timestamp
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    for decision in args.decision:
        state["decisions"].append(f"[{ts}] {decision}")

    write_state(path, state, args.slug)

    # Report
    if old_stage:
        print(f"Transition: {old_stage} → {args.stage}")
    else:
        print(f"Created: {args.stage} (mode={state['mode']})")
    print(f"State file: {path}")


def main():
    # Route the resume commands (`status`, `continue`) before argparse so the
    # legacy `<slug> <stage>` set form keeps working unchanged. A project
    # literally named "status" or "continue" would be shadowed here — an
    # accepted edge (kebab slugs are rarely bare command words).
    argv = sys.argv[1:]
    if argv and argv[0] == "status":
        if len(argv) > 1:
            print("ERROR: status takes no arguments", file=sys.stderr)
            sys.exit(2)
        cmd_status()
    elif argv and argv[0] == "continue":
        if len(argv) > 2:
            print("ERROR: continue takes at most one slug", file=sys.stderr)
            sys.exit(2)
        cmd_continue(argv[1] if len(argv) > 1 else None)
    else:
        cmd_set()


if __name__ == "__main__":
    main()
