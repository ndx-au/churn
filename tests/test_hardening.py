"""Tests for security hardening and edge-case fixes."""

from pathlib import Path

import pytest

from churn.drivers.base import SourceItem
from churn.drivers.filesystem import FileSystemDriver
from churn.okf import make_frontmatter, validate_bundle, write_concept


def test_filesystem_rejects_path_outside_root(tmp_path: Path):
    root = tmp_path / "root"
    outside = tmp_path / "outside.txt"
    root.mkdir()
    outside.write_text("secret", encoding="utf-8")

    driver = FileSystemDriver({"root": str(root)})
    item = SourceItem(id="outside.txt", path_or_uri=str(outside.resolve()))
    with pytest.raises(ValueError, match="outside driver root"):
        driver.fetch_item(item)


def test_filesystem_skips_git_dir(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("git", encoding="utf-8")
    (tmp_path / "visible.md").write_text("# Hi", encoding="utf-8")

    driver = FileSystemDriver({"root": str(tmp_path)})
    items = driver.list_items()
    paths = [i.path_or_uri for i in items]
    assert any("visible.md" in p for p in paths)
    assert not any(".git" in p for p in paths)


def test_write_concept_rejects_traversal(tmp_path: Path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    with pytest.raises(ValueError, match="path traversal"):
        write_concept(bundle, "../escape.md", make_frontmatter(type="X"), "body")


def test_validate_missing_index_is_error(tmp_path: Path):
    bundle = tmp_path / "okf"
    write_concept(bundle, "only.md", make_frontmatter(type="Note"), "# Note")
    report = validate_bundle(bundle)
    assert report["ok"] is False
    assert any("index.md" in e for e in report["errors"])


def test_chunk_by_headings_merges_overflow():
    from churn.extract import chunk_by_headings

    body = "\n".join(f"# H{i}\nbody{i}" for i in range(5))
    chunks = chunk_by_headings(body, max_chunks=2)
    assert len(chunks) == 2
    assert "H4" in chunks[-1]