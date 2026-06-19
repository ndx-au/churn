# CHURN — Universal Legacy-to-OKF Converter
**The Community Reference Implementation for Google Open Knowledge Format (OKF)**

**Version:** 0.1-draft  
**Date:** 19 June 2026  
**License:** Apache 2.0  
**Repo:** (you will create) github.com/yourname/churn-okf

## Vision
CHURN is the universal importer Google did not ship: it converts any legacy knowledge source (files at rest, services over protocols, encrypted archives, exotic formats) into clean, validator-passing OKF bundles.

We explicitly position CHURN as **“the official community reference implementation for legacy → OKF conversion”** and will submit it to the GoogleCloudPlatform/knowledge-catalog repo.

## Core Architecture: Driver Plugin System (Python-idiomatic)

CHURN uses a clean entry-point + abstract base class system so contributors can add new drivers with one `pip install` and zero core changes.

- `churn/drivers/base.py` — `SourceDriver` ABC
- `pyproject.toml` registers drivers via `[project.entry-points."churn.drivers"]`
- New driver example: `pip install churn-driver-confluence` → automatically appears in `churn drivers list`

This is the exact pattern used by `black`, `pytest`, `langchain` community loaders, and `pluggy` — every experienced Python developer knows it.

Full security slices (connectivity, decoding, PKI, SHA validation, credentials) are handled in the base class so driver authors only implement `connect()`, `list_items()`, and `fetch_item()`.

See CONTRIBUTING-DRIVER.md for the 15-minute template.

## Roadmap & Milestones
See ROADMAP.md (M001–M005).

We ship as both `pip` package and single executable via Nuitka so non-Python users can just download `churn.exe`.
