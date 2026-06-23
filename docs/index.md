# churn

**Harvest → Unify → Refine → Normalize**

Universal converter from legacy sources to [Google Open Knowledge Format (OKF)](https://github.com/GoogleCloudPlatform/knowledge-catalog) bundles.

churn is a Python CLI and plugin framework: **drivers** fetch raw bytes, **extract** normalizes them to Markdown, and the **OKF writer** emits a bundle that the sibling **ekg** project (`../ekg` relative to this repo) can consume directly from an ERE `doctree/`.

## What you get

An OKF bundle directory typically contains:

| Artifact | Purpose |
|----------|---------|
| `*.md` concept files | Leading YAML frontmatter with required `type:` plus body |
| `index.md` | Grouped links to all concepts (OKF §6) |
| `log.md` | Creation/update log (OKF §7) |
| `frontmatter.yaml` | Per-folder metadata for ekg-style navigation |
| `_static/` | Asset directory for images and attachments |
| `manifest.json` | SHA-256 manifest of concept files |

## Current status

| Milestone | Status | Highlights |
|-----------|--------|------------|
| M001 Foundations | Complete | pyproject, `SourceDriver` ABC, entry-point discovery, Typer CLI |
| M002 Drivers | Complete | filesystem, HTTP, S3; retries, size caps, security boundaries |
| M003 Parsing | Complete | Markdown pass-through, unstructured PDF/DOCX/HTML, heading chunking |
| M004 OKF | Complete | Writer, validator, preview, log.md, ekg folder frontmatter |
| M005 Launch | In progress | MkDocs (this site), Nuitka binary, cookiecutter polish |

**Tests:** 40 passing (unit, integration, network smoke where marked).

## Install

```bash
# Core CLI
pip install -e .

# Rich document extraction (PDF, DOCX, HTML via unstructured)
pip install -e '.[parse]'

# S3 / GCS-compatible object storage (boto3)
pip install -e '.[parse,s3]'

# Development
pip install -e '.[dev,parse,s3]'
```

Requires **Python 3.10+**.

## Quick example

```bash
churn --version
churn drivers list
churn convert ./my-notes/ --out ./my-bundle
churn validate ./my-bundle
churn preview ./my-bundle
```

## Documentation map

| Page | Contents |
|------|----------|
| [Quickstart](quickstart.md) | Install, first conversion, common workflows |
| [CLI Reference](cli.md) | Every command, flag, and source format |
| [Drivers](drivers.md) | Built-in drivers, config, plugins |
| [OKF & EKG](okf-ekg.md) | Bundle layout, validation, ekg compatibility |
| [Contributing](contributing.md) | Plugin driver guide |
| [Roadmap](roadmap.md) | Milestones and planned work |

## Project links (repository)

- Source specs: [specs/](https://github.com/ndx-video/churn/tree/main/specs)
- Living roadmap: [ROADMAP.md](https://github.com/ndx-video/churn/blob/main/ROADMAP.md)
- Agent harness: [AGENTS.md](https://github.com/ndx-video/churn/blob/main/AGENTS.md)

## Serve this site locally

```bash
pip install mkdocs mkdocs-material
mkdocs serve
```

Open `http://127.0.0.1:8000` (M005.003).