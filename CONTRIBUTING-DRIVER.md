# Contributing a Driver to CHURN

This is the 15-minute template referenced in the whitepaper and M001.

## 1. Implement the ABC

Subclass `churn.drivers.base.SourceDriver`.

Minimal:

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

See `churn/drivers/filesystem.py` and `http.py` for examples.

## 2. Package it

- `pyproject.toml` of your package must declare:
  ```toml
  [project.entry-points."churn.drivers"]
  mydriver = "my_driver_pkg:MyDriver"
  ```

- Depend on `churn` (or just the base if minimal).

## 3. Security & best practices (base handles most)

- Base owns credentials injection, retry, SHA manifest, error wrapping.
- Your driver should be thin: connect / list / fetch bytes.
- Never log secrets.

## 4. Test

- Unit for list/fetch with tmp or mocks.
- Smoke: `churn drivers list` should show it after `pip install`.
- End-to-end: `churn convert mydriver:some-query --out /tmp/out` produces OKF bundle with `type:` frontmatter.

## 5. Docs

Update your README with example usage.

See specs/ and the main README for OKF expectations and ekg compatibility notes.

PRs welcome!
