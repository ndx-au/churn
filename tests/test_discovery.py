"""Basic plugin/driver discovery and FS driver tests."""

from pathlib import Path

from churn.drivers import discover_drivers, get_driver
from churn.drivers.filesystem import FileSystemDriver


def test_discover_includes_filesystem():
    drivers = discover_drivers()
    assert "filesystem" in drivers
    assert drivers["filesystem"] is FileSystemDriver


def test_get_driver():
    d = get_driver("filesystem")
    assert isinstance(d, FileSystemDriver)


def test_filesystem_list_and_fetch(tmp_path: Path):
    # Create a small tree
    (tmp_path / "hello.md").write_text("# Hello\nWorld", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "note.txt").write_text("note content", encoding="utf-8")

    driver = FileSystemDriver({"root": str(tmp_path)})
    items = driver.list_items()
    assert len(items) >= 2

    # fetch one
    hello = next(i for i in items if "hello" in i.path_or_uri)
    content = driver.fetch_item(hello)
    assert b"Hello" in content.content
    assert content.sha256 is not None
