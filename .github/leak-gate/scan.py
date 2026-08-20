#!/usr/bin/env python3
"""Leak gate — CI net for public pushes. POST-PUBLICATION ALARM, not prevention:
by the time this runs the push has landed; the local pre-push hook is the wall.
This net exists for pushes that bypassed the hook (new clone, web UI, --no-verify).

v2 (2026-08-07, post Codex adversarial pass): per-commit scanning, 3-field term
parse (name-class was dead in v1), identity + filename checks, binary-addition
flags, REDACTED output (a public log must never republish the matched content),
strict subprocess handling (a git error is a failed scan, not a clean one),
canary-in-secret assertion. Deliberate evasion is out of scope (accident net).
"""
import fnmatch, os, re, subprocess, sys

EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
MAX_FALLBACK_COMMITS = 20  # zero/invalid 'before' → scan this many recent commits
# Key prefixes assembled by concatenation so this file never contains a string
# that trips prefix detectors (including its own).
KEY_PREFIXES = ["sk-" + "or-v1-", "sk-" + "ant-", "dop_" + "v1.", "ghp" + "_",
                "github_" + "pat_", "xox" + "b-", "xox" + "p-", "xox" + "a-"]
GENERIC = [
    ("aws-key", re.compile(r"AKIA" + r"[0-9A-Z]{16}")),
    ("private-key-block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY")),
    ("email", re.compile(r"[a-zA-Z0-9._%+-]+@([a-zA-Z0-9.-]+\.[a-z]{2,})")),
    ("phone", re.compile(r"\b\d{3}[-. ]\d{3}[-. ]\d{4}\b")),
]
EMAIL_ALLOW_DOMAINS = {"users.noreply.github.com", "example.com", "example.org"}
NAME_ALLOW_DEFAULT = {"README.md", "THANKS.md", "LICENSE"}


class GitError(Exception):
    pass


def sh(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise GitError(f"git {' '.join(args[:3])}… rc={r.returncode}: {r.stderr.strip()[:200]}")
    return r.stdout


def normalize(text):
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def load_terms():
    terms = []
    for ln in os.environ.get("VERA_DENYLIST_TERMS", "").splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        parts = ln.split("\t")
        if len(parts) == 1:
            parts = ["lit"] + parts
        klass, term = parts[0].lower(), parts[1].lower()
        allow = set(parts[2].split()) if len(parts) > 2 else set()
        terms.append((term, klass, allow or (NAME_ALLOW_DEFAULT if klass == "name" else set())))
    return terms


def match_text(label, text, terms, path=None, allow_names=True):
    """Return REDACTED hit descriptions — never the matched content."""
    hits = []
    for line in text.splitlines():
        low = line.lower()
        for det, rx in GENERIC:
            for m in rx.finditer(line):
                if det == "email" and m.group(1).lower() in EMAIL_ALLOW_DOMAINS:
                    continue
                hits.append(f"{label}: [{det}] (content redacted)")
        for p in KEY_PREFIXES:
            if p.lower() in low:
                hits.append(f"{label}: [key-prefix] (content redacted)")
        norm = normalize(line)
        padded = f" {norm} "
        for term, klass, allow in terms:
            if klass == "name":
                if not allow_names:
                    continue
                base = os.path.basename(path) if path else None
                if base and any(fnmatch.fnmatch(base, g) for g in allow):
                    continue
                if re.search(rf"\b{re.escape(term)}\b", low):
                    hits.append(f"{label}: [name-outside-attribution] (content redacted)")
            else:  # lit — normalized substring catches punctuation-embedded terms
                if f" {term} " in padded or term in low:
                    hits.append(f"{label}: [term] (content redacted)")
    return hits


def commit_hits(c, terms, check_identity_email=True):
    hits = []
    short = c[:8]
    try:
        parent = sh("rev-parse", "--verify", f"{c}^").strip()
    except GitError:
        parent = EMPTY_TREE
    hits += match_text(f"commit {short} (message)", sh("log", "-1", "--format=%B", c), terms)
    ident = sh("log", "-1", "--format=%an <%ae>%n%cn <%ce>", c)
    hits += match_text(f"commit {short} (identity)", ident, terms, allow_names=False)
    # Skipped on the unknown-base fallback: it can reach pre-gate history whose
    # hostname emails are accepted-as-is (audit 2026-08-06); flagging them would
    # train the --no-verify reflex, the gate's real long-term failure mode.
    if check_identity_email:
        for e in sh("log", "-1", "--format=%ae%n%ce", c).split():
            if not e.endswith("@users.noreply.github.com"):
                hits.append(f"commit {short}: [identity-email] non-noreply address in public history")
    for entry in sh("diff", "--numstat", "-z", "--no-renames", parent, c).split("\0"):
        if not entry.strip():
            continue
        cols = entry.split("\t")
        if len(cols) < 3:
            continue
        add, _, path = cols[0], cols[1], cols[2]
        hits += match_text(f"commit {short} (filename)", path, terms, path=path)
        if add == "-":
            if subprocess.run(["git", "cat-file", "-e", f"{c}:{path}"], capture_output=True).returncode == 0:
                hits.append(f"commit {short}: {path}: [binary-added] content unscannable — verify by eye")
            continue
        diff = sh("diff", "--no-renames", parent, c, "--", path)
        added = "\n".join(ln[1:] for ln in diff.splitlines()
                          if ln.startswith("+") and not ln.startswith("+++"))
        hits += match_text(f"commit {short}: {path}", added, terms, path=path)
    return hits


def main():
    terms = load_terms()
    canary = "vera-canary-" + "leak-test"
    if not match_text("selftest", f"note {canary}", [(canary, "lit", set())]):
        print("FAIL-CLOSED: canary self-test failed — matcher untrusted", file=sys.stderr)
        return 1
    if terms and not any(t == canary for t, _, _ in terms):
        print("FAIL-CLOSED: VERA_DENYLIST_TERMS present but missing its canary line — secret malformed", file=sys.stderr)
        return 1
    if not terms:
        print("WARN: VERA_DENYLIST_TERMS absent (fork or missing secret) — generic scan only")

    before, after = sys.argv[1], sys.argv[2]
    try:
        fallback = before == "0" * 40 or subprocess.run(
            ["git", "cat-file", "-e", before], capture_output=True).returncode != 0
        if fallback:
            commits = sh("rev-list", f"--max-count={MAX_FALLBACK_COMMITS}", after).split()
            print(f"NOTE: base unknown — scanning last {len(commits)} commits (approximation; the local hook is the real wall)")
        else:
            commits = sh("rev-list", f"{before}..{after}").split()
        violations = []
        for c in commits:
            violations += commit_hits(c, terms, check_identity_email=not fallback)
    except GitError as e:
        print(f"FAIL-CLOSED: scan incomplete — {e}", file=sys.stderr)
        return 1
    if violations:
        print("LEAK GATE FAILED — matches in pushed commits (content redacted; reproduce locally with the pre-push hook):")
        for v in sorted(set(violations))[:30]:
            print("  " + v)
        return 1
    print(f"leak gate: clean ({len(commits)} commits scanned)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
