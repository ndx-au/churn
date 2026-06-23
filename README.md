# churn

**CHURN**: Harvest → Unify → Refine → Normalize.

Universal legacy knowledge → Google Open Knowledge Format (OKF) converter.
Community reference implementation intended for submission to GoogleCloudPlatform/knowledge-catalog.

## Quick Start (early build)

```bash
pip install -e .
churn --version
churn drivers list

# Convert a local file or tree to an OKF bundle
churn convert ./my-legacy-notes/ --out ./my-bundle

# With chunking for multi-heading docs
churn convert large-doc.md --chunk --out ./chunked-okf

# S3/B2 example (anon public bucket using CHURN_S3_* from .env)
churn convert s3://my-public-b2-bucket/path/to/file.md --out ./b2-okf

# Parse extra for rich PDF/DOCX (unstructured)
# pip install -e '.[parse]'
churn convert report.pdf --out ./pdf-okf   # uses rich extract, type 'PDF Document'

# The bundle contains:
#   index.md (+ log.md)
#   *.md (with required YAML frontmatter `type:` + recommended fields)
#   frontmatter.yaml (for ekg folders)
```

## Current Status (M001–M004 progress, M005 starting)

- [x] pyproject + plugin entry point discovery
- [x] SourceDriver ABC + registry
- [x] FileSystemDriver (opportunistic multi-format + extraction)
- [x] HTTPDriver (resilient fetches)
- [x] S3Driver (boto3, anon public + B2 endpoint support)
- [x] OKF writer (frontmatter + grouped index + folder frontmatter.yaml + log.md + validate_bundle)
- [x] Typer + Rich CLI (`drivers list`, `convert` --chunk, `preview`, `validate`)
- [x] Light extractor (optional unstructured for pdf/docx/html, hints to fm, chunk stub)
- [x] Tests (21p +1s), real smokes (curl, trees, B2 S3 anon, EKG roundtrips, richer PDF/DOCX with [parse])
- [ ] Deeper M003 chunking wiring / M004 log polish / M005 (Nuitka, docs)
- [x] Basic pytest + smoke tests
- Working real-world smoke: local files + live HTTP (httpbin)

See specs/ for full roadmap (M001–M005).

## Relationship to EKG

This project was conceived to feed the sibling `../ekg/` project.
All OKF output aims to be directly consumable when placed under an ERE `doctree/`.

See AGENTS.md for the ekg sibling location note.

## Development

```bash
pip install -e ".[dev,parse]"
pytest
ruff check .
```

Contributions via drivers (see CONTRIBUTING-DRIVER.md when written).
