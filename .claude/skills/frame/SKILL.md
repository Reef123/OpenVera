---
name: frame
description: "Design system (DESIGN.md tokens + build contract), architecture diagrams (Mermaid), and wireframes. Invoked by /build or when user mentions design, style, branding, vibe, or aesthetic — even if they don't say 'design'."
argument-hint: <project-slug> [--quick] [--deep] [--arch] [--ui] [--system <brand>] [--from-spec]
---

# /frame — Design System & Wireframe Generator

Generate design artifacts: DESIGN.md (tokens, components, build contract), architecture diagrams, and structured wireframes.

## Configuration (auto-loaded)

```!
cat vera-system/config.json
```

## Depth

| Mode | Time | What |
|------|------|------|
| `--quick` (default) | 3-5 min | Starter system — good enough to build from, refined later |
| `--deep` | 8-12 min | Full system — component inventory, state coverage, Stitch screens if available |

## Arguments

| Flag | Effect |
|------|--------|
| `<slug>` | Project in `{paths.projects_dir}/<slug>/` |
| `--arch` | Architecture diagram only |
| `--ui` | DESIGN.md + wireframes only |
| `--system <brand>` | Fetch reference from awesome-design-md, extract traits (not copy) |
| `--from-spec` | Read `spec.md` to infer design from project context |
| (no flags) | Generate all: arch → DESIGN.md → wireframes (sequential — each feeds the next) |

---

## Step 1: Design Direction (everything upfront)

All design decisions here. No stopping mid-flow.

```
AskUserQuestion(
  questions: [
    {
      question: "Pick the axes that match your product:",
      header: "Design Direction",
      options: [
        // GENERATE 3 curated bundles based on project type. Each is a trait bundle, not a brand name.
        // Example for a developer tool:
        //   {label: "Precision tool", description: "Compact spacing, low radius, restrained color, strong hierarchy, subtle borders — think command center"},
        //   {label: "Calm workspace", description: "Medium spacing, soft neutrals, rounded surfaces, low shadow — think document editor"},
        //   {label: "Bold dashboard", description: "Dense data, vibrant accents, dark-ready, crisp contrast — think mission control"},
        {label: "[Direction A — best fit for project type]", description: "[trait bundle: density, tone, shape, contrast]"},
        {label: "[Direction B — different direction]", description: "[trait bundle]"},
        {label: "[Direction C — unexpected]", description: "[trait bundle]"},
        {label: "I'll describe it", description: "Free text"}
      ]
    },
    {
      question: "Light or dark?",
      header: "Mode",
      options: [
        {label: "Light", description: "White backgrounds, dark text"},
        {label: "Dark", description: "Dark backgrounds, light text"},
        {label: "Both", description: "Light primary, dark supported"},
        {label: "Match the direction", description: "You decide"}
      ]
    },
    {
      question: "Steal traits from an existing design system?",
      header: "Reference",
      options: [
        // GENERATE 2 suggestions matched to project domain
        {label: "[Brand A]", description: "Borrowing: [specific traits — e.g., density model, border philosophy]"},
        {label: "[Brand B]", description: "Borrowing: [different traits]"},
        {label: "No reference", description: "Generate fresh from the direction above"},
        {label: "I have one in mind", description: "I'll name it"}
      ]
    }
  ]
)
```

**Direction generation logic:** Read `{paths.projects_dir}/<slug>/spec.md` or `idea.md` (try both, use whichever exists). If neither exists, infer from the slug name and arguments. Each direction encodes density/tone/shape/contrast (shown in the examples above). Don't use brand names as the direction label — use the feel. Brands go in Reference only.

If `--system <brand>` was passed, omit the Reference question from the AskUserQuestion — use that brand for trait extraction directly.

### Aesthetic Floor (rotating palette set — never default to bootstrap)

**No matter what 3 directions get generated, one MUST be picked from the Vera Considered Palettes set below.** The set rotates hues so V0s don't all look identical — variety across builds is part of the floor. Pick the palette whose mood matches the project; if mood is ambiguous, hash the project slug deterministically into the set so the same idea always gets the same palette.

**All palettes share the philosophy** — warm-paper background (no pure white), slightly off-black text (warm ink), soft warm borders (never gray-200), ONE accent (never bootstrap blue), considered radius scale (0.5-1.5rem), whisper shadows.

#### Vera Considered Palettes (rotation set)

