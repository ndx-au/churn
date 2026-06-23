---
name: dotprogress
description: >
  Append-only progress logging (Dot Progress). Use after meaningful sessions that
  change specs, architecture, APIs, conventions, or roadmap work — or when recording
  a bug fix or regression. Entries are immutable; never edit committed entries.
paths:
  - ".progress/**/*.md"
  - "ROADMAP.md"
---

# Progress log (DotProgress)

Implement [.progress/README.md](../../../.progress/README.md). Plan in [ROADMAP.md](../../../ROADMAP.md) (if present); record by **appending** a new file.

## Choose entry type

| Type | Subfolder | Prefix | Use when |
|------|-----------|--------|----------|
| Milestone | `.progress/milestone/` | `M{n}.{index}.` | Session advances a roadmap milestone |
| General | `.progress/general/` | `G{number}.` | Meaningful work not tied to a milestone |
| Fix | `.progress/fixes/` | `F{number}.` | Bug fix or regression repair |

Entries live in type subfolders; `README.md` stays at the `.progress/` root. Counters are global per prefix, not per subfolder.

## Workflow

1. Decide type (milestone vs general vs fix).
2. List existing files for that prefix in its subfolder and pick the **next** index (three-digit milestone) or **six-digit** number (`G`/`F`).
3. Copy the entry template from `.progress/README.md`.
4. Set `milestone` frontmatter: roadmap short form, `General`, or `Fix`.
5. Write Summary, Changes, Decisions, Follow-ups, References.
6. **Never** edit, rename, or delete a committed progress file — add a new entry instead.

## Quick numbering

```bash
ls .progress/milestone/M000.*.md   # milestone M0 — next three-digit index
ls .progress/general/G*.md         # general — next six-digit G00000n
ls .progress/fixes/F*.md           # fix — next six-digit F00000n
```

Skip entries only for trivial typos with zero design impact.
