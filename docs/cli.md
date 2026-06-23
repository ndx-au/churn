# CLI Reference

`churn` is a [Typer](https://typer.tiangolo.com/) + [Rich](https://rich.readthedocs.io/) command-line interface.

```bash
churn --help
churn convert --help
churn drivers --help
```

## Global options

| Option | Description |
|--------|-------------|
| `--version` | Print version (`churn 0.1.0`) and exit |
| `--help` | Show help for the current command |

Invoking `churn` with no subcommand prints top-level help.

---

## `churn convert`

Convert a source into an OKF bundle.

```bash
churn convert SOURCE [OPTIONS]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `SOURCE` | Local path, URL, `s3://` URI, or `driver:query` (see [Source formats](#source-formats)) |

### Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--out` | `-o` | `out-okf` | Output bundle directory (created if missing) |
| `--chunk` | | `false` | Split multi-section documents into separate concepts |
| `--limit` | | `100` | Maximum items to convert; `0` disables the cap |
| `--s3-anonymous` | | `false` | Force anonymous (unsigned) S3 access |
| `--unstructured-languages` | | `eng` | Comma-separated language codes for unstructured extractors |

### Behavior

1. Resolves `SOURCE` to a driver + query (see below).
2. Connects, lists items, applies `--limit`.
3. Fetches each item, extracts/normalizes to Markdown, writes concept `.md` files.
4. Writes `index.md`, `log.md`, root/subdir `frontmatter.yaml`, `_static/`, `manifest.json`.
5. Prints a Rich summary panel (path, concept count, truncation/failure notes).

**Exit codes:** `0` on success; `1` when source missing, no items found, all items failed, or unhandled error.

**Progress:** Rich spinner + bar during fetch/convert.

**Chunking:** With `--chunk`, documents are split on top-level `# ` headings (or unstructured element boundaries for PDF/DOCX/HTML when `[parse]` is installed). Additional parts are named `{stem}-part2.md`, etc., preserving subdirectory structure.

**HTTP concept IDs:** URLs produce stable filenames like `page-a1b2c3d4e5.md` (stem + SHA-256 prefix) to avoid collisions.

**Filesystem concept IDs:** Relative paths from the driver root, e.g. `docs/guide.md`.

### Source formats

| Format | Example | Driver |
|--------|---------|--------|
| Local file | `notes.md`, `C:\docs\file.txt` | filesystem |
| Local directory | `./wiki/`, `filesystem:./wiki/` | filesystem |
| HTTP(S) URL | `https://example.com/page` | http |
| HTTP with auth | `https://user:pass@host/path` | http (credentials stripped from URL) |
| S3 URI | `s3://bucket/key` or `s3://bucket/prefix/` | s3 |
| Driver query | `http:https://…`, `s3:bucket/prefix`, `filesystem:./path` | named driver |

**Windows paths:** `C:\foo` is treated as a filesystem path, not `driver:query` (drive letter guard).

**S3 credentials:** Read from `CHURN_S3_*` environment variables or `.env`. Anonymous when `--s3-anonymous` is set or when `CHURN_S3_ACCESS_KEY_ID` is unset.

### Examples

```bash
churn convert ./notes/ --out ./okf-bundle
churn convert large.md --chunk -o ./chunked
churn convert https://example.com/doc --out ./web-okf
churn convert s3://public-bucket/docs/ --s3-anonymous --limit 0 -o ./s3-okf
churn convert report.pdf --unstructured-languages eng -o ./pdf-okf
```

---

## `churn validate`

OKF v0.1 conformance check on an existing bundle.

```bash
churn validate BUNDLE_PATH
```

### Checks

- Every concept `*.md` (excluding `index.md`, `log.md`) has parseable leading `---` YAML frontmatter with non-empty `type:`.
- `index.md` and `log.md` must **not** start with frontmatter.
- When concepts exist, `index.md` is required (OKF §6 recommendation).

**Exit codes:** `0` if conformant; `1` with error list if not.

```bash
churn validate ./my-bundle
# OK — 12 concepts conformant. has_index=True root_fm=True
```

---

## `churn preview`

Quick inspection of a bundle without leaving the terminal.

```bash
churn preview BUNDLE_PATH
```

Shows:

- Bundle path and `index.md` presence (first ~1200 chars of index)
- Up to five sample concept paths
- Validation summary (`validate_bundle` report)
- Approximate heading count and `frontmatter.yaml` folder count
- Subdirectory listing (first five)
- Tail of `log.md` if present

---

## `churn log`

Print full `log.md` contents.

```bash
churn log BUNDLE_PATH
```

---

## `churn drivers list`

List all drivers discovered via the `churn.drivers` entry-point group plus built-ins.

```bash
churn drivers list
```

Output is a Rich table: **Name**, **Description**, **Class** (module path).

Built-in drivers: `filesystem`, `http`, `s3` (when boto3 is available). External plugins appear after `pip install` of packages that register entry points. Built-in names cannot be overridden.

---

## `churn drivers`

Parent command for driver management. With no subcommand, prints a hint to run `churn drivers list`.

---

## Environment variables

All use the `CHURN_` prefix (loaded from environment and optional `.env` via pydantic-settings).

| Variable | Used by | Description |
|----------|---------|-------------|
| `CHURN_LOG_LEVEL` | Core | Logging level (default `INFO`) |
| `CHURN_HTTP_TIMEOUT` | HTTP driver config | Request timeout seconds (default `30`) |
| `CHURN_S3_REGION` | S3 driver / CLI | AWS or compatible region |
| `CHURN_S3_ENDPOINT` | S3 driver / CLI | Custom endpoint (e.g. Backblaze B2) |
| `CHURN_S3_ACCESS_KEY_ID` | S3 driver / CLI | Access key; absence triggers anonymous mode |
| `CHURN_S3_SECRET_ACCESS_KEY` | S3 driver / CLI | Secret key |

---

## Output bundle layout

After `churn convert`, expect:

```
my-bundle/
├── index.md
├── log.md
├── frontmatter.yaml
├── manifest.json
├── _static/
├── concept-a.md
├── concept-b.md
└── subdir/
    ├── frontmatter.yaml
    └── nested.md
```

Each concept file:

```markdown
---
type: LegacyDocument
title: My Concept
description: Imported from source
timestamp: 2026-06-23T12:00:00+00:00
source_path: relative/path.md
---

# My Concept

Body content…
```

See [OKF & EKG](okf-ekg.md) for field semantics and ekg consumption notes.