| Palette | bg | bg-alt | text | text-secondary | border | accent | Mood signals |
|---------|----|----|------|----------------|--------|--------|--------------|
| **Warm Paper / Coral** | `#faf9f5` | `#e8e6dc` | `#141413` | `#b0aea5` | `#d6d4ca` | `#d97757` | Conversational, reading-room, friendly. Trainer/coach/onboarding tools. |
| **Linen / Sage** | `#f5f3ed` | `#e0ddd1` | `#1c1c1c` | `#8a877c` | `#cdc9bc` | `#5b8474` | Calm, document-y, utility. Notes apps, writing tools, planners. |
| **Ivory / Indigo** | `#f8f6ef` | `#e9e5d8` | `#161618` | `#8e8a82` | `#d2cdbf` | `#5c6e95` | Thoughtful, library, quietly serious. Research, knowledge tools. |
| **Bone / Terracotta** | `#f4ede1` | `#e3d8c6` | `#1a1614` | `#8a7d6e` | `#cfc1ad` | `#c1614a` | Handmade, earthy-confident. Craft tools, makers, artisanal. |
| **Stone / Ochre** | `#efece6` | `#d9d4c8` | `#14140e` | `#807c70` | `#c9c2b0` | `#c79a44` | Documentary, archival, considered. Reference, finance, records. |
| **Cream / Plum** | `#faf6ef` | `#ebe3d3` | `#1a1518` | `#8c8076` | `#d2c8b6` | `#7c5876` | Soft, refined, slightly unexpected. Creative tools, journals. |

**Picking logic for the picker option:**
1. Read `spec.md` (or `idea.md`). Extract mood signals from `## The job`, `## What's out there`, and `## What good looks like`.
2. Match against the "Mood signals" column above. First match wins.
3. If no match (ambiguous spec) — hash the project slug: `palette_index = sum(ord(c) for c in slug) % 6`. Deterministic so the same slug always gets the same palette.

**Apply this recipe verbatim in `DESIGN.md`** when this direction is picked:

| Token | Value | Why |
|-------|-------|-----|
| `--color-bg` | (palette `bg`) | Reads as crafted, not corporate. Pure white feels like a default. |
| `--color-bg-subtle` | (palette `bg-alt`) | Section dividers, asides — same warmth, deeper |
| `--color-text` | (palette `text`) | Slightly off-black holds warmth across the page |
| `--color-text-secondary` | (palette `text-secondary`) | Helper text, metadata |
| `--color-border` | (palette `border`) | Soft, never gray-200 |
| `--color-brand` | (palette `accent`) | Single accent. Used sparingly. |
| `--font-serif` | Lora (or similar reading serif) | Body text. Yes, body. |
| `--font-sans` | Inter (or similar utility sans) | UI labels, buttons, inputs |
| `--font-heading` | Poppins (or similar geometric heading) | h1-h4 |
| `--radius` | `1rem` (with 0.5–1.5rem scale) | Rounded but not bubbly |
| Shadows | `0 0.25rem 1.25rem rgba(0,0,0,0.035)` | Whisper, not slap |

**Direction label format for the picker** — use the palette name as the label:

```
{label: "Warm Paper / Coral",
 description: "Reading-room palette: paper bg, serif body, warm coral accent, soft warm borders. Conversational projects."}
```

Generate 3 picker options total: (1) the picked palette from the rotation set, (2) one project-shaped variation (precision tool / bold dashboard / etc), (3) "I'll describe it" free-text escape.

**Don't always pick coral.** If 5 V0s in a row land on Warm Paper / Coral because the rotation logic isn't varying, the rotation is broken — every project's mood is being read as conversational. Re-check the mood matching against the table.

**Why this floor exists:** V0s built with default Tailwind grays + system-ui + bootstrap blue look like prototypes. Token cost to do better is small. The recipe — warm-paper bg, serif body, single warm accent, soft warm borders, considered radius and whisper shadows — applies the same philosophy across all 6 palettes; only the hue rotates.

---

## Step 2: Fetch Reference Traits (if brand selected)

Run from the project directory so the output lands in the right place:
```bash
cd {paths.projects_dir}/<slug> && npx getdesign@latest add <brand>
```

`getdesign` is a public npm package (currently v0.6.3) — `npx` will fetch it on first run. Requires Node/npm. If `npx` is missing or the fetch fails, surface a one-line reason and continue without blocking.

