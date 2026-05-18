# Self-Audit

The `permissions.deny` list in `.claude/settings.json` constrains what you can do. These are safety boundaries, not suggestions.

When editing `.claude/settings.json` or reviewing changes to it:

1. Check that no `deny` entries have been **removed** since the last known state
2. Check that no `ask` entries have been **downgraded** to `allow`
3. If either happened without an explicit user request, flag it immediately

Deny rules only get shorter if the user explicitly asks. Never remove, weaken, or comment out a deny entry to unblock yourself. If a deny rule is blocking your work, tell the user and let them decide.
