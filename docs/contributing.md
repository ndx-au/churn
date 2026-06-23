# Contributing a Driver

This guide covers the 15-minute path to a churn source driver plugin.

## 1. Implement the ABC

Subclass `churn.drivers.base.SourceDriver`:

```python
from churn.drivers.base import SourceDriver, SourceItem, FetchedContent

class MyDriver(SourceDriver):
    name = "mydriver"
    description = "Fetches from MyService"

    def list_items(self, query=None, **kw):
        # return list of SourceItem
        ...

    def fetch_item(self, item: SourceItem) -> FetchedContent:
        ...
```

See `churn/drivers/filesystem.py` and `churn/drivers/http.py` for reference implementations.

## 2. Package and register

Your package `pyproject.toml` must declare:

```toml
[project.entry-points."churn.drivers"]
mydriver = "my_driver_pkg:MyDriver"
```

Depend on `churn` (or implement against the base module only for minimal deps).

Built-in names (`filesystem`, `http`, `s3`) are reserved and cannot be overridden.

## 3. Design principles

- **Thin drivers** — connect, list, fetch bytes only; parsing and OKF rendering stay in core.
- **Security** — enforce scope boundaries, cap sizes, never log secrets.
- **Errors** — raise clear exceptions; the CLI reports per-item failures.

See [Drivers](drivers.md) for built-in security patterns.

## 4. Test

```bash
pip install -e .
pytest tests/                    # your package tests
churn drivers list               # should list mydriver after pip install -e your-pkg
churn convert mydriver:query --out /tmp/out
churn validate /tmp/out
```

## 5. Cookiecutter template

A starter template lives at `templates/driver-cookiecutter/` in the churn repo (M005 stub).

## 6. OKF expectations

End-to-end conversion must produce concepts with non-empty `type:` frontmatter. See [OKF & EKG](okf-ekg.md).

## Pull requests

Update your package README with example usage. PRs welcome against the churn repo for built-in driver improvements; external drivers live in their own packages.