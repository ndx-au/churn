# churn

**Harvest → Unify → Refine → Normalize**

Universal converter from legacy sources to [Google Open Knowledge Format (OKF)](https://github.com/GoogleCloudPlatform/knowledge-catalog) bundles.

Compatible with the sibling [ekg](../ekg) project for doctree consumption (frontmatter, _static assets, headings, folders, log.md).

## Status

M001–M004 complete (drivers, extract via [parse]/unstructured, OKF writer with ekg fidelity, CLI).

M005 in progress: beautiful CLI, Nuitka, MkDocs (this), cookiecutter, launch.

See [ROADMAP.md](../ROADMAP.md) and specs/.

## Quick Links

- [Quickstart](quickstart.md)
- CLI: `churn convert --help`
- Install: `pip install -e '.[parse,s3]'`

M005.003 — this MkDocs stub. Expand with content from README + specs + code docstrings.