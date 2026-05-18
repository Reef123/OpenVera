---
name: finds-real-gotchas
created: 2026-04-18
rubric: research
---

## Input

`/scout next.js app router vs pages router for a small SaaS in 2026`

## Expected Qualities

- Should pull at least one Reddit thread and at least one YouTube video — not only blog posts.
- Should surface concrete gotchas (e.g., specific server-component pitfall, hydration mismatch, third-party library compatibility) rather than generic "App Router is newer."
- Should give a recommendation conditional on the user's situation, not a flat "App Router won."
- Should NOT recommend rewriting an existing Pages-Router app without a concrete reason.
- Should finish in roughly 2-3 minutes and stay under $0.10 — anything over that means it drifted into `/research` territory.
- Should cite source URLs inline, not as a dump at the end.

## Why this test exists

Caught a real failure mode where `/scout` returned a generic "App Router is the future" answer with three Vercel blog posts and no actual community input. The whole point of `/scout` is the Reddit + YouTube layer; if the output reads like a marketing page, the skill failed.
