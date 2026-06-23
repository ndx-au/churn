# Dot Progress — progress log spec

Immutable audit trail for project work. Record **what happened and why** by **appending** new files — never edit, rename, or delete committed entries.

Tie milestone work to your project's milestones (typically from [ROADMAP.md](../ROADMAP.md) at the repo root, if you use one). Use **General** or **Fix** entries for meaningful work that is not tied to a milestone. This folder is **tracked in git**. Do not add `.progress/` to `.gitignore`.

## Directory layout

Entries are grouped into subfolders **by type** so the log stays easy for humans to browse. `README.md` stays at the `.progress/` root; every entry lives under its type folder.

| Subfolder | Entry type | Prefix |
|-----------|------------|--------|
| `.progress/milestone/` | Milestone | `M{milestone}.{index}.` |
| `.progress/general/` | General | `G{number}.` |
| `.progress/fixes/` | Fix | `F{number}.` |

Counters are **global per prefix** across the whole log (not per subfolder). An optional agent-harness layer (`.claude/rules/` + `.claude/skills/`) can enforce this automatically — see [Agent integration](#agent-integration).

## Filename convention (strict)

Choose the prefix that matches the entry type:

| Type | When to use | Format |
|------|-------------|--------|
| **Milestone** | Work advances a roadmap milestone | `{milestone}.{index}.{descriptor}.md` |
| **General** | Meaningful work not tied to a milestone | `G{number}.{descriptor}.md` |
| **Fix** | Bug fix or regression repair | `F{number}.{descriptor}.md` |

### Milestone entries

```
milestone/{milestone}.{index}.{descriptor}.md
```

| Segment | Format | Example |
|---------|--------|---------|
| `milestone` | `M` + milestone number **zero-padded to three digits** (`M000` = milestone 0, `M001` = milestone 1, …) | `M000`, `M002` |
| `index` | **Three-digit** zero-padded sequence **per milestone**, monotonic | `001`, `002`, `013` |
| `descriptor` | Lowercase kebab-case summary of **this entry only** | `example-entry` |

**Full example:** `milestone/M000.002.websocket-viewport-spec.md`

> Only the **filename** milestone token is zero-padded. Prose references (e.g. "M0 — Bootstrap", the `milestone` frontmatter field) may use your roadmap's short form.

### General and Fix entries

```
general/G{number}.{descriptor}.md
fixes/F{number}.{descriptor}.md
```

| Segment | Format | Example |
|---------|--------|---------|
| `prefix` | `G` for general work; `F` for fixes | `G`, `F` |
| `number` | **Six-digit** zero-padded sequence **per prefix**, monotonic | `000001`, `000012` |
| `descriptor` | Lowercase kebab-case summary of **this entry only** | `this-is-a-general-change` |

**Full examples:** `general/G000012.this-is-a-general-change.md`, `fixes/F000003.fix-login-redirect.md`

> General and Fix entries use a **single** six-digit counter per prefix — not the milestone `M` + three-digit index pattern.

### Index rules

**Milestone (`M`):**
- Each milestone has its **own** counter starting at `001`.
- Always use the **next** available index for that milestone (scan existing files in `.progress/milestone/`).
- Never reuse or renumber an index after a file is committed.
- Gaps are allowed; do not backfill.

**General (`G`) and Fix (`F`):**
- Each prefix has its **own** global counter starting at `000001` (six-digit zero-padded).
- Always use the **next** available number for that prefix (scan existing `G*.md` in `.progress/general/` or `F*.md` in `.progress/fixes/`).
- Never reuse or renumber a number after a file is committed.
- Gaps are allowed; do not backfill.

### Descriptor rules

- Short, stable, human-readable slug.
- Describe **this** entry only (not the whole milestone or theme).
- Regressions and reversals get **new** descriptors (e.g. `revert-auth-refactor`).

## Immutability (strict)

| Allowed | Forbidden |
|---------|-----------|
| Create a **new** file with the next index or number | Edit, rename, or delete an existing progress file |
| Document a regression as a **new** entry | "Fix" or overwrite a prior entry |
| Reference earlier entries by filename/link | Consolidate multiple events into one retroactive doc |

> A one-time, maintainer-led **structural migration** of the log itself (e.g. adopting these subfolders) is the only exception — record it as a new entry that explains the move.

## When to write an entry

Create a progress document at the end of any session that:

- Completes or partially completes roadmap work
- Changes specs, architecture, APIs, or conventions
- Makes a decision future agents should understand
- Introduces a regression or reverts direction (say so explicitly)

Skip entries only for trivial typo fixes with zero design impact.

## Entry template

Copy into each new file:

```markdown
---
file: {filename}
date: YYYY-MM-DD
milestone: M{n} — {name from ROADMAP} | General | Fix
related_commits: {hash or uncommitted}
---

# {title}

## Summary

One paragraph: what happened and why.

## Changes

- Bullet list of artifacts touched

## Decisions

- Anything entailed for downstream work

## Follow-ups

- Open items, if any

## References

- Links to specs, prior progress entries, issues
```

For General entries, set `milestone: General`. For Fix entries, set `milestone: Fix`. For roadmap work, use the roadmap short form (e.g. `M0 — Bootstrap`).

Filled-in examples:

- [milestone/M000.001.example-entry.md](milestone/M000.001.example-entry.md) — milestone (`milestone: M0 — Bootstrap`)
- [general/G000001.example-general-entry.md](general/G000001.example-general-entry.md) — general (`milestone: General`)
- [fixes/F000001.example-fix-entry.md](fixes/F000001.example-fix-entry.md) — fix (`milestone: Fix`)

## Relationship to other docs

| Document | Role |
|----------|------|
| [ROADMAP.md](../ROADMAP.md) | **What** to build, milestone gates *(optional)* |
| `.progress/` | **Historical record** of what was done, when, and why |

## Finding the next number

Before creating a file, list existing entries for the relevant prefix in its subfolder:

**Milestone:**

```bash
ls .progress/milestone/M000.*.md
```

Use max(index) + 1 (three-digit). If none exist, start at `001`.

**General:**

```bash
ls .progress/general/G*.md
```

Use max(number) + 1 (six-digit). If none exist, start at `000001`.

**Fix:**

```bash
ls .progress/fixes/F*.md
```

Use max(number) + 1 (six-digit). If none exist, start at `000001`.

## Agent integration

Dot Progress is agent-native. The optional `.claude/` layer turns this spec into automatic behavior for AI coding agents (Cursor, Claude Code, and compatible harnesses):

| Artifact | Role |
|----------|------|
| [`.claude/rules/dotprogress.md`](../.claude/rules/dotprogress.md) | Path-glob rule — loads this convention whenever an agent touches `.progress/**` or `ROADMAP.md` |
| [`.claude/skills/dotprogress/SKILL.md`](../.claude/skills/dotprogress/SKILL.md) | Skill — the append-an-entry procedure an agent invokes at end of a meaningful session |

Both are generic and copy-paste portable. Adopt them by copying the `.claude/` files alongside `.progress/`; no project-specific edits required.
