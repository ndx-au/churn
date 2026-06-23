"""CLI integration tests for convert, validate, and drivers."""

from pathlib import Path

from typer.testing import CliRunner

from churn.cli import app

runner = CliRunner()


def test_convert_local_md(tmp_path: Path):
    src = tmp_path / "note.md"
    src.write_text("# Hello\n\nWorld content here.", encoding="utf-8")
    out = tmp_path / "bundle"
    result = runner.invoke(app, ["convert", str(src), "--out", str(out)])
    assert result.exit_code == 0, result.stdout
    assert (out / "note.md").exists()
    assert (out / "index.md").exists()
    assert (out / "manifest.json").exists()


def test_convert_missing_source_exits_nonzero(tmp_path: Path):
    missing = tmp_path / "does-not-exist"
    result = runner.invoke(app, ["convert", str(missing), "--out", str(tmp_path / "out")])
    assert result.exit_code == 1


def test_convert_driver_query_filesystem(tmp_path: Path):
    src = tmp_path / "doc.md"
    src.write_text("# Driver Query\n\nBody.", encoding="utf-8")
    out = tmp_path / "bundle"
    result = runner.invoke(
        app, ["convert", f"filesystem:{src}", "--out", str(out)]
    )
    assert result.exit_code == 0, result.stdout
    assert (out / "doc.md").exists()


def test_convert_chunk_preserves_sections(tmp_path: Path):
    src = tmp_path / "multi.md"
    src.write_text(
        "# One\n\nFirst.\n\n# Two\n\nSecond.\n\n# Three\n\nThird.",
        encoding="utf-8",
    )
    out = tmp_path / "bundle"
    result = runner.invoke(app, ["convert", str(src), "--out", str(out), "--chunk"])
    assert result.exit_code == 0, result.stdout
    concepts = [p for p in out.rglob("*.md") if p.name not in {"index.md", "log.md"}]
    assert len(concepts) >= 3


def test_validate_reports_errors_cleanly(tmp_path: Path):
    bundle = tmp_path / "bad"
    bundle.mkdir()
    (bundle / "broken.md").write_text("# no frontmatter\n", encoding="utf-8")
    result = runner.invoke(app, ["validate", str(bundle)])
    assert result.exit_code == 1
    assert "Validate error:" not in result.stdout


def test_drivers_group_shows_help():
    result = runner.invoke(app, ["drivers"])
    assert result.exit_code == 0
    assert "churn drivers list" in result.stdout