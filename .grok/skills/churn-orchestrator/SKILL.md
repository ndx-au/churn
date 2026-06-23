---
name: churn-orchestrator
description: "Orchestrates the full autonomous build of the churn project using specialist subagents. Trigger for: build churn, implement specs, advance M001/M002/M003..., add drivers, OKF rendering, smoke tests, improve previous work, fix issues, re-run slices. Always use this for follow-up on churn codebase."
when-to-use: "Any work that advances the churn Python package implementation, drivers, OKF output, CLI, tests per the specs/ folder and ekg sibling compatibility. Re-runs, partials, and extensions."
---

# Churn Project Orchestrator

Coordinates a specialist team to build the complete "churn" legacy-to-OKF converter (Python, plugin-based, per specs/Milestones) so that it can feed OKF bundles into the sibling ../ekg/ project and act as the community reference implementation.

**Execution style:** Hybrid (parallel research + sequential build phases + producer-review loops via resume_from + todo tracking). Orchestrator owns state via todo_write and `_workspace/`.

## Team Roles (use spawn_subagent with these as subagent_type where custom .grok/agents/ exist)

| Role                  | subagent_type        | Primary Focus                     | Typical Output                  |
|-----------------------|----------------------|-----------------------------------|---------------------------------|
| Researcher            | churn-researcher     | OKF spec, ekg compat, sources     | _workspace/01_research-*.md    |
| Foundations           | foundations-engineer | pyproject, ABC, CLI skeleton      | package files + tests           |
| Drivers               | drivers-engineer     | File/HTTP/S3 + base integration   | drivers/*.py + smoke            |
| OKF Renderer          | okf-engineer         | Bundle writer + frontmatter + index | okf/ + sample bundles           |
| Quality/Smoke         | quality-smoke-tester | pytest + real smoke (curl etc)    | test files + execution logs     |
| Architect (lead)      | churn-architect      | Design, integration, decisions    | reviews + .progress entries     |

Use `general-purpose` for simple glue if needed. Always prefix description with [role].

## File Handoff Convention (strict)
- `_workspace/00_input/` : snapshots of request + key specs
- `_workspace/01_research-*.md`
- `_workspace/02_foundations/`
- `_workspace/03_drivers/`
- `_workspace/04_okf/`
- `_workspace/05_tests/`
- `_workspace/99_final-report.md`
- Actual code changes are made directly to the workspace tree (churn/ src etc). Use workspace files for analysis notes only.

## Workflow

### Phase 0: Context Check
- If `_workspace/` exists:
  - User says "only fix X" or "re-run slice Y" → partial: re-spawn only affected roles, feed them prior artifacts.
  - New major request → mv _workspace _workspace_prev_$(date +%s) and start fresh.
- Else → fresh.
- Always load current specs/ + AGENTS.md + recent .progress/milestone/ entries + sibling ekg key files (parser, OKF docs).
- Initialize shared todo list with high-level phases: research, foundations, drivers, okf-renderer, quality, integrate, smoke, document.

### Phase 1: Research & Alignment (parallel capable)
Spawn `[researcher]` (background) + optionally architect review.
- Deep dive OKF SPEC + ekg's handling.
- Identify 3-5 opportunistic input sources for first drivers (File multi-format wins; HTTP; S3).
- Map M00x slices to concrete tasks.
- Write research summary.
- Update todos.

### Phase 2: Foundations (M001 core)
Spawn `[foundations-engineer]`.
- Implement pyproject.toml, layout (churn/, tests/, drivers/base.py).
- Plugin registry + entry points.
- Minimal Typer CLI (churn --help, churn drivers list).
- Credential base.
- Basic tests.
- After, spawn quick `[quality-smoke-tester]` smoke for `churn --version` / drivers list.
- Append .progress entry for M001 slice.

### Phase 3: Drivers (M002)
Spawn `[drivers-engineer]` (can parallelize fs + http).
- Implement SourceDriver ABC first if not present.
- FileSystemDriver (opportunistic: .md, .txt, .pdf via unstructured if dep added, html).
- HTTPDriver (use real fetches + auth option).
- S3Driver (boto, signed or anon).
- Common: retry, manifest sha.
- CLI integration: `churn list <source>`, `churn fetch ...`
- Smoke: use run_terminal or actual curl simulation in tests.

### Phase 4: OKF Rendering & Compliance (M004 early for feedback)
Spawn `[okf-engineer]`.
- Bundle writer: output dir with correct .md + frontmatter (type required).
- index.md + optional log.md generator.
- Basic validator (conformance check).
- Preview command.
- Produce sample OKF bundle from a driver fetch.
- Verify mentally/ by inspection against ekg doctree samples.
- Make bundles ekg-sync friendly (folder layout, frontmatter.yaml hints if needed, but primarily flat concept md).

### Phase 5: Parsing/Normalization + More (M003)
- Extend drivers or add extractor layer.
- Use unstructured etc for rich content → normalized MD concepts.
- Chunking stub.
- Metadata mapper.

### Phase 6: Quality, Polish, Smoke & M005 slices
- Full test suite + CI.
- Smoke tests: real FS tree conversion, httpbin.org or public MD URL via curl-like, produce OKF, ls the bundle.
- Beautiful CLI (rich panels, progress bars via rich).
- Stubs for remaining (Nuitka, MkDocs, cookiecutter) with .progress todos.
- Update root docs.

### Phase 7: Integration & Reporting
- Architect reviews cross-cuts (plugin + OKF + ekg fit).
- Write 99_final-report.md summarizing slices, commands to demo, known stubs, next todos.
- Ensure every major slice has a corresponding .progress/milestone/M00x.xxx.*.md appended (use the DotProgress convention strictly: new file only).
- Leave `_workspace/` for audit.

## Data Passing
- Orchestrator reads prior phase outputs and injects paths or summaries into next spawn prompt.
- Engineers write code directly (cwd is project root).
- Use shared `_workspace/` notes for large analysis.

## Error Handling (mandatory)
- One subagent fails → retry once (resume_from with failure context), else mark todo failed + continue with "X incomplete because Y" note.
- Conflicting research → architect decides; record rationale in progress + report.
- Never delete prior progress entries.

## Testing Scenarios (in orchestrator execution)
1. Normal: "Implement M001 foundations + M002.001 FileSystemDriver end-to-end with smoke."
   - Expect: installable package, drivers list shows filesystem, convert local dir to okf bundle, pytest passes, smoke output captured.
2. Error/recovery: "Add HTTP driver but simulate bad auth." 
   - Expect: clear error, partial progress entry, tests cover the case.

## Post-run
- Summarize produced files and demo commands to user.
- Update AGENTS.md change history if structural harness change.
- Always propose next slice or ask for focus.

Respect DotProgress: after significant work, the orchestrator or delegated role MUST append a properly named new entry under .progress/ (never edit).
