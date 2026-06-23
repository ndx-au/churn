# Roadmap

High-level milestone plan for churn. Authoritative detail lives in [specs/ROADMAP.md](https://github.com/ndx-video/churn/blob/main/specs/ROADMAP.md) and per-milestone spec files.

**Goal:** Production-ready, extensible OKF converter — the community reference implementation for Google Open Knowledge Format.

## Milestones

### M001 — Foundations & Plugin Architecture ✅

Core package layout, `SourceDriver` ABC, setuptools entry-point discovery, Typer CLI skeleton, pydantic-settings config, pytest + ruff.

**Spec:** [M001-FOUNDATIONS.md](https://github.com/ndx-video/churn/blob/main/specs/M001-FOUNDATIONS.md)

Delivered:

- `pip install -e .` with `churn` console script
- `churn drivers list`, plugin registration pattern
- CONTRIBUTING-DRIVER template

---

### M002 — Core Drivers & Connectivity ✅

File, HTTP, and S3 connectivity with resilience and security.

**Spec:** [M002-CORE-DRIVERS.md](https://github.com/ndx-video/churn/blob/main/specs/M002-CORE-DRIVERS.md)

Delivered:

| Slice | Status |
|-------|--------|
| M002.001 FileSystemDriver | ✅ Multi-format walk, gitignore, root boundary |
| M002.002 HTTPDriver | ✅ Retries, streaming cap, URL basic auth |
| M002.003 S3/GCS driver | ✅ boto3, anonymous + B2 endpoint |
| M002.004 Retry + errors | ✅ tenacity (HTTP), surfaced S3 init errors |
| M002.006 SHA manifest | ✅ `manifest.json` on convert |
| M002.007 Tests | ✅ Discovery, hardening, CLI integration |

Remaining / future:

- M002.005 PKI + decryption hooks
- S3 `max_bytes` parity with HTTP/filesystem

---

### M003 — Decoding, Extraction & Normalization ✅

Turn raw bytes into clean Markdown + metadata hints.

**Spec:** [M003-PARSING.md](https://github.com/ndx-video/churn/blob/main/specs/M003-PARSING.md)

Delivered:

- Pass-through for `.md`, `.txt`, `.rst`
- Optional `unstructured[pdf,docx]` for rich PDF/DOCX/HTML
- Naive HTML fallback with title/description heuristics
- `--chunk` heading + unstructured element chunking
- `map_metadata` for frontmatter enrichment
- `--unstructured-languages` CLI config

Future:

- Deeper concept splitter / config surface
- Nested `.gitignore` in filesystem driver

---

### M004 — OKF Rendering, Validation & Compliance ✅

Bundle writer, validator, preview, ekg fidelity.

**Spec:** [M004-OKF-RENDERING.md](https://github.com/ndx-video/churn/blob/main/specs/M004-OKF-RENDERING.md)

Delivered:

| Slice | Status |
|-------|--------|
| M004.001 Bundle writer | ✅ Concepts, index, log |
| M004.002 Frontmatter | ✅ Concepts + folder `frontmatter.yaml` |
| M004.003 Validator | ✅ `churn validate`, `validate_bundle` |
| M004.005 Preview | ✅ `churn preview`, `churn log` |

Remaining:

- M004.004 Strict OKF 0.1 mode (Google validator parity)
- M004.006 Submit reference importer to Google repo

---

### M005 — CLI Polish, Packaging, Docs & Community Launch 🚧

Beautiful UX, distribution, documentation, contributor onboarding.

**Spec:** [M005-LAUNCH.md](https://github.com/ndx-video/churn/blob/main/specs/M005-LAUNCH.md)

| Slice | Status |
|-------|--------|
| M005.001 Rich CLI | ✅ Panels, progress bars on convert |
| M005.002 Nuitka binary | 📋 Stub in pyproject comments |
| M005.003 MkDocs | 🚧 This site (`mkdocs serve`) |
| M005.004 Cookiecutter driver | 📋 Template at `templates/driver-cookiecutter/` |
| M005.005 Community launch | 📋 Pending |

---

## How progress is tracked

churn uses [DotProgress](https://github.com/ndx-video/DotProgress): immutable entries under `.progress/`:

- `.progress/milestone/` — M001–M004 slice completions
- `.progress/general/` — cross-cutting work
- `.progress/fixes/` — bug fixes and hardening passes

See [.progress/README.md](https://github.com/ndx-video/churn/blob/main/.progress/README.md) for naming rules.

## Contributing

1. Pick a slice from specs/ or an open item above.
2. Implement with tests (`pytest`; 40 tests currently).
3. Append a DotProgress entry (never edit prior entries).
4. For drivers, follow [Contributing](contributing.md).

## Harness-driven development

Autonomous agent work is coordinated via `.grok/skills/churn-orchestrator` (see [AGENTS.md](https://github.com/ndx-video/churn/blob/main/AGENTS.md)). Use `churn-orchestrator` for milestone advances, driver work, OKF changes, tests, and re-work.