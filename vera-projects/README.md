# Vera Projects

Your work output lives here. Harness files live in `../vera-system/`.

## Structure

```
vera-projects/
├── projects/                ← project workspaces (created by /build)
│   └── <slug>/              ← one project
│       ├── spec.md          ← what to build
│       ├── plans/           ← master plans from /build full
│       ├── research/        ← project-specific research
│       └── .build/          ← validation + review artifacts
└── research-output/         ← standalone research (not tied to a project)
```

These directories are created as needed by skills. Don't worry about setting them up manually.
