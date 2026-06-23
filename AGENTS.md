# Agent Guide — churn

Instructions for AI coding agents working in this repository.

## DotProgress

Read and **implement** [.progress/README.md](.progress/README.md). That file is the single source of truth for the Dot Progress convention — entry types, subfolder layout, naming, immutability, YAML frontmatter template, and when to append progress files.

Entries live in type subfolders: `.progress/milestone/` (`M{n}.{index}.*`), `.progress/general/` (`G{number}.*`), `.progress/fixes/` (`F{number}.*`). Milestone index is three-digit per milestone; General/Fix use a global six-digit counter per prefix.

This project adopts the DotProgress convention from https://github.com/ndx-video/DotProgress.

## EKG Project Location

**Important:** The "ekg" project referred to in the specs has its source code in a sibling folder at `../ekg` relative to this project (`churn`).

When specs, whitepaper, or tasks reference the ekg project (e.g. for OKF consumption, integration points, or cross-repo behaviors), look for the actual implementation and details in:

- `../ekg/`

Adjust any relative references or plans accordingly.

## Workflow

- Plan in [ROADMAP.md](ROADMAP.md) and [specs/](specs/).
- Record completed work by appending a new `.progress/` entry (never edit prior entries).
- Use the entry template and naming rules in [.progress/README.md](.progress/README.md).
- For project context, see [README.md](README.md) and the specs/ directory.

## Optional Agent Harness

For automatic enforcement, the `.claude/` rules/skills from DotProgress can be added if your agent supports them.

## Harness (Grok Agent Team)

**Goal:** Autonomous implementation of the full churn project (Python OKF converter) from specs/ + ekg sibling compatibility.

**Trigger:** Use `churn-orchestrator` skill for any build, advance milestone slice, driver, OKF rendering, test, or re-work on the churn package. It coordinates specialist subagents (researcher, foundations, drivers, okf, quality, architect).

**Execution:** Follows hybrid orchestration with spawn_subagent, todo_write, _workspace/ handoff, and strict DotProgress appends.

## Change History (Harness + Major Work)

| Date       | Change                          | Target          | Reason |
|------------|---------------------------------|-----------------|--------|
| 2026-06-23 | Initial harness bootstrap       | .grok/ + orchestrator | Enable autonomous full project build from specs |
| 2026-06-23 | DotProgress + ekg sibling note  | AGENTS.md       | Prior setup |
| 2026-06-23 | Continued next steps (chunking wire, log.md, S3 B2 anon smoke, rich progress, docs) | .grok/ + .progress + code | Per previous autonomous plan + quality review |
| 2026-06-23 | [parse] re-smoke richer PDF, extract config support, EKG roundtrip on PDF bundle, S3 B2 anon verified | code + .progress | Unstructured active, deeper M003 start, EKG checks |
| 2026-06-23 | Opportunistic hardening pass (convert bugs, chunking, driver security, 12 new tests) | code + .progress/fixes | Harness maintenance /harness audit |
| 2026-06-23 | Second harness pass (HTTP URL auth, gitignore, S3 mock test, drivers skill) | code + .grok/ + .progress/fixes | /harness codebase audit |
| 2026-06-23 | Comprehensive MkDocs docs (6 pages, CLI/drivers/OKF/roadmap) | docs/ + README | User request post-harness |

