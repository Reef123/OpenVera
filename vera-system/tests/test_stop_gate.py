#!/usr/bin/env python3
"""Tests for the Stop-gate hook layer.

stop-doc-sync-gate.py decides whether to hold a turn open until /doc-sync
runs; mark-dirty.py decides whether a write re-arms that gate. Both decisions
are pure functions extracted for exactly this test — a regression here either
traps the user at every turn end (gate too eager) or silently disables the
compounding loop (gate or marker too lax).

Stdlib unittest, runs on macOS system Python 3.9.6:

    python3 -m unittest discover -s vera-system/tests
    python3 tests/test_stop_gate.py
"""
import importlib.util
import sys
import tempfile
import time
import unittest
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parents[2] / ".claude" / "hooks"


def _load(name, filename):
    """Import a hyphenated hook file as a module."""
    spec = importlib.util.spec_from_file_location(name, _HOOKS_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


stop_gate = _load("stop_doc_sync_gate", "stop-doc-sync-gate.py")
mark_dirty = _load("mark_dirty", "mark-dirty.py")


class ShouldBlockTests(unittest.TestCase):
    """Full truth table: block IFF ending AND dirty AND NOT stop_hook_active."""

    def test_blocks_only_when_ending_and_dirty_and_not_active(self):
        self.assertTrue(stop_gate.should_block(True, True, False))

    def test_all_other_combinations_allow(self):
        for ending in (True, False):
            for dirty in (True, False):
                for active in (True, False):
                    if ending and dirty and not active:
                        continue
                    self.assertFalse(
                        stop_gate.should_block(ending, dirty, active),
                        f"should_block({ending}, {dirty}, {active}) must be False",
                    )

    def test_loop_guard_wins_over_everything(self):
        # stop_hook_active=True means we already blocked this cycle —
        # blocking again would fight Claude Code's loop prevention.
        self.assertFalse(stop_gate.should_block(True, True, True))


class RepoRootValidationTests(unittest.TestCase):
    def test_real_repo_root_validates(self):
        real_root = _HOOKS_DIR.parents[1]
        self.assertEqual(stop_gate._validate_repo_root(real_root), real_root.resolve())

    def test_foreign_dir_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(stop_gate._validate_repo_root(Path(tmp)))

    def test_mark_dirty_uses_same_defense(self):
        real_root = _HOOKS_DIR.parents[1]
        self.assertEqual(mark_dirty._validate_repo_root(real_root), real_root.resolve())
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(mark_dirty._validate_repo_root(Path(tmp)))


class LockFreshnessTests(unittest.TestCase):
    """A fresh lockfile suppresses mark-dirty; a stale one must NOT — a
    crashed skill would otherwise disable the gates forever."""

    def test_fresh_lock_is_honored(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock = Path(tmp) / ".doc-sync-running"
            lock.touch()
            self.assertTrue(mark_dirty.lock_is_fresh(lock, time.time()))

    def test_stale_lock_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock = Path(tmp) / ".doc-sync-running"
            lock.touch()
            future = time.time() + mark_dirty.LOCK_TTL_SECONDS + 1
            self.assertFalse(mark_dirty.lock_is_fresh(lock, future))

    def test_missing_lock_is_not_fresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock = Path(tmp) / ".doc-sync-running"
            self.assertFalse(mark_dirty.lock_is_fresh(lock, time.time()))

    def test_boundary_exactly_at_ttl_is_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock = Path(tmp) / ".curate-running"
            lock.touch()
            at_ttl = lock.stat().st_mtime + mark_dirty.LOCK_TTL_SECONDS
            self.assertFalse(mark_dirty.lock_is_fresh(lock, at_ttl))


if __name__ == "__main__":
    sys.exit(unittest.main())