**Verify DESIGN.md landed in the project dir.** `getdesign` walks up the filesystem looking for a `package.json` marker and writes `DESIGN.md` next to whichever it finds first. From inside a project subdir of a larger Vera workspace, that often means `DESIGN.md` lands at the workspace root instead of `{paths.projects_dir}/<slug>/`. Check both locations:

```bash
# If DESIGN.md isn't where it should be, mv it from wherever getdesign actually wrote it.
if [ ! -f "{paths.projects_dir}/<slug>/DESIGN.md" ]; then
  # Most common landing spot: the repo root above the project dir.
  for candidate in "$(git rev-parse --show-toplevel 2>/dev/null)" "$(pwd)/.." "$HOME"; do
    if [ -f "$candidate/DESIGN.md" ] && [ "$candidate" != "{paths.projects_dir}/<slug>" ]; then
      mv "$candidate/DESIGN.md" "{paths.projects_dir}/<slug>/DESIGN.md"
      break
    fi
  done
fi
```

This is a workaround for getdesign's package.json-walk-up behavior. Until that's fixed upstream, the mv keeps the artifact local to the project.

If it succeeds, read the generated `DESIGN.md` in the project dir. **Extract traits, don't copy the system:**

1. Identify: density model, contrast model, radius scale, border/shadow philosophy, typography tone, nav pattern
2. Compare against project needs (from spec.md)
3. Resolve conflicts — e.g., "keep Linear's density but warm it up for consumer onboarding"
4. Generate a new system informed by those traits

The output should read as "a design system for [project]," not "Linear but tweaked."

If fetch fails, generate from the direction answers. Don't block.

---

## Step 3: Architecture Diagram → `arch.md`

Skip if `--ui` only. Runs FIRST because wireframes need to know the component boundaries.

Read `spec.md` for the core flow. Generate:

Generate four sections using Mermaid:
1. **System Overview** — `graph TD` with subgraphs for Client/Server/External. Use actual component names from spec.md.
2. **Data Flow** — `sequenceDiagram` for the primary user action from spec.
3. **Components table** — Component, Responsibility, Tech, Owns Data, Connects To.
4. **Boundaries** — Auth boundary, client/server split, external dependencies.

5-10 nodes for quick, more for deep. This is the reviewer agent's structural reference.

---

## Step 4: DESIGN.md → `DESIGN.md`

Skip if `--arch` only. Runs AFTER arch (component inventory informs the design system). If `--ui` only and `arch.md` already exists in the project dir, read it for component context.

### Sections 1-9: Stitch Format

