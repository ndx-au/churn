# OKF & EKG Compatibility

churn produces **Google Open Knowledge Format (OKF) v0.1** bundles designed for direct consumption by the sibling **ekg** project (source at `../ekg` relative to the churn repo).

## OKF bundle structure

An OKF directory is a folder of Markdown files with YAML frontmatter. churn emits:

| File / directory | OKF role | churn behavior |
|------------------|----------|----------------|
| `*.md` (concepts) | Knowledge units | Required `type:` in frontmatter; body is Markdown |
| `index.md` | Directory index (§6) | Grouped bullet links with descriptions |
| `log.md` | Update log (§7) | Append-only creation/update entries |
| `frontmatter.yaml` | Folder metadata | Plain YAML (no `---` fences); ekg navigation hints |
| `_static/` | Assets | Created empty; reference images as `![alt](_static/foo.png)` |

Additionally, churn writes `manifest.json` with per-concept SHA-256 hashes (future validation hook; not part of the Google spec).

### Concept frontmatter

Every concept file starts with:

```yaml
---
type: LegacyDocument          # required (OKF §4.1)
title: Human-readable title   # recommended
description: Short summary    # recommended
timestamp: 2026-06-23T12:00:00+00:00
source_path: original/path.md # churn-specific provenance
---
```

`type` values churn commonly assigns:

| Source | Typical `type` |
|--------|----------------|
| Generic text / unknown | `LegacyDocument` |
| HTML (naive or unstructured) | `HTML Document` |
| PDF | `PDF Document` |
| DOCX | `Word Document` |
| Binary fallback | `Binary` |

Extra keys from unstructured metadata appear as `meta_*` fields when available (e.g. `meta_languages`).

### index.md

Auto-generated with root entries first, then `## subdir` sections for nested concepts:

```markdown
# Index

* [Guide](docs/guide.md) — Imported from guide.md

## docs

* [API](docs/api.md) — API reference
```

### log.md

```markdown
# Directory Update Log

## 2026-06-23
* **Creation**: Converted 12 concept(s) from ./wiki/
```

### frontmatter.yaml

Per-folder plain YAML for ekg-style doctree navigation:

```yaml
type: category
title: wiki
description: Converted from wiki
semantic_tags:
  - imported
  - legacy-knowledge
```

Subdirectories that contain concepts receive their own `frontmatter.yaml` with `type: category` and a `group` semantic tag.

## Validation

```bash
churn validate ./my-bundle
```

`validate_bundle` (in `churn/okf/writer.py`) checks:

1. **Concepts** — leading `---` frontmatter parses; `type` is non-empty.
2. **Reserved files** — `index.md` and `log.md` must not start with `---`.
3. **Index presence** — when concepts exist, `index.md` is required.
4. **Symlink safety** — walks resolve within the bundle root.

This is a practical subset aligned with [Google OKF SPEC §9](https://github.com/GoogleCloudPlatform/knowledge-catalog) and ekg parser tolerance. It is not a full Google validator replacement (M004.004 strict mode is planned).

Preview also surfaces validation status:

```bash
churn preview ./my-bundle
```

## ekg integration

The ekg project lives at `../ekg` relative to churn (see [AGENTS.md](https://github.com/ndx-video/churn/blob/main/AGENTS.md)).

### Placement

Place churn output under ekg's ERE doctree:

```
ekg/
└── doctree/
    └── imported/
        └── my-bundle/     ← churn output copied here
            ├── index.md
            ├── frontmatter.yaml
            └── …
```

### What ekg expects

ekg's parser and doctree tooling generally expect:

- **Leading frontmatter** on concept `.md` files with at least `type`.
- **No frontmatter** on `index.md` and `log.md`.
- **Folder `frontmatter.yaml`** for section-friendly navigation (churn writes these at root and subdirs).
- **Markdown headings** in concept bodies for section extraction (goldmark-compatible).
- **`_static/`** for relative asset paths.

churn's writer, index grouping, and folder frontmatter were designed against ekg samples and `../ekg/docs/OKF-FORMAT.md`.

### Roundtrip workflow

```bash
# 1. Convert legacy source
churn convert ./legacy-docs/ --chunk --out ./bundles/legacy-okf

# 2. Validate before handoff
churn validate ./bundles/legacy-okf

# 3. Copy into ekg doctree
cp -r ./bundles/legacy-okf ../ekg/doctree/imported/legacy-okf

# 4. Use ekg tooling to browse, link, or further refine
```

Automated ekg roundtrip tests in churn verify that bundles parse cleanly against ekg expectations (see `.progress` entries G000011, G000012).

## Chunking and concept boundaries

With `--chunk`, churn splits large documents into multiple concepts:

- Markdown / text: split on top-level `# ` headings.
- PDF / DOCX / HTML (with `[parse]`): split on unstructured Title/Heading elements.
- Overflow: merges excess chunks when over `max_chunks` (default 20).

Chunk filenames: `doc-part2.md`, `subdir/guide-part3.md`. Index entries reflect each part with `(part N)` in the title.

## Manifest

`manifest.json` at bundle root:

```json
{
  "generated_at": "2026-06-23T12:00:00+00:00",
  "files": {
    "guide.md": {
      "size": 1234,
      "sha256": "abc…"
    }
  }
}
```

Reserved files (`index.md`, `log.md`) are excluded. Intended for future integrity checks (M002.006).

## Further reading

- Google OKF: [knowledge-catalog](https://github.com/GoogleCloudPlatform/knowledge-catalog)
- churn specs: [M004-OKF-RENDERING.md](https://github.com/ndx-video/churn/blob/main/specs/M004-OKF-RENDERING.md)
- ekg format notes: `../ekg/docs/OKF-FORMAT.md` (sibling repo)
- Parsing / extraction: [M003-PARSING.md](https://github.com/ndx-video/churn/blob/main/specs/M003-PARSING.md)