# Quickstart

Get from zero to a validated OKF bundle in a few minutes.

## 1. Install

```bash
git clone <your-churn-repo>
cd churn

# Minimum: CLI + built-in drivers (filesystem, HTTP; S3 needs boto3)
pip install -e .

# Recommended for real-world use
pip install -e '.[parse,s3,dev]'
```

| Extra | Adds | When you need it |
|-------|------|------------------|
| `parse` | `unstructured[pdf,docx]` | PDF, DOCX, rich HTML extraction |
| `s3` | `boto3` | `s3://` sources (AWS, Backblaze B2, MinIO, etc.) |
| `dev` | `pytest`, `ruff`, `mypy` | Contributing or CI |

Verify:

```bash
churn --version          # churn 0.1.0
churn drivers list       # filesystem, http, s3 (if boto3 installed)
pytest                   # 40 tests (network smoke optional)
```

## 2. Convert local files

**Single file:**

```bash
churn convert notes/meeting.md --out ./bundles/meeting-okf
```

**Directory tree:**

```bash
churn convert ./legacy-wiki/ --out ./bundles/wiki-okf
```

The filesystem driver walks recursively, skips VCS/cache directories (`.git`, `node_modules`, `.venv`, …), and respects the root `.gitignore`.

**Multi-section documents** — split on `# ` headings into separate concepts:

```bash
churn convert long-guide.md --chunk --out ./bundles/guide-okf
```

Chunked output uses `-part2`, `-part3` suffixes in concept filenames.

## 3. Convert from the web

```bash
# Direct URL (auto-selects HTTP driver)
churn convert https://example.com/docs/page.html --out ./bundles/web-okf

# Explicit driver:query form
churn convert http:https://httpbin.org/json --out ./bundles/json-okf
```

**HTTP basic auth** — embed credentials in the URL; churn strips them before logging and passes them to the driver:

```bash
churn convert https://user:pass@internal.example.com/api/doc --out ./bundles/secure-okf
```

## 4. Convert from S3 / Backblaze B2

Create a `.env` file (optional) for private buckets or custom endpoints:

```env
CHURN_S3_ENDPOINT=https://s3.us-west-004.backblazeb2.com
CHURN_S3_REGION=us-west-004
CHURN_S3_ACCESS_KEY_ID=your-key
CHURN_S3_SECRET_ACCESS_KEY=your-secret
```

**Public bucket** (anonymous access):

```bash
churn convert s3://my-public-bucket/path/to/doc.md \
  --out ./bundles/s3-okf \
  --s3-anonymous
```

**Private bucket** — omit `--s3-anonymous` and set `CHURN_S3_ACCESS_KEY_ID` / `CHURN_S3_SECRET_ACCESS_KEY`. If no credentials are configured, churn defaults to anonymous mode.

**Prefix listing** — use `s3://bucket/prefix/` to convert all objects under a prefix (subject to `--limit`).

## 5. Rich PDF / DOCX extraction

Install the parse extra, then convert as usual:

```bash
pip install -e '.[parse]'
churn convert report.pdf --out ./bundles/report-okf
churn convert manual.docx --chunk --out ./bundles/manual-okf
```

Without `[parse]`, PDF/DOCX produce a stub concept noting that full extraction requires the extra.

Tune unstructured language hints:

```bash
churn convert report.pdf --unstructured-languages eng,deu --out ./bundles/report-okf
```

## 6. Validate and preview

```bash
churn validate ./bundles/wiki-okf
churn preview ./bundles/wiki-okf
churn log ./bundles/wiki-okf
```

`validate` checks OKF v0.1 conformance (frontmatter `type:` on concepts, no frontmatter on `index.md`/`log.md`, `index.md` present when concepts exist).

`preview` shows index excerpt, sample concepts, validation summary, heading counts, and recent log entries.

## 7. Use with ekg

Copy or symlink the bundle into the sibling ekg project's doctree:

```bash
# From churn repo root; ekg is ../ekg per AGENTS.md
cp -r ./bundles/wiki-okf ../ekg/doctree/imported/wiki-okf
```

See [OKF & EKG](okf-ekg.md) for layout and frontmatter expectations.

## Common options

| Flag | Default | Description |
|------|---------|-------------|
| `--out`, `-o` | `out-okf` | Output bundle directory |
| `--chunk` | off | Split multi-heading docs into multiple concepts |
| `--limit` | `100` | Max items to convert (`0` = no limit) |
| `--s3-anonymous` | off | Force unsigned S3 access |
| `--unstructured-languages` | `eng` | Comma-separated languages for unstructured |

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `No items found` | Empty source, gitignored paths, or bad S3 prefix | Check path; inspect `.gitignore`; verify bucket/prefix |
| `S3 driver unavailable` | boto3 not installed | `pip install -e '.[s3]'` |
| Stub PDF body | `[parse]` not installed | `pip install -e '.[parse]'` |
| `Validation errors: missing index.md` | Empty or partial bundle | Re-run `convert`; ensure at least one concept succeeded |
| Truncated output | Default `--limit 100` | Pass `--limit 0` for full tree |

## Next steps

- Full command reference: [CLI Reference](cli.md)
- Driver details and plugins: [Drivers](drivers.md)
- Bundle spec and ekg notes: [OKF & EKG](okf-ekg.md)