```markdown
# Design System — [Project Name]

## 1. Visual Theme & Atmosphere
[2-3 sentences from the direction choice. Name the density, tone, shape, contrast axes explicitly.]

## 2. Color Palette & Roles

### Semantic Roles
| Role | Token | Light | Dark | When to Use | When NOT to Use |
|------|-------|-------|------|-------------|-----------------|
| bg/default | `--color-bg` | #hex | #hex | Root page background, body | Cards, buttons, inputs |
| bg/subtle | `--color-bg-subtle` | #hex | #hex | Section backgrounds, table stripes | Page root, elevated surfaces |
| bg/elevated | `--color-bg-elevated` | #hex | #hex | Cards, dropdowns, popovers | Page background, inline elements |
| text/primary | `--color-text` | #hex | #hex | Headings, body text, labels | Placeholder text, disabled states |
| text/secondary | `--color-text-secondary` | #hex | #hex | Descriptions, helper text | Headings, primary actions |
| text/tertiary | `--color-text-tertiary` | #hex | #hex | Placeholders, timestamps, metadata | Body text, headings |
| border/default | `--color-border` | #hex | #hex | Input borders, card outlines | Decorative dividers within cards |
| border/subtle | `--color-border-subtle` | #hex | #hex | Dividers, table borders | Interactive element borders |
| fill/brand | `--color-brand` | #hex | #hex | Primary buttons, active indicators | Borders, backgrounds, body text |
| fill/brand-hover | `--color-brand-hover` | #hex | #hex | Hover state of brand elements only | Default state of anything |
| status/success | `--color-success` | #hex | #hex | Success alerts, positive indicators | Decorative use, brand accents |
| status/error | `--color-error` | #hex | #hex | Error states, destructive buttons | Warnings, decorative use |
| status/warning | `--color-warning` | #hex | #hex | Caution alerts, expiring states | Errors, success states |
| focus/ring | `--color-focus` | #hex | #hex | Focus-visible on all interactives | Decorative borders |
| overlay/scrim | `--color-overlay` | rgba | rgba | Behind modals and drawers | Inline content backgrounds |

### Accent Palette
[1-3 accent colors with hex + usage context]

## 3. Typography Rules

### Font Stack
- **Primary**: [font], [fallback stack]
- **Mono**: [font], [fallback stack]

### Scale
| Token | Size | Weight | Line Height | Letter Spacing | Use |
|-------|------|--------|-------------|----------------|-----|
| `--text-display` | Xpx | 600 | 1.1 | -Xpx | Hero headlines |
| `--text-heading` | Xpx | 600 | 1.2 | -Xpx | Section titles |
| `--text-subheading` | Xpx | 500 | 1.3 | normal | Card titles |
| `--text-body` | Xpx | 400 | 1.5 | normal | Reading text |
| `--text-small` | Xpx | 400 | 1.4 | normal | UI labels |
| `--text-caption` | Xpx | 400 | 1.3 | normal | Metadata |

## 4. Component Stylings

### Buttons
| Variant | Background | Text | Border | Radius | Padding | States |
|---------|-----------|------|--------|--------|---------|--------|
| Primary | brand | white | none | Xpx | X Y | hover: darken 10%, active: darken 15%, disabled: 50% opacity, focus: ring |
| Secondary | transparent | brand | 1px brand | Xpx | X Y | hover: bg subtle, ... |
| Ghost | transparent | text | none | Xpx | X Y | hover: bg subtle, ... |
| Destructive | error | white | none | Xpx | X Y | hover: darken, ... |

Sizes: sm (32px height), md (40px), lg (48px). Icon spacing: 8px gap.

### Cards
- Background: `bg/elevated`
- Border: [shadow-as-border or 1px solid border/subtle]
- Radius: Xpx
- Padding: Xpx
- Hover: [shadow intensification or border change]

### Inputs
- Height: 40px (md)
- Border: 1px solid border/default
- Focus: 2px ring focus/ring
- Error: border error, helper text below
- Placeholder: text/tertiary
- Radius: matches buttons

### Navigation
- Pattern: [sidebar / topbar / tabs]
- Active: [indicator style]
- Mobile: [collapse to hamburger / bottom tabs]

### Additional Components (--deep mode)

For complex systems, generate per-category reference files in `{paths.projects_dir}/<slug>/design/`:
- `design/form-elements.md` — Input, Textarea, Select, Checkbox, Radio, Switch, Date Picker
- `design/navigation.md` — Button, Link, Breadcrumbs, Tabs, Menu, Pagination
- `design/data-display.md` — Badge, Alert, Toast, Table, Avatar, Progress, Tooltip, Empty State, Skeleton

Each reference file should include per component:
- **Variant properties:** type, status, state, size (with defaults)
- **State flow:** empty → active → filled → error → disabled
- **Sizing cheat sheet:** when to use sm/md/lg in context
- **Do / Don't rules:** "Use Input (not bare field) for labeled form fields" / "Don't use more than one solid button per section"

## 5. Layout Principles

### Tokens
| Token | Value |
|-------|-------|
| `--space-1` | 4px |
| `--space-2` | 8px |
| `--space-3` | 12px |
| `--space-4` | 16px |
| `--space-6` | 24px |
| `--space-8` | 32px |
| `--space-12` | 48px |
| `--space-16` | 64px |
| `--radius-sm` | Xpx |
| `--radius-md` | Xpx |
| `--radius-lg` | Xpx |
| `--radius-full` | 9999px |

### Grid
- Max content: Xpx
- Columns: 12 (desktop), 8 (tablet), 4 (mobile)
- Gutter: `--space-4`

## 6. Depth & Elevation
| Level | Shadow | Use |
|-------|--------|-----|
| 0 | none | Flat surfaces |
| 1 | `0 1px 2px rgba(0,0,0,0.05)` | Cards, dropdowns |
| 2 | `0 4px 12px rgba(0,0,0,0.1)` | Modals, popovers |
| 3 | `0 8px 24px rgba(0,0,0,0.15)` | Floating panels |

## 7. Do's and Don'ts
- DO: [rules derived from the direction — e.g., "use whitespace to create hierarchy, not borders"]
- DON'T: [anti-patterns — e.g., "don't use more than 2 accent colors per screen"]
- DO: [accessibility rule — e.g., "maintain 4.5:1 contrast for body text"]
- DON'T: [common mistake for this style]

## 8. Responsive Behavior
| Breakpoint | Width | Changes |
|------------|-------|---------|
| Desktop | >1024px | Full layout |
| Tablet | 768-1024px | [specific collapse] |
| Mobile | <768px | [specific stack] |
- Touch targets: minimum 44px
- Font scaling: [if any]

## 9. Agent Prompt Guide
```
Primary: #hex | Brand: #hex | Background: #hex | Text: #hex
Font: [name] | Heading: weight X | Body: weight X
Radius: Xpx | Spacing unit: Xpx | Max width: Xpx
Shadow-border: [yes/no] | Border method: [description]
Vibe in one line: "[principle]"
```
```

