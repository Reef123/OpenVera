# Security

## Reporting a vulnerability

If you find a security issue in Vera (a prompt injection vector, a skill that can exfiltrate secrets, a script that takes unvalidated input into a shell), open a [GitHub private vulnerability report](https://github.com/Reef123/OpenVera/security/advisories/new) or DM [@shareefatwork](https://x.com/shareefatwork).

I'll respond within a week. For anything time-sensitive, say so in the report.

## What's in scope

- Code in this repo: scripts under `vera-system/scripts/`, hooks under `.claude/hooks/`, the bootstrap script.
- Skill instructions that could be tricked into leaking your secrets or running unsafe commands.
- The settings.json permission model in `.claude/settings.json`.

## Handling your own secrets

- `.secrets` and `.env*` are gitignored. Never commit them.
- Bootstrap writes `.secrets` with `chmod 600`.
- `settings.json` denies reads of `~/.ssh`, `~/.aws`, `*.env`, and known credential paths by default. 

## What Vera does with untrusted input

- `/scout` and `/research` fetch external content through two paths with different guarantees. The `youtube-analyze.py` and `openrouter.py --search` scripts wrap their output in `<!-- UNTRUSTED EXTERNAL CONTENT -->` delimiters programmatically, so injection attempts arrive clearly fenced as data. The `WebFetch`, `WebSearch`, and Firecrawl paths have no programmatic wrapper: the skills instruct the model to treat fetched content as data rather than instructions, but on those paths the boundary is model-enforced, not mechanically guaranteed. Report any injection that gets through so the boundary can be tightened.
- Hooks and scripts pass secrets via environment variables, not shell interpolation.
