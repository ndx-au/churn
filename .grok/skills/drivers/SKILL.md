---
name: drivers
description: "Implement and harden CHURN source drivers (filesystem, HTTP, S3, plugins). Use for M002 slices, driver security, fetch resilience, entry-point plugins, smoke tests with real FS/curl/S3, driver bug fixes, and re-work on churn.drivers. Always use when adding or fixing drivers, list/fetch behavior, or driver:query CLI dispatch."
when-to-use: "Filesystem/HTTP/S3 driver work, plugin entry points, driver security boundaries, boto3/httpx integration, driver smoke tests, or fixing fetch/list bugs in the churn package."
---

# Drivers Skill

Implements `SourceDriver` plugins under `churn/drivers/` and wires them into the CLI (`churn convert`, `churn drivers list`).

## Architecture

- ABC: `churn/drivers/base.py` (`SourceItem`, `FetchedContent`, `SourceDriver`)
- Discovery: `churn/drivers/__init__.py` entry points + built-ins (built-ins cannot be overridden)
- CLI dispatch: `churn/cli.py` `_resolve_driver_and_query` handles paths, URLs, `s3://`, and `driver:query`

## Driver Checklist

| Driver | Key behaviors |
|--------|-----------------|
| **filesystem** | Root boundary on list+fetch; skip VCS/cache dirs; respect `.gitignore`; max file size |
| **http** | Streaming fetch + size cap; retry 5xx/429; basic auth via config or URL credentials (stripped by CLI) |
| **s3** | boto3 optional extra; anonymous mode for public buckets; URI validation; surfaced init errors |

## Security Principles

- Never read/fetch outside configured root (filesystem)
- Reject path traversal in OKF output paths (writer, not driver)
- Strip credentials from URLs before logging or writing metadata
- Cap response/object sizes

## Testing

- Unit: `tests/test_discovery.py`, `tests/test_hardening.py`, `tests/test_http_driver.py`
- CLI integration: `tests/test_cli_convert.py` (filesystem, S3 mock)
- Network smoke: `@pytest.mark.network` for httpbin (optional in CI)

## DotProgress

After driver slices or fixes, append `.progress/milestone/M002.*` or `.progress/fixes/F*.md` per [.progress/README.md](../../../.progress/README.md).