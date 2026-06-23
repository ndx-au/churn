"""Tests for CLI helper utilities (e.g. frontmatter stripping)."""

from churn.cli import _strip_leading_frontmatter


def test_strip_leading_frontmatter_basic():
    raw = """---
type: Foo
---

# Title

Body.
"""
    out = _strip_leading_frontmatter(raw)
    assert out.strip().startswith("# Title")
    assert "type: Foo" not in out


def test_strip_no_frontmatter():
    raw = "# Just a heading\n\nContent."
    assert _strip_leading_frontmatter(raw) == raw


def test_strip_malformed():
    raw = "---\nno closing\n# Title"
    # Should return original or safe content
    out = _strip_leading_frontmatter(raw)
    assert "# Title" in out or out == raw
