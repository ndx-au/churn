# Drivers

Drivers are the **fetch layer** of churn. Each driver implements `SourceDriver`: connect, list discoverable items, fetch raw bytes. Parsing, chunking, and OKF rendering happen in the core after fetch.

## Architecture

```
SOURCE → [Driver: list + fetch] → bytes → [extract] → Markdown → [OKF writer] → bundle/
```

| Component | Location |
|-----------|----------|
| ABC + dataclasses | `churn/drivers/base.py` |
| Discovery | `churn/drivers/__init__.py` |
| Built-ins | `churn/drivers/filesystem.py`, `http.py`, `s3.py` |
| CLI dispatch | `churn/cli.py` → `_resolve_driver_and_query` |

Drivers register through setuptools entry points:

```toml
[project.entry-points."churn.drivers"]
mydriver = "my_package:MyDriver"
```

Built-in names (`filesystem`, `http`, `s3`) are reserved — external plugins cannot override them.

## Built-in drivers

### filesystem

**Name:** `filesystem`  
**Description:** Local files and directory trees.

| Capability | Detail |
|------------|--------|
| List | Recursive walk from query path or configured `root` |
| Formats | `.md`, `.txt`, `.rst`, `.html`, `.pdf`, `.docx` (extraction in core) |
| Security | `fetch_item` refuses paths outside `root`; `list_items` returns empty for out-of-root queries |
| Skips | `.git`, `.svn`, `node_modules`, `.venv`, `__pycache__`, and similar |
| Gitignore | Root `.gitignore` respected by default (`respect_gitignore: true`) |
| Size cap | Skips / rejects files over `max_file_bytes` (default 50 MiB) |

**Config keys:**

| Key | Default | Description |
|-----|---------|-------------|
| `root` | `.` | Boundary for relative paths and security checks |
| `max_file_bytes` | `52428800` | Maximum file size |
| `respect_gitignore` | `true` | Honor root `.gitignore` during discovery |

**CLI usage:**

```bash
churn convert ./my-dir/ --out ./okf
churn convert filesystem:./my-dir/specific.md --out ./okf
```

Concept IDs mirror relative paths: `docs/guide.md` → `docs/guide.md` in the bundle.

---

### http

**Name:** `http`  
**Description:** HTTP/HTTPS GET with retries and streaming size limits.

| Capability | Detail |
|------------|--------|
| List | Single-item list when query is a URL |
| Fetch | Streaming download with `max_bytes` cap (default 50 MiB) |
| Retry | Up to 3 attempts on 5xx, 429, timeouts, transport errors |
| Auth | Basic auth via config `auth` tuple or URL credentials (`https://user:pass@host`) |
| Redirects | Followed automatically |

**Config keys:**

| Key | Default | Description |
|-----|---------|-------------|
| `timeout` | `30` | Request timeout (seconds) |
| `headers` | `{}` | Extra request headers |
| `max_bytes` | `52428800` | Maximum response size |
| `auth` | `None` | `(username, password)` for HTTP basic auth |

**CLI usage:**

```bash
churn convert https://example.com/api/doc.json --out ./okf
churn convert http:https://internal.example.com/data --out ./okf
churn convert https://user:token@internal.example.com/secret --out ./okf
```

Credentials in URLs are stripped before fetch and metadata; they are not written to the bundle.

Concept IDs use URL stem + short hash: `doc-a1b2c3d4e5.md`.

---

### s3

**Name:** `s3`  
**Description:** S3- and GCS-compatible object storage via boto3.

| Capability | Detail |
|------------|--------|
| List | `list_objects_v2` under `bucket/prefix` |
| Fetch | `get_object` by bucket/key |
| Anonymous | UNSIGNED requests for public buckets |
| Endpoints | Custom endpoints (Backblaze B2, MinIO, etc.) via `endpoint_url` |
| Errors | Init failures surfaced with actionable messages |

Requires `pip install -e '.[s3]'` (boto3).

**Config keys:**

| Key | Description |
|-----|-------------|
| `endpoint_url` / `endpoint` | Custom S3-compatible endpoint |
| `region` | Region name (default `us-east-1`) |
| `aws_access_key_id` / `access_key_id` | Access key |
| `aws_secret_access_key` / `secret_access_key` | Secret key |
| `anonymous` | `true` for unsigned public access |

Environment variables (`CHURN_S3_*`) merge into config when not set explicitly. See [CLI Reference](cli.md#environment-variables).

**CLI usage:**

```bash
# Public bucket
churn convert s3://my-bucket/path/doc.md --s3-anonymous --out ./okf

# Prefix (many objects; subject to --limit)
churn convert s3://my-bucket/docs/ --out ./okf

# Explicit driver form
churn convert s3:my-bucket/prefix/ --out ./okf
```

URI form: `s3://bucket/key` or `s3://bucket/prefix/`. Keys ending in `/` are skipped during listing.

---

## Driver lifecycle

```python
from churn.drivers import get_driver

driver = get_driver("filesystem", {"root": "/data"})
driver.connect()
items = driver.list_items("/data/docs")
content = driver.fetch_item(items[0])
driver.close()
```

Or as a context manager:

```python
with get_driver("http") as driver:
    items = driver.list_items("https://example.com")
    ...
```

The CLI always calls `close()` in a `finally` block after `convert`.

## Writing a plugin driver

1. Subclass `SourceDriver` — implement `list_items` and `fetch_item`.
2. Set class attributes `name` and `description`.
3. Register an entry point under `churn.drivers`.
4. Keep the driver thin: return bytes + mime; do not parse OKF.

Full guide: [Contributing](contributing.md).

Cookiecutter template (M005 stub): `templates/driver-cookiecutter/`.

**Smoke test after install:**

```bash
churn drivers list                    # shows your driver
churn convert mydriver:query --out /tmp/out
churn validate /tmp/out
```

## Security checklist

| Rule | Rationale |
|------|-----------|
| Enforce root/scope boundaries on list **and** fetch | Prevents path traversal and confused-deputy reads |
| Cap download sizes | Protects against oversized responses/objects |
| Strip credentials from URLs and logs | Prevents secret leakage in bundles and terminals |
| Do not override built-in driver names | Predictable core behavior for all users |
| Surface errors clearly | CLI reports per-item failures without silent drops |

## Testing drivers

| Test file | Coverage |
|-----------|----------|
| `tests/test_discovery.py` | Entry-point discovery, filesystem list/fetch |
| `tests/test_http_driver.py` | Auth config, live httpbin smoke (`@pytest.mark.network`) |
| `tests/test_hardening.py` | Root boundary, gitignore, traversal guards |
| `tests/test_cli_convert.py` | End-to-end convert, S3 mock dispatch |

Run all tests:

```bash
pytest
pytest -m 'not network'   # skip live HTTP smoke
```