### Section 10: Build Contract (--deep mode, or always for /build full)

The machine-readable spec the AI actually builds from. Add as `## 10. Build Contract` in DESIGN.md:

**Design Tokens** — Generate a `:root` CSS block with all tokens from sections 2, 3, 5, 6 as custom properties (`--color-bg`, `--color-text`, `--space-4`, etc.).

**Component Checklist** — Table: Component, Variants, States, Included. Cover every component needed by the core flow.

**Layout Templates** — Table: Page Type, Shell pattern, Key Regions. One row per screen type (Dashboard, Detail, Form, Auth, etc.).

**State Coverage** — Every screen handles: default, empty (illustration/message), loading (skeleton/spinner), error (inline alert).

**Accessibility** — WCAG AA (4.5:1 body text, 3:1 large text), visible focus ring on all interactives, 44px touch targets, respect `prefers-reduced-motion`.

---

## Step 5: Wireframes → `wireframes.md`

Skip if `--arch` only. Runs AFTER DESIGN.md (wireframes consume the component inventory and layout tokens).

Derive screens from the core flow in `spec.md`. Don't invent screens — each one maps to a user task.

### Structured Wireframe Format

```markdown
# Wireframes — [Project Name]

## Screen: [Name]
**Purpose:** [what the user accomplishes here]

### Layout
- Shell: [sidebar + topbar / topbar only / centered / etc.]
- Content width: [fluid to max-width / fixed / full-bleed]
- Sections (top to bottom):
  1. [Region name — e.g., KPI row]
  2. [Region name — e.g., Chart area]
  3. [Region name — e.g., Data table]

### Components (from DESIGN.md)
- [ComponentName] — [how it's used here]
- [ComponentName] — [how it's used here]

### Hierarchy
- Primary action: [what + where]
- Secondary actions: [what + where]
- Most prominent element: [what draws the eye]

### States
- **Empty:** [what the user sees before data exists]
- **Loading:** [skeleton/spinner placement]
- **Error:** [inline alert placement]

### Responsive
- Tablet: [what changes]
- Mobile: [what stacks/collapses]

### ASCII (optional visual aid)
┌──────────────────────────────┐
│ [rough block layout]         │
└──────────────────────────────┘
```

3-5 screens for `--quick`. Full core flow for `--deep`.

**Local HTML preview first (--deep):**
Before pushing to any design tool, build a local HTML preview. Iteration is faster locally.
1. Generate a single `preview.html` in the project root that renders the primary screen using the DESIGN.md tokens
2. Open in browser, verify the design direction works visually
3. Adjust tokens/components if needed — cheaper to fix here than after Stitch

**Then, if Stitch MCP available:**
1. `mcp__stitch__create_project`
2. For each screen: `mcp__stitch__generate_screen_from_text` with wireframe spec + DESIGN.md
3. `mcp__stitch__generate_variants` for the primary screen (2-3 options)
4. Record screen IDs in wireframes.md next to each screen

---

## Step 6: Save & Report

Save to `{paths.projects_dir}/<slug>/`:
- `arch.md`
- `DESIGN.md`
- `wireframes.md`

Flash summary: what was generated, key design decisions, token count.

If called by `/build` → return immediately. If standalone → "Adjust anything?"

---

## `/build` Integration

| Build Phase | Call | Depth |
|-------------|------|-------|
| V0 Stage 1 | `/frame <slug> --quick --from-spec` | quick (vibe from build's Stage 0) |
| Full SDLC Phase 2 | `/frame <slug> --deep --arch --from-spec` | deep arch |
| Full SDLC Phase 4 | `/frame <slug> --deep --ui --from-spec` | deep UI + wireframes (reads existing `arch.md` for component context) |

`/build` owns the user stop. `/frame` owns the design expertise.

---

*Author: Shareef Ellis · [@shareefatwork](https://x.com/shareefatwork)*
