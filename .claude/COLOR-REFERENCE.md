# Color Reference

ANSI color conventions for chat output. Skills use these consistently so the user trains their eye across surfaces.

| Purpose | Color | ANSI | Used by |
|---------|-------|------|---------|
| **Notification** — "Vera is telling me something" | Dark orange | `\033[1;38;5;208m` | Vera check-ins, ship checklists, alerts |
| **Output artifact** — "this is Vera's product" | Gold | `\033[1;38;5;214m` | `/start-here` idea doc |
| **Chrome** — framing, banners | Padres brown | `\033[38;5;130m` | bootstrap banner |

Always reset with `\033[0m`. Fall back to plain text on non-TTY (hooks/pipes).
