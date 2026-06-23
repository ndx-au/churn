"""Lightweight extraction / normalization layer (M003).

Goal: turn raw fetched bytes into clean Markdown concept body + suggested metadata.

Strategy (per research report + specs/M003-PARSING.md):
- .md / .txt / .rst → pass-through (strip leading frontmatter)
- If [parse] extra installed (unstructured[pdf,docx]), use for pdf/docx/html
  → layout-aware MD (headings/lists via element categories)
- .html (no unstructured) → improved naive strip
- pdf/docx etc (no unstructured) → stub note + suggested_type
- Always attempt better title (first H1 or first sentence) + description hint
- Return suggested_frontmatter updates (title, description, suggested_type, original_type hints)

Graceful: no hard dep on unstructured. Fallback keeps M00x working.
Follow-ups (see .progress): full chunking, concept splitter, config for unstructured, richer mapper.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def extract_to_markdown(
    data: bytes,
    *,
    mime: str | None = None,
    path_hint: str | None = None,
    max_chars: int = 8000,
    unstructured_config: dict | None = None,
) -> tuple[str, dict[str, Any]]:
    """
    Return (markdown_body, suggested_frontmatter_updates)

    The caller (convert etc.) is still responsible for the final OKF frontmatter.
    This only helps produce a nicer body and title/desc hints.
    """
    suffix = (Path(path_hint).suffix.lower() if path_hint else "") or ""
    m = (mime or "").lower()

    # Try rich extraction via unstructured when [parse] extra present.
    # (pdf/docx/html) → layout-aware MD (headings via element cats).
    pdfish = suffix in {".pdf", ".docx", ".doc", ".html", ".htm"}
    pdfish = pdfish or "pdf" in m or "word" in m or "html" in m
    if pdfish:
        rich = _try_unstructured_to_markdown(data, path_hint, mime, max_chars, unstructured_config or {})
        if rich is not None:
            return rich

    # Text formats (md/txt/rst): pass-through + strip fm
    if suffix in {".md", ".markdown", ".txt", ".rst"} or "text/plain" in m or "text/markdown" in m:
        text = data.decode("utf-8", errors="replace")
        body = _strip_leading_frontmatter(text)[:max_chars]
        title = _guess_title(body, path_hint)
        desc = _guess_description(body)
        hints: dict[str, Any] = {"title": title}
        if desc:
            hints["description"] = desc
        return body, hints

    if suffix in {".html", ".htm"} or "html" in m:
        # Naive fallback when unstructured not available (improved for title/desc)
        text = data.decode("utf-8", errors="replace")
        # Prefer explicit <title> or first <h1> for title (before stripping)
        tmatch = re.search(r"<title[^>]*>(.*?)</title>|<h1[^>]*>(.*?)</h1>", text, re.I | re.S)
        html_title = None
        if tmatch:
            html_title = (tmatch.group(1) or tmatch.group(2) or "").strip()[:120]
        # Drop head entirely for body content (avoids title dup)
        body_src = re.sub(r"<head[^>]*>.*?</head>", "", text, flags=re.I | re.S)
        cleaned = re.sub(r"<script[^>]*>.*?</script>", "", body_src, flags=re.I | re.S)
        cleaned = re.sub(r"<style[^>]*>.*?</style>", "", cleaned, flags=re.I | re.S)
        cleaned = re.sub(r"<[^>]+>", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        body_clean = (cleaned[:max_chars] or "imported html").strip()
        title = html_title or _guess_title(body_clean, path_hint)
        title = title or (Path(path_hint).stem if path_hint else "HTML")
        # de-dup leading title phrase in body if present
        if title:
            pat = re.escape(title)
            body_clean = re.sub(
                r"^\s*" + pat + r"\s*[\.\,\:\;\-\–\—]?\s*",
                "",
                body_clean,
                count=1,
                flags=re.I,
            ).strip()
        desc = (
            _guess_description("# " + title + "\n\n" + body_clean)
            or _guess_description(body_clean)
            or "Imported HTML document."
        )
        body = f"# {title}\n\n{body_clean}" if body_clean else f"# {title}"
        return body, {"title": title, "description": desc, "suggested_type": "HTML Document", "original_type": "HTML"}

    # PDF/DOCX fallback when no unstructured
    if suffix in {".pdf", ".docx", ".doc"}:
        stem = Path(path_hint).stem if path_hint else "Document"
        suggested_type = "PDF Document" if suffix == ".pdf" else "Word Document"
        stub = "( binary content — full extraction requires [parse] + unstructured )"
        body = f"# {stem}\n\n{stub}"
        hints = {
            "title": stem,
            "suggested_type": suggested_type,
            "original_type": suggested_type,
        }
        return body, hints

    # Unknown / binary-ish
    text = data.decode("utf-8", errors="replace")
    preview = text[:500].replace("\x00", "�")
    stem = Path(path_hint).stem if path_hint else "Binary"
    body = f"# {stem}\n\n```\n{preview}\n``` (truncated)"
    return body, {"suggested_type": "Binary"}


def extract_to_markdown_and_chunks(
    data: bytes,
    *,
    mime: str | None = None,
    path_hint: str | None = None,
    max_chars: int = 8000,
    unstructured_config: dict | None = None,
    chunk: bool = False,
) -> tuple[list[str], dict[str, Any]]:
    """M003 deeper wire: return (list_of_chunk_bodies, hints).

    Always >=1 chunk. When chunk=True + [parse] rich source, uses unstructured elements
    for chunk_by_unstructured_elements (headings/titles as delimiters). Falls back to heading chunker.
    Hints from overall/first. Per-chunk fm titles handled by caller (cli).
    """
    if not chunk:
        body, hints = extract_to_markdown(
            data,
            mime=mime,
            path_hint=path_hint,
            max_chars=max_chars,
            unstructured_config=unstructured_config,
        )
        return [body], hints

    # Chunk before per-chunk truncation so multi-section docs are not cut early.
    body, hints = extract_to_markdown(
        data,
        mime=mime,
        path_hint=path_hint,
        max_chars=max(500_000, max_chars * 20),
        unstructured_config=unstructured_config,
    )

    # wire elements chunk for parse paths
    suffix = (Path(path_hint).suffix.lower() if path_hint else "") or ""
    mlow = (mime or "").lower()
    pdfish = suffix in {".pdf", ".docx", ".doc", ".html", ".htm"} or "pdf" in mlow or "word" in mlow or "html" in mlow
    if pdfish:
        try:
            import io
            buf = io.BytesIO(data)
            filename = path_hint or "document"
            if suffix == ".pdf" or "pdf" in mlow:
                from unstructured.partition.pdf import partition_pdf
                els = partition_pdf(file=buf, file_filename=filename, include_page_breaks=False, **(unstructured_config or {}))
            elif suffix in {".docx", ".doc"} or "word" in mlow:
                from unstructured.partition.docx import partition_docx
                els = partition_docx(file=buf, file_filename=filename, **(unstructured_config or {}))
            elif suffix in {".html", ".htm"} or "html" in mlow:
                from unstructured.partition.html import partition_html
                els = partition_html(file=buf, file_filename=filename, **(unstructured_config or {}))
            else:
                from unstructured.partition.auto import partition
                els = partition(file=buf, file_filename=filename, include_page_breaks=False, **(unstructured_config or {}))
            chs = chunk_by_unstructured_elements(els)
            if chs:
                return [_truncate_chunk(c, max_chars) for c in chs], hints
        except Exception:
            pass
    # fallback
    chs = chunk_by_headings(body)
    return [_truncate_chunk(c, max_chars) for c in chs], hints


def _truncate_chunk(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "…"


def chunk_by_headings(body: str, max_chunks: int = 20) -> list[str]:
    """Basic heading-based chunker (M003.004).

    Splits body on top-level (# ) headings. Returns list of chunks (each starting with its heading).
    If no headings or few, returns [body] (single concept).
    """
    lines = body.splitlines(keepends=True)
    chunks: list[str] = []
    current: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# ") and current:
            chunks.append("".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        chunks.append("".join(current))
    if not chunks:
        chunks = [body]
    if len(chunks) > max_chunks:
        merged = chunks[: max_chunks - 1]
        merged.append("".join(chunks[max_chunks - 1 :]))
        return merged
    return chunks


def chunk_by_unstructured_elements(elements: list, max_chunks: int = 20) -> list[str]:
    """Deeper M003.004: chunk directly from unstructured elements (wired when [parse] active).

    Splits on Title/Heading/Header categories as natural concept boundaries.
    Falls back gracefully if no elements. Produces chunks preserving layout (lists/tables etc).
    Per-chunk bodies start with appropriate # or ## .
    """
    if not elements:
        return []
    chunks: list[str] = []
    current: list[str] = []
    for el in elements:
        text = (getattr(el, "text", None) or str(el)).strip()
        if not text:
            continue
        category = getattr(el, "category", "NarrativeText") or "NarrativeText"
        if category in ("Title", "Heading", "Header") and current:
            chunks.append("\n\n".join(current))
            if category == "Title":
                current = [f"# {text}"]
            else:
                current = [f"## {text}"]
        elif category in ("Title", "Heading", "Header"):
            current = [f"# {text}" if category == "Title" else f"## {text}"]
        else:
            current.append(text)
    if current:
        chunks.append("\n\n".join(current))
    if not chunks:
        all_text = "\n\n".join(
            (getattr(el, "text", str(el)) or "")
            for el in elements
            if (getattr(el, "text", None) or str(el)).strip()
        )
        return [all_text[:8000]] if all_text else []
    if len(chunks) > max_chunks:
        merged = chunks[: max_chunks - 1]
        merged.append("\n\n".join(chunks[max_chunks - 1 :]))
        return merged
    return chunks


def map_metadata(hints: dict[str, Any] | None, element_metadata: Any | None = None, unstructured_config: dict | None = None) -> dict[str, Any]:
    """M003.003 metadata mapper: enriches hints/fm from unstructured element.metadata + config.

    Maps common fields (languages, dates, filetype, page etc) for OKF frontmatter use.
    Callers (cli/extract) can merge into make_frontmatter extra or per-chunk.
    """
    out = dict(hints or {})
    meta = element_metadata
    if meta is not None:
        if not isinstance(meta, dict):
            meta = {k: getattr(meta, k, None) for k in ("languages", "last_modified", "filename", "page_number", "filetype", "title", "url")}
        for k, v in (meta or {}).items():
            if v and k not in out:
                # prefix to avoid clobber; consumers can promote keys like languages -> fm
                out[f"meta_{k}"] = v
    if unstructured_config:
        out["unstructured_config_used"] = bool(unstructured_config)
    return out


def _strip_leading_frontmatter(text: str) -> str:
    lines = text.splitlines(keepends=True)
    if not lines or not lines[0].strip().startswith("---"):
        return text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "".join(lines[i + 1 :]).lstrip("\n\r")
    return text


def _guess_title(body: str, path_hint: str | None) -> str | None:
    """First H1, else first non-empty sentence-ish line, else path stem."""
    # First H1
    m = re.search(r"^#\s+(.+)$", body, re.M)
    if m:
        return m.group(1).strip()[:120]
    # First sentence / first line
    for line in body.splitlines():
        s = line.strip()
        if s and not s.startswith("#") and not s.startswith("```"):
            # take first sentence
            sent = re.split(r"[.!?]\s+", s, maxsplit=1)[0].strip()
            if sent:
                return sent[:120]
            return s[:120]
    if path_hint:
        return Path(path_hint).stem.replace("_", " ").title()
    return None


def _guess_description(body: str) -> str | None:
    """Heuristic first paragraph or first sentence after title for description hint.
    Skips an initial title-like line (the one used for H1) to avoid desc==title.
    """
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    started = False
    para: list[str] = []
    skipped_first = False
    for ln in lines:
        if ln.startswith("#"):
            if started and para:
                break
            continue
        if not started:
            started = True
            # if first content line is short and title-ish, skip it for desc
            if not skipped_first and len(ln) < 80 and not re.search(r"[.!?]$", ln):
                skipped_first = True
                continue
        para.append(ln)
        if len(" ".join(para)) > 160:
            break
    if para:
        text = " ".join(para)
        # truncate to ~1 sentence-ish
        m = re.match(r"^(.{20,160}?[.!?])(\s|$)", text)
        if m:
            return m.group(1).strip()
        return text[:140].rsplit(" ", 1)[0].strip() + "…"
    return None


def _try_unstructured_to_markdown(
    data: bytes, path_hint: str | None, mime: str | None, max_chars: int, unstructured_config: dict | None = None
) -> tuple[str, dict[str, Any]] | None:
    """Attempt layout-aware extraction using unstructured (if [parse] extra installed).

    Uses specific partitioners + element categories to emit headings.
    Returns None on import or processing failure (caller falls back).
    """
    try:
        import io
    except Exception:
        return None

    try:
        buf = io.BytesIO(data)
        filename = path_hint or "document"
        suffix = (Path(path_hint).suffix.lower() if path_hint else "") or ""
        m = (mime or "").lower()

        if suffix == ".pdf" or "pdf" in m:
            from unstructured.partition.pdf import partition_pdf
            elements = partition_pdf(file=buf, file_filename=filename, include_page_breaks=False, **(unstructured_config or {}))
        elif suffix in {".docx", ".doc"} or "word" in m:
            from unstructured.partition.docx import partition_docx
            elements = partition_docx(file=buf, file_filename=filename, **(unstructured_config or {}))
        elif suffix in {".html", ".htm"} or "html" in m:
            from unstructured.partition.html import partition_html
            elements = partition_html(file=buf, file_filename=filename, **(unstructured_config or {}))
        else:
            from unstructured.partition.auto import partition
            elements = partition(file=buf, file_filename=filename, include_page_breaks=False, **(unstructured_config or {}))
    except Exception:
        return None

    try:
        md_parts: list[str] = []
        extracted_title: str | None = None
        suggested_t: str | None = None

        if suffix == ".pdf":
            suggested_t = "PDF Document"
        elif suffix in {".docx", ".doc"}:
            suggested_t = "Word Document"
        elif "html" in (mime or "").lower() or suffix in {".html", ".htm"}:
            suggested_t = "HTML Document"

        for el in elements:
            text = (getattr(el, "text", None) or str(el)).strip()
            if not text:
                continue
            category = getattr(el, "category", "NarrativeText") or "NarrativeText"

            meta = getattr(el, "metadata", None)
            if meta is not None and not extracted_title:
                mt = getattr(meta, "title", None)
                if mt and isinstance(mt, str):
                    extracted_title = mt.strip()[:120]

            if category == "Title" and not extracted_title:
                extracted_title = text[:120]
                md_parts.append(f"# {text}")
            elif category in ("Heading", "Header"):
                if not any(p.startswith("# ") for p in md_parts):
                    md_parts.append(f"# {text}")
                    if not extracted_title:
                        extracted_title = text[:120]
                else:
                    md_parts.append(f"## {text}")
            elif category == "ListItem":
                md_parts.append(f"- {text}")
            elif category == "Table":
                md_parts.append(f"```\n{text}\n```")
            else:
                md_parts.append(text)

        if not md_parts:
            if extracted_title:
                body = f"# {extracted_title}"
                hints = {"title": extracted_title}
                if suggested_t:
                    hints["suggested_type"] = suggested_t
                    hints["original_type"] = suggested_t
                hints = map_metadata(hints, None, unstructured_config)
                return body, hints
            return None

        body = "\n\n".join(md_parts)[:max_chars]
        title = extracted_title or _guess_title(body, path_hint)
        hints: dict[str, Any] = {"title": title}
        desc = _guess_description(body)
        if desc:
            hints["description"] = desc
        if suggested_t:
            hints["suggested_type"] = suggested_t
            hints["original_type"] = suggested_t
        # Wire M003.003 mapper + note elements used for chunk potential
        try:
            last_meta = getattr(elements[-1], "metadata", None) if elements else None
            hints = map_metadata(hints, last_meta, unstructured_config)
        except Exception:
            pass
        return body, hints
    except Exception:
        return None
