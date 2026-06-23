"""Tests for OKF bundle writer."""

from pathlib import Path

from churn.okf import (
    make_frontmatter,
    make_index_entry,
    validate_bundle,
    write_concept,
    write_folder_frontmatter,
    write_index,
)


def test_write_minimal_bundle(tmp_path: Path):
    bundle = tmp_path / "bundle"
    fm = make_frontmatter(type="TestDoc", title="Test")
    p = write_concept(bundle, "concepts/test.md", fm, "# Test\n\nBody here.")
    assert p.exists()

    idx = write_index(bundle, [{"title": "Test", "path": "concepts/test.md"}])
    assert idx.exists()
    assert "Test" in idx.read_text(encoding="utf-8")


def test_make_index_entry_prefers_fm(tmp_path: Path):
    entry = make_index_entry(
        "docs/guide.md",
        frontmatter={"title": "My Guide", "description": "How to use."},
        body="# ignore\n\nFirst para here.",
    )
    assert entry["title"] == "My Guide"
    assert entry["description"] == "How to use."
    assert entry["path"] == "docs/guide.md"


def test_make_index_entry_fallback_desc_from_body():
    entry = make_index_entry("note.md", body="# Note\n\nThis is the lead sentence for index.")
    assert entry["title"] == "Note"
    assert "lead sentence" in entry["description"]


def test_write_index_groups_subdirs(tmp_path: Path):
    bundle = tmp_path / "b"
    entries = [
        {"title": "RootOne", "path": "root1.md", "description": "r1"},
        {"title": "SubDoc", "path": "sub/doc.md", "description": "s"},
        {"title": "SubOther", "path": "sub/other.md", "description": "s2"},
    ]
    idxp = write_index(bundle, entries)
    txt = idxp.read_text(encoding="utf-8")
    assert "# Index" in txt
    assert "* [RootOne](root1.md)" in txt
    assert "## sub" in txt
    assert "* [SubDoc](sub/doc.md)" in txt
    # no fm on index
    assert not txt.lstrip().startswith("---")


def test_write_folder_frontmatter_root_and_sub(tmp_path: Path):
    bundle = tmp_path / "bundle"
    # root
    p1 = write_folder_frontmatter(
        bundle, "", title="MyBundle", type="category", semantic_tags=["imported"], description="root"
    )
    assert p1.exists()
    content1 = p1.read_text(encoding="utf-8")
    assert "semantic_tags:" in content1
    assert "type: category" in content1
    # sub
    p2 = write_folder_frontmatter(bundle, "sub/dir", title="Sub", semantic_tags=["group"])
    assert (bundle / "sub" / "dir" / "frontmatter.yaml").exists()
    assert "type: category" in p2.read_text(encoding="utf-8")


def test_validate_bundle_ok_and_errors(tmp_path: Path):
    bundle = tmp_path / "okf"
    # good concept with type
    good_fm = make_frontmatter(type="Guide", title="G")
    write_concept(bundle, "guide.md", good_fm, "# G\nBody.")
    # another good in sub
    write_concept(bundle, "sub/s.md", make_frontmatter(type="Note"), "note")
    # index (no fm)
    write_index(bundle, [{"title": "G", "path": "guide.md"}])
    # root folder fm
    write_folder_frontmatter(bundle, "", title="B")

    report = validate_bundle(bundle)
    assert report["ok"] is True
    assert report["concepts"] == 2
    assert report["has_index"] is True
    assert report["root_frontmatter"] is True
    assert len(report["errors"]) == 0

    # now break one
    bad = bundle / "bad.md"
    bad.write_text("# No frontmatter at all\n")
    report2 = validate_bundle(bundle)
    assert report2["ok"] is False
    assert any("bad.md" in e and "frontmatter" in e for e in report2["errors"])
    # concepts count is only successful parsed (bad skipped)
    assert report2["concepts"] == 2  # bad skipped

    # reserved with fm should error
    (bundle / "index.md").write_text("---\ntype: bad\n---\n# nope\n")
    report3 = validate_bundle(bundle)
    errs = report3["errors"]
    assert any("index.md" in e and "reserved" in e for e in errs)
    # at this stage bad.md and overwritten index are errors; good concepts still 2
    assert report3["concepts"] == 2
