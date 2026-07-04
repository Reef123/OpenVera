---
name: wireframe-first
description: "Iterative wireframing method for ONE screen or substantial component. ASCII boxes, beat-by-beat, ratify before code. Prevents the rebuild-loop failure mode (multiple code attempts when the real issue is unresolved design)."
argument-hint: "<screen-or-component-name>"
---

# Wireframe First

Substantial UI = sketch in text, get sign-off, then build.

**Vs `/frame`:** `/frame` does project-level wireframes + DESIGN.md in one shot, called by `/build`. `/wireframe-first` is the interactive method for iterating ONE screen with the user — usually after `/frame` set the system but a specific surface needs more rounds, or after a build attempt failed twice on intent mismatch.

**Trigger:** New screen, multi-beat experience, big component rewrite, structural redesign.

**Skip:** Trivial edit (copy change, color tweak), precise spec already given, "just build it."

---

## Method

### 1. State the user goal in one sentence

What does the user walk out with? The artifact + the felt experience. Not UI copy.

> Good: *"User walks out with one prompt that works for a task they have, plus the experience of seeing their weak prompt close the gap."*
> Bad: *"A guided learning experience that helps users improve prompting."*

If the sentence won't form, stop and ask.

### 2. Surface 2-3 strategic forks BEFORE sketching

Wireframes are downstream of unresolved decisions. Surface forks as direct picks. State your recommendation + one-line reasoning, ask where the user pushes back. Resolve each before drawing a single box.

**Anti-pattern:** sketching a wireframe that secretly bakes an architectural decision. User thinks they're approving a layout; they're approving a schema.

### 3. Sketch in text, not pixels

ASCII boxes only. No Figma, no screenshots. Constraints force clarity.

Per beat — three sentences max:
- **Layout** — what's on the screen, top to bottom
- **Active element** — what the user clicks, types, selects
- **Interaction** — what happens next

Anything more is essay; cut it.

### 4. Number the beats; show the flow

Beat 1 → Beat 2 → Beat 3. Branches get `Beat 3.5`. Numbering lets feedback target precisely ("change Beat 3.5"). If >5 beats, the experience is probably two glued together — surface that.

### 5. Iterate one piece, show the full set again

When the user pushes back on Beat 2, re-render ALL beats with the edit applied. User shouldn't assemble updates mentally; downstream interactions break silently otherwise.

### 6. Audit your own additions

Between rounds: did you add a subhead, a persistence layer, an extra screen, a scoring rubric the user didn't ask for? Flag it in the next reply: *"Adding [X] — push back if too much."* Never smuggle scope as polish.

Never assume infrastructure exists. Grep before referencing a toolkit, persistence layer, or shared component.

### 7. Close with state + API + estimate

- **State additions** — new fields the component needs, OR "component-local only, no new state"
- **API contract** — endpoint + request/response if a new endpoint is needed; otherwise "no new API"
- **Build estimate** — total hours + 3-5 line breakdown

### 8. Ratify before building

End each round with *"Ready to build, or anything to push on first?"* On push, return to Step 5. On "go" or "build it," write code. Not before.

---

## Default Posture

- **Real components > new components.** Grep existing components before sketching a new one.
- **Copy button > persistence layer** for take-home artifacts. Persistence has cost.
- **Empty input + "Use an example" escape > pre-filled.** Pre-filled steers; empty invites.
- **Coaching/guidance surfaces:** no score, no streak, no gamification unless explicitly asked. Dashboards and analytics UIs are exempt — scores there are the product.

---

## Bail Conditions

Stop wireframing, ask the user when:
- Goal sentence won't form
- A fork has no obvious right answer and the user hasn't weighed in
- Beats exceed 5 and won't compress
- Required infrastructure (toolkit, API, design system) is missing or uncertain
- Terse pushback you can't parse ("nope") — ask for the specific piece

---

## Anti-Patterns

| Pattern | Fix |
|---|---|
| Sketching before forks resolved | Step 2 first |
| Smuggling infrastructure | Grep before referencing |
| "Goal" = UI copy | Goal is the bet, not the headline |
| Showing partial updates | Always show the full set after an edit |
| Polish disguised as scope | Surface every addition explicitly |
| Pixel mockups | Text only |

---

*Author: Shareef Ellis · [@shareefatwork](https://x.com/shareefatwork)*
