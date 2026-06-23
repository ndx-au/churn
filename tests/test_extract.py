"""Basic tests for the lightweight extractor (M003).

Covers naive paths + graceful behavior when [parse] (unstructured) not installed.
When parse extra present, richer layout tests run (see skipif).
"""

import pytest

from churn.extract import extract_to_markdown


def _has_unstructured() -> bool:
    try:
        import importlib.util

        return importlib.util.find_spec("unstructured") is not None
    except Exception:
        return False


def test_extract_markdown_passthrough():
    body, hints = extract_to_markdown(b"# Hello\n\nWorld", path_hint="note.md")
    assert "Hello" in body
    assert hints.get("title") == "Hello"


def test_extract_html_naive():
    html = b"<html><h1>Title</h1><p>Para</p></html>"
    body, _ = extract_to_markdown(html, mime="text/html", path_hint="page.html")
    assert "Title" in body or "Para" in body


def test_extract_fallback():
    body, hints = extract_to_markdown(b"\x00\x01binary", path_hint="file.bin")
    assert "Binary" in body or "binary" in body.lower()


def test_extract_pdf_stub_without_parse():
    """PDF path should give useful title + suggested_type hint (graceful with/without parse)."""
    body, hints = extract_to_markdown(
        b"%PDF-1.4 stub binary", path_hint="report.pdf", mime="application/pdf"
    )
    # When parse present, rich path may still succeed or give title; when absent stub note
    assert hints.get("title") == "report" or "report" in (hints.get("title") or "").lower()
    st = hints.get("suggested_type") or hints.get("original_type") or ""
    assert "PDF" in str(st) or "Document" in str(st) or not st


def test_extract_md_title_and_desc_hints():
    """MD passthrough gives title from H1 + description hint from body."""
    body, hints = extract_to_markdown(
        b"# My Great Report\n\nThis is the intro sentence. More text follows here for para.",
        path_hint="report.md",
    )
    assert hints.get("title") == "My Great Report"
    desc = hints.get("description")
    assert desc is not None
    assert "intro sentence" in desc or "This is" in desc


@pytest.mark.skipif(
    not _has_unstructured(),
    reason="needs [parse] extra (pip install -e '.[parse]')",
)
def test_extract_rich_with_unstructured_if_available():
    """If unstructured present, pdf/docx/html return layout MD + hints."""
    # Synthetic; when installed real partition runs. Fallback ok here.
    body, hints = extract_to_markdown(
        b"%PDF-1.4 minimal", path_hint="sample.pdf", mime="application/pdf"
    )
    # either got rich (no stub msg) or fell back (still has hints)
    if "requires the [parse]" not in body:
        assert hints.get("suggested_type") in ("PDF Document", None)
    assert hints.get("title")


def test_extract_html_naive_suggested_type():
    """Naive HTML path emits suggested_type for parity (post quality review)."""
    body, hints = extract_to_markdown(
        b"<h1>Title</h1><p>Body text here.</p>", path_hint="page.html"
    )
    assert hints.get("suggested_type") == "HTML Document"
    assert hints.get("title")


def test_chunk_before_truncate():
    """Chunking must not truncate before splitting on headings."""
    from churn.extract import extract_to_markdown_and_chunks

    sections = "\n\n".join(f"# Section {i}\n\n" + ("word " * 200) for i in range(4))
    bodies, _ = extract_to_markdown_and_chunks(
        sections.encode(),
        path_hint="big.md",
        max_chars=500,
        chunk=True,
    )
    assert len(bodies) >= 4


def test_chunk_by_headings_basic():
    """Basic chunker splits on top-level # headings only (M003.004)."""
    from churn.extract import chunk_by_headings

    body = "# H1\ntext1\n\n# H2\ntext2\n\n# H3\ntext3"
    chunks = chunk_by_headings(body)
    assert len(chunks) == 3
    assert all(c.startswith("# ") for c in chunks)
    assert "H3" in chunks[-1]


def test_chunk_by_unstructured_elements():
    """Deeper element-aware chunker (M003.004 wire with unstructured cats)."""
    from churn.extract import chunk_by_unstructured_elements
    # Simulate minimal elements (duck type)
    class El:
        def __init__(self, text, cat):
            self.text = text
            self.category = cat
            self.metadata = None
    els = [El("Main Title", "Title"), El("body one", "NarrativeText"), El("Sub Head", "Heading"), El("body two", "NarrativeText")]
    chs = chunk_by_unstructured_elements(els)
    assert len(chs) >= 1
    assert any("Main Title" in c for c in chs)


def test_map_metadata():
    """Metadata mapper enriches hints (M003.003)."""
    from churn.extract import map_metadata
    hints = {"title": "t"}
    class M: languages = ["eng"]; filename = "f.pdf"
    out = map_metadata(hints, M())
    assert out.get("title") == "t"
    assert "meta_languages" in out or "meta_filename" in out
