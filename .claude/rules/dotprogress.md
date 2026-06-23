---
paths:
  - ".progress/**/*.md"
  - "ROADMAP.md"
---

# DotProgress entry

Follow [.progress/README.md](../../.progress/README.md). Entries are **append-only** — never edit, rename, or delete committed files.

## Entry type

| Type | Subfolder | Filename | When |
|------|-----------|----------|------|
| Milestone | `.progress/milestone/` | `M{n}.{index}.{descriptor}.md` | Work advances a roadmap milestone |
| General | `.progress/general/` | `G{number}.{descriptor}.md` | Meaningful work not tied to a milestone |
| Fix | `.progress/fixes/` | `F{number}.{descriptor}.md` | Bug fix or regression repair |

Entries live in type subfolders; `.progress/README.md` stays at the root. Counters are global per prefix (not per subfolder).

## Before creating a file

Scan the matching subfolder for the next index or number:

- **Milestone:** `ls .progress/milestone/M000.*.md` → next **three-digit** index for that milestone (`001`+)
- **General:** `ls .progress/general/G*.md` → next **six-digit** number (`000001`+)
- **Fix:** `ls .progress/fixes/F*.md` → next **six-digit** number (`000001`+)

Set frontmatter `milestone` to the roadmap short form (e.g. `M0 — Bootstrap`), `General`, or `Fix`. Use `{title}` in the H1 — not necessarily the milestone label. Copy the entry template from `.progress/README.md`.
