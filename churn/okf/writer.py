"""Minimal OKF v0.1 bundle writer.

Produces directories of markdown with required frontmatter + index.md.

Designed to be compatible with:
- Google OKF SPEC v0.1
- ekg sibling doctree consumption (frontmatter + links + sections)
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def make_frontmatter(
    *,
    type: str,
    title: str | None = None,
    description: str | None = None,
    tags: list[str] | None = None,
    resource: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    fm: dict[str, Any] = {"type": type}
    if title:
        fm["title"] = title
    if description:
        fm["description"] = description
    if tags:
        fm["tags"] = tags
    if resource:
        fm["resource"] = resource
    fm["timestamp"] = datetime.now(timezone.utc).isoformat()
    fm.update(extra)
    return fm


def _safe_bundle_path(bundle_root: Path, rel_path: str) -> Path:
    """Resolve rel_path under bundle_root; reject path traversal."""
    rel = rel_path.replace("\\", "/").lstrip("/")
    if ".." in Path(rel).parts:
        raise ValueError(f"Unsafe concept path (path traversal): {rel_path!r}")
    full = (bundle_root / rel).resolve()
    root = bundle_root.resolve()
    if not full.is_relative_to(root):
        raise ValueError(f"Concept path escapes bundle root: {rel_path!r}")
    return full


def write_concept(
    bundle_root: Path,
    rel_path: str,
    frontmatter: dict[str, Any],
    body: str,
) -> Path:
    """Write a single concept markdown file with proper frontmatter."""
    full = _safe_bundle_path(bundle_root, rel_path)
    full.parent.mkdir(parents=True, exist_ok=True)

    with full.open("w", encoding="utf-8") as f:
        f.write("---\n")
        yaml.safe_dump(frontmatter, f, sort_keys=False, allow_unicode=True)
        f.write("---\n\n")
        f.write(body.strip() + "\n")
    return full


def write_index(bundle_root: Path, entries: list[dict[str, str]]) -> Path:
    """Write index.md supporting simple section grouping for subdirs (progressive disclosure).

    Per OKF SPEC §6 and ekg examples: uses headings for groups + * links with descriptions.
    Entries may be flat or pre-grouped; auto-groups by top-level dir.
    """
    bundle_root.mkdir(parents=True, exist_ok=True)
    idx = bundle_root / "index.md"
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for e in entries:
        path = e.get("path", "") or ""
        # top-level group: "" for root files, "subdir" for sub/...
        if "/" in path:
            group = path.split("/", 1)[0]
        else:
            group = ""
        groups[group].append(e)

    lines: list[str] = ["# Index\n"]

    # root entries first (no heading or under implicit root)
    root_entries = groups.get("", [])
    for e in root_entries:
        title = e.get("title") or e.get("path", "")
        desc = e.get("description", "")
        link = e.get("path", "")
        lines.append(f"* [{title}]({link}) — {desc}")
    if root_entries:
        lines.append("")

    # subdir groups, sorted for determinism
    for g in sorted(k for k in groups if k):
        lines.append(f"## {g}\n")
        for e in groups[g]:
            title = e.get("title") or e.get("path", "")
            desc = e.get("description", "")
            link = e.get("path", "")
            lines.append(f"* [{title}]({link}) — {desc}")
        lines.append("")

    idx.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return idx


def compute_manifest(bundle_root: Path) -> dict[str, Any]:
    """Very small manifest for future SHA validation (M002)."""
    files = {}
    for p in sorted(bundle_root.rglob("*.md")):
        if p.name in {"index.md", "log.md"}:
            continue
        data = p.read_bytes()
        files[str(p.relative_to(bundle_root))] = {
            "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files": files,
    }


def write_folder_frontmatter(
    bundle_root: Path,
    rel_dir: str,
    *,
    title: str | None = None,
    type: str = "category",
    description: str | None = None,
    semantic_tags: list[str] | None = None,
    **extra: Any,
) -> Path:
    """Write ekg-style frontmatter.yaml (plain YAML, no ---) for a folder.

    See ../ekg/docs/OKF-FORMAT.md and ekg ere/folders.
    Robust for root: accepts "", ".", or "subdir".
    """
    rel = (rel_dir or "").strip().rstrip("/")
    if rel in ("", "."):
        d = bundle_root
    else:
        d = bundle_root / rel
    d.mkdir(parents=True, exist_ok=True)
    fm: dict[str, Any] = {"type": type}
    if title:
        fm["title"] = title
    if description:
        fm["description"] = description
    if semantic_tags:
        fm["semantic_tags"] = semantic_tags
    fm.update(extra)
    target = d / "frontmatter.yaml"
    target.write_text(yaml.safe_dump(fm, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return target


def ensure_static_dir(bundle_root: Path) -> Path:
    """Ensure _static/ dir for assets (ekg/OKF fidelity, per ../ekg and SPEC).
    Callers can copy images here and reference as ![alt](_static/foo.png).
    """
    static = bundle_root / "_static"
    static.mkdir(parents=True, exist_ok=True)
    return static


def append_log_entry(bundle_root: Path, message: str, entry_type: str = "Update") -> Path:
    """Append a simple entry to log.md (M004 stub).

    Format per OKF SPEC §7: date grouped, **Type** message.
    Creates log.md if missing (no frontmatter).
    """
    log = bundle_root / "log.md"
    bundle_root.mkdir(parents=True, exist_ok=True)
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    line = f"* **{entry_type}**: {message}\n"
    if log.exists():
        content = log.read_text(encoding="utf-8")
        if f"## {date}" in content:
            # append to today's section
            content = content.rstrip() + "\n" + line
        else:
            content = content.rstrip() + f"\n\n## {date}\n" + line
        log.write_text(content, encoding="utf-8")
    else:
        content = f"# Directory Update Log\n\n## {date}\n{line}"
        log.write_text(content, encoding="utf-8")
    return log


def make_index_entry(
    rel_path: str,
    frontmatter: dict[str, Any] | None = None,
    body: str | None = None,
) -> dict[str, str]:
    """Small helper: generate index entry preferring frontmatter title/description (per OKF recs + ekg).

    Falls back to path stem for title; optional first body para for desc.
    Used by convert for richer index.md entries.
    """
    fm = frontmatter or {}
    title = fm.get("title") or Path(rel_path).stem.replace("_", " ").title()
    desc = fm.get("description") or ""
    if not desc and body:
        for line in body.splitlines():
            s = line.strip()
            if s and not s.startswith("#"):
                desc = s[:120]
                break
    return {"title": str(title), "path": rel_path, "description": desc}


def _parse_frontmatter(text: str) -> dict[str, Any] | None:
    """Parse leading YAML frontmatter (--- ... ---) using yaml.safe_load.
    Matches ekg parser style (leading --- only, tolerant).
    Returns dict or None if absent/malformed.
    """
    if not text:
        return None
    stripped = text.lstrip()
    if not stripped.startswith("---"):
        return None
    lines = text.splitlines(keepends=True)
    end_idx = None
    for i in range(1, min(200, len(lines))):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        return None
    fm_block = "".join(lines[1:end_idx])
    try:
        data = yaml.safe_load(fm_block)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def validate_bundle(bundle_root: Path) -> dict[str, Any]:
    """Simple OKF v0.1 + ekg conformance validator.

    Checks (SPEC §9 core):
    - Every non-reserved *.md has parseable leading --- frontmatter with non-empty `type`.
    - Reserved (index.md, log.md) MUST NOT have leading frontmatter.
    Returns report: {'ok': bool, 'errors': list[str], 'concepts': int, 'has_index': bool, 'root_frontmatter': bool, ...}
    Does not fail hard; for use in CLI preview/validate and smokes.
    """
    errors: list[str] = []
    concepts = 0
    has_index = (bundle_root / "index.md").exists()
    root_fm = (bundle_root / "frontmatter.yaml").exists()

    root_resolved = bundle_root.resolve()
    for md in sorted(bundle_root.rglob("*.md")):
        md_resolved = md.resolve()
        if not md_resolved.is_relative_to(root_resolved):
            continue
        rel = str(md_resolved.relative_to(root_resolved)).replace("\\", "/")
        if md.name in {"index.md", "log.md"}:
            txt = md.read_text(encoding="utf-8", errors="replace")
            if txt.lstrip().startswith("---"):
                errors.append(f"{rel}: reserved file must not start with frontmatter (OKF §6/7)")
            continue

        txt = md.read_text(encoding="utf-8", errors="replace")
        fm = _parse_frontmatter(txt)
        if fm is None:
            errors.append(f"{rel}: missing or unparseable leading frontmatter block (OKF §4.1)")
            continue
        t = fm.get("type")
        if not t or not str(t).strip():
            errors.append(f"{rel}: frontmatter missing non-empty 'type:' (Google OKF SPEC required; ekg parser tolerant but recommend fix)")
            continue
        concepts += 1

    if concepts > 0 and not has_index:
        errors.append("missing index.md (recommended when concepts are present; OKF §6)")

    ok = len(errors) == 0
    return {
        "ok": ok,
        "errors": errors,
        "concepts": concepts,
        "has_index": has_index,
        "root_frontmatter": root_fm,
        "bundle_root": str(bundle_root),
    }
