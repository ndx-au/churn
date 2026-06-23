"""Typer + Rich CLI for CHURN.

Current minimal commands for M001:
  churn --version
  churn drivers list
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table

from churn import __version__
from churn.drivers import discover_drivers, get_driver

app = typer.Typer(
    name="churn",
    help="CHURN — Harvest → Unify → Refine → Normalize. Legacy knowledge to OKF.",
    add_completion=False,
)
console = Console()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option("--version", help="Show version and exit.")
    ] = False,
) -> None:
    if version:
        console.print(f"churn {__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


drivers_app = typer.Typer(help="Manage source drivers (plugins)")


@drivers_app.callback(invoke_without_command=True)
def drivers_group(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        console.print("Use 'churn drivers list' to see available drivers.")
        console.print("Drivers are discovered via the 'churn.drivers' entry point group.")


@drivers_app.command("list")
def drivers_list() -> None:
    """List all discovered drivers."""
    drivers = discover_drivers()
    table = Table(title="Discovered Drivers (entry point: churn.drivers)")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Description", style="green")
    table.add_column("Class", style="dim")

    for name, driver_cls in drivers.items():
        table.add_row(
            name,
            getattr(driver_cls, "description", "(no description)"),
            f"{driver_cls.__module__}.{driver_cls.__name__}",
        )

    console.print(table)
    if not drivers:
        console.print("[yellow]No drivers registered yet.[/]")


app.add_typer(drivers_app, name="drivers")


def _parse_driver_query(source: str) -> tuple[str, str] | None:
    """Parse `driver:query` when query is not a Windows drive path."""
    if "://" in source:
        return None
    if len(source) >= 2 and source[1] == ":" and source[0].isalpha():
        return None
    if ":" not in source:
        return None
    name, query = source.split(":", 1)
    if name in discover_drivers():
        return name, query
    return None


def _resolve_driver_and_query(
    source: str,
    *,
    s3_anonymous: bool,
) -> tuple[Any, str, Path | None]:
    """Return (driver, query, optional filesystem root for relative concept ids)."""
    from churn.config import settings

    parsed = _parse_driver_query(source)
    if parsed:
        driver_name, query = parsed
        if driver_name == "filesystem":
            qpath = Path(query).resolve()
            root = qpath if qpath.is_dir() else qpath.parent
            return get_driver("filesystem", {"root": str(root)}), str(qpath), root
        return get_driver(driver_name), query, None

    if source.startswith(("http://", "https://")):
        return get_driver("http"), source, None

    if source.startswith(("s3://", "s3:")):
        s3_config: dict[str, Any] = {}
        if settings.s3_endpoint:
            s3_config["endpoint_url"] = settings.s3_endpoint
        if settings.s3_region:
            s3_config["region"] = settings.s3_region
        if s3_anonymous or not settings.s3_access_key_id:
            s3_config["anonymous"] = True
        else:
            s3_config["aws_access_key_id"] = settings.s3_access_key_id
            if settings.s3_secret_access_key:
                s3_config["aws_secret_access_key"] = settings.s3_secret_access_key
        query = source.replace("s3://", "", 1).replace("s3:", "", 1)
        return get_driver("s3", s3_config), query, None

    src_path = Path(source).resolve()
    if not src_path.exists():
        raise FileNotFoundError(f"Source not found: {source}")
    root = src_path if src_path.is_dir() else src_path.parent
    query = str(src_path) if src_path.is_file() else source
    return get_driver("filesystem", {"root": str(root)}), query, root


def _http_concept_id(url: str) -> str:
    """Unique, stable concept filename for HTTP sources."""
    parsed_name = Path(url.rstrip("/")).name or "concept"
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(parsed_name).stem).strip("-") or "concept"
    digest = hashlib.sha256(url.encode()).hexdigest()[:10]
    return f"{stem}-{digest}.md"


@app.command()
def convert(
    source: Annotated[str, typer.Argument(help="Source path, URL, or driver:query")],
    out: Annotated[
        str, typer.Option("--out", "-o", help="Output OKF bundle directory")
    ] = "out-okf",
    chunk: Annotated[
        bool,
        typer.Option("--chunk", help="Split multi-section documents into multiple concepts"),
    ] = False,
    unstructured_languages: Annotated[
        str,
        typer.Option("--unstructured-languages", help="Comma-separated languages for unstructured"),
    ] = "eng",
    limit: Annotated[
        int, typer.Option("--limit", help="Max items to convert (0 = no limit)")
    ] = 100,
    s3_anonymous: Annotated[
        bool,
        typer.Option("--s3-anonymous", help="Force anonymous S3 access (public buckets)"),
    ] = False,
) -> None:
    """Convert a source into a minimal OKF bundle."""
    from churn.extract import extract_to_markdown_and_chunks, map_metadata
    from churn.okf import (
        append_log_entry,
        compute_manifest,
        ensure_static_dir,
        make_frontmatter,
        make_index_entry,
        write_concept,
        write_folder_frontmatter,
        write_index,
    )

    out_path = Path(out).resolve()
    out_path.mkdir(parents=True, exist_ok=True)

    driver = None
    entries: list[dict[str, str]] = []
    truncated = False
    failures = 0
    total_items = 0

    try:
        driver, query, fs_root = _resolve_driver_and_query(source, s3_anonymous=s3_anonymous)
        driver.connect()
        items = driver.list_items(query)
        total_items = len(items)

        if not items:
            console.print(f"[red]No items found for source:[/] {source}")
            raise typer.Exit(1)

        work_items = items if limit <= 0 else items[:limit]
        truncated = limit > 0 and total_items > limit

        lang_list = [x.strip() for x in unstructured_languages.split(",") if x.strip()]
        unstructured_cfg = {"languages": lang_list} if lang_list else None
        parsed = _parse_driver_query(source)
        is_http = source.startswith(("http://", "https://")) or (
            parsed is not None and parsed[0] == "http"
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Converting {len(work_items)} item(s) from {source[:40]}...",
                total=len(work_items),
            )
            for item in work_items:
                try:
                    fetched = driver.fetch_item(item)

                    if fs_root:
                        try:
                            rel = Path(item.path_or_uri).resolve().relative_to(fs_root)
                            concept_id = str(rel.with_suffix(".md")).replace("\\", "/")
                        except Exception:
                            concept_id = Path(item.id or item.path_or_uri).with_suffix(".md").name
                    elif is_http:
                        concept_id = _http_concept_id(item.path_or_uri)
                    else:
                        u = item.path_or_uri
                        base = Path(u).stem or Path(u.rstrip("/")).name or item.id or "concept"
                        base = re.sub(r"[^A-Za-z0-9._-]+", "-", base).strip("-") or "concept"
                        concept_id = f"{base}.md"
                    concept_id = concept_id.replace("\\", "/")

                    try:
                        ch_bodies, hints = extract_to_markdown_and_chunks(
                            fetched.content,
                            mime=fetched.mime,
                            path_hint=item.path_or_uri,
                            max_chars=4000,
                            unstructured_config=unstructured_cfg,
                            chunk=chunk,
                        )
                        hints = map_metadata(hints, None, unstructured_cfg)
                        path_hint = Path(item.path_or_uri)
                        title = hints.get("title") or path_hint.stem.replace("_", " ").title()
                        desc = hints.get("description") or f"Imported from {path_hint.name}"
                        typ = hints.get("suggested_type") or "LegacyDocument"
                    except Exception:
                        raw = fetched.content.decode("utf-8", errors="replace")
                        body_f = _strip_leading_frontmatter(raw)[:4000].strip()
                        title = Path(item.path_or_uri).stem.replace("_", " ").title()
                        desc = f"Imported from {Path(item.path_or_uri).name}"
                        typ = "LegacyDocument"
                        if not body_f.lstrip().startswith("#"):
                            body_f = f"# {title}\n\n" + body_f
                        ch_bodies = [body_f]
                        hints = {}

                    chs: list[str] = []
                    for b in ch_bodies:
                        bb = b.lstrip()
                        if not bb.startswith("#"):
                            bb = f"# {title}\n\n" + bb
                        chs.append(bb)

                    for cidx, ch_body in enumerate(chs):
                        c_id = concept_id
                        c_title = title
                        if cidx > 0:
                            parent = Path(concept_id).parent
                            stem = Path(concept_id).stem
                            part_name = f"{stem}-part{cidx + 1}.md"
                            if str(parent) != ".":
                                c_id = str(parent / part_name).replace("\\", "/")
                            else:
                                c_id = part_name
                            c_title = f"{title} (part {cidx + 1})"
                        ch_desc = desc + (f" (chunk {cidx + 1})" if cidx > 0 else "")

                        if is_http:
                            src_label = item.id or item.path_or_uri
                        else:
                            try:
                                p = Path(item.path_or_uri)
                                src_label = (
                                    str(p.relative_to(fs_root))
                                    if fs_root and p.is_relative_to(fs_root)
                                    else p.name
                                )
                            except Exception:
                                src_label = Path(item.path_or_uri).name
                        src_label = str(src_label).replace("\\", "/")

                        fm_extra = {
                            k: v
                            for k, v in hints.items()
                            if k.startswith("meta_") and v is not None
                        }
                        fm = make_frontmatter(
                            type=typ,
                            title=c_title,
                            description=ch_desc,
                            source_path=src_label,
                            **fm_extra,
                        )
                        write_concept(out_path, c_id, fm, ch_body)
                        entries.append(make_index_entry(c_id, fm, ch_body))
                except Exception as exc:
                    failures += 1
                    console.print(f"[red]Failed {item.id}: {exc}[/]")
                progress.advance(task)

        if not entries:
            console.print(
                "[red]No concepts were written (all items failed or empty output).[/]"
            )
            raise typer.Exit(1)

        write_index(out_path, entries)

        log_msg = f"Converted {len(entries)} concept(s) from {source}"
        if truncated:
            log_msg += f" (truncated: {len(items)} discovered, {limit} limit)"
        append_log_entry(out_path, log_msg, "Creation")

        ensure_static_dir(out_path)
        try:
            src_p = Path(source).resolve()
        except Exception:
            src_p = None
        if src_p and not src_p.exists():
            src_p = None
        clean_label = (
            (src_p.name if src_p else None)
            or (_parse_driver_query(source) or ("", source))[1]
            or Path(source).name
            or "Imported"
        )
        write_folder_frontmatter(
            out_path,
            "",
            title=clean_label,
            type="category",
            description=f"Converted from {clean_label}",
            semantic_tags=["imported", "legacy-knowledge"],
        )
        subdirs = {
            str(Path(e["path"]).parent).replace("\\", "/")
            for e in entries
            if "/" in e.get("path", "")
        }
        for sd in sorted(subdirs):
            if sd and sd != ".":
                write_folder_frontmatter(
                    out_path,
                    sd,
                    title=sd,
                    type="category",
                    description=f"Subsection: {sd}",
                    semantic_tags=["group"],
                )

        manifest_path = out_path / "manifest.json"
        manifest_path.write_text(
            json.dumps(compute_manifest(out_path), indent=2) + "\n",
            encoding="utf-8",
        )
    except typer.Exit:
        raise
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(1) from exc
    except Exception as exc:
        console.print(f"[red]Convert failed:[/] {exc}")
        raise typer.Exit(1) from exc
    finally:
        if driver is not None:
            driver.close()

    trunc_note = f"\n  truncated: yes ({total_items} found, limit {limit})" if truncated else ""
    fail_note = f"\n  failures: {failures}" if failures else ""
    summary = (
        f"[green]Wrote OKF bundle[/]\n"
        f"  path: {out_path}\n"
        f"  concepts: {len(entries)}\n"
        f"  manifest.json: present{trunc_note}{fail_note}\n\n"
        f"Inspect: churn validate {out_path}; churn preview {out_path}"
    )
    console.print(Panel(summary, title="churn convert", border_style="green"))


@app.command()
def preview(
    bundle: Annotated[str, typer.Argument(help="Path to an OKF bundle directory")],
) -> None:
    """Quick preview of an OKF bundle (index + top concepts + validation summary + structure).

    Enhanced for M004: shows basic conformance (via validate_bundle), heading counts (aids ekg sections),
    folder frontmatter presence, etc. Per OKF §9 + ekg parser expectations.
    """
    b = Path(bundle).resolve()
    if not b.exists():
        console.print(f"[red]Bundle not found:[/] {b}")
        raise typer.Exit(1)

    idx = b / "index.md"
    console.print(Panel(f"[bold]Bundle:[/] {b}\n_has_index={idx.exists()}", title="churn preview", border_style="blue"))
    if idx.exists():
        console.print(idx.read_text(encoding="utf-8")[:1200])
    else:
        console.print("[yellow]No index.md[/]")

    # List a few .md files
    mds = sorted([p for p in b.rglob("*.md") if p.name not in {"index.md", "log.md"}])[:5]
    if mds:
        console.print("\n[bold]Sample concepts:[/]")
        for m in mds:
            console.print(f"  - {m.relative_to(b)}")

    # Validation summary + basic structure (headings, folders) - lean M004 enhancement
    try:
        from churn.okf import validate_bundle

        report = validate_bundle(b)
        status = "OK" if report.get("ok") else "ISSUES"
        console.print(f"\n[bold]Validation:[/] {status}  concepts={report.get('concepts', 0)}  has_index={report.get('has_index')}  root_frontmatter.yaml={report.get('root_frontmatter')}")
        if report.get("errors"):
            console.print("[yellow]Validation notes:[/]")
            for e in report["errors"][:3]:
                console.print(f"  - {e}")
    except Exception as exc:
        console.print(f"[yellow]Validation unavailable:[/] {exc}")

    # Rough heading/structure stats (supports ekg section extraction via goldmark)
    try:
        import re

        heading_count = 0
        fm_count = len(list(b.rglob("frontmatter.yaml")))
        for mdp in b.rglob("*.md"):
            if mdp.name in {"index.md", "log.md"}:
                continue
            txt = mdp.read_text(encoding="utf-8", errors="replace")
            heading_count += len(re.findall(r"^#{1,6}\s", txt, re.M))
        console.print(f"[bold]Structure:[/] headings~{heading_count}  folder_frontmatter.yaml={fm_count}")
        subs = [str(p.relative_to(b)) for p in b.iterdir() if p.is_dir()]
        if subs:
            console.print(f"  subdirs: {subs[:5]}")
    except Exception:
        pass

    # Show log.md tail if present (M004)
    logp = b / "log.md"
    if logp.exists():
        console.print("\n[bold]Recent log:[/]")
        console.print(logp.read_text(encoding="utf-8")[-400:])


@app.command()
def log(
    bundle: Annotated[str, typer.Argument(help="Path to an OKF bundle directory")],
) -> None:
    """Show log.md for the bundle (M004 stub/polish)."""
    b = Path(bundle).resolve()
    logp = b / "log.md"
    if logp.exists():
        console.print(logp.read_text(encoding="utf-8"))
    else:
        console.print("[yellow]No log.md[/]")


@app.command()
def validate(
    bundle: Annotated[str, typer.Argument(help="Path to an OKF bundle directory")],
) -> None:
    """OKF v0.1 conformance check (parseable frontmatter + non-empty type on concepts; index no fm).

    Uses writer.validate_bundle (proper yaml parse per ekg extract + SPEC §9).
    """
    b = Path(bundle).resolve()
    if not b.exists():
        console.print(f"[red]Not found:[/] {b}")
        raise typer.Exit(1)

    from churn.okf import validate_bundle

    report = validate_bundle(b)
    if not report.get("ok"):
        console.print("[red]Validation errors:[/]")
        for e in report.get("errors", []):
            console.print(f"  - {e}")
        console.print("[dim]See OKF SPEC §4.1 (required type) and ../ekg/docs/OKF-FORMAT.md[/]")
        raise typer.Exit(1)
    console.print(
        f"[green]OK[/] — {report.get('concepts', 0)} concepts conformant. "
        f"has_index={report.get('has_index')} root_fm={report.get('root_frontmatter')}"
    )


def _strip_leading_frontmatter(text: str) -> str:
    """Remove a leading YAML frontmatter block if present (robust version)."""
    lines = text.splitlines(keepends=True)
    if not lines or not lines[0].strip().startswith("---"):
        return text

    # Find the closing ---
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            # Return everything after the closing line (drop the frontmatter + the --- line)
            rest = "".join(lines[i+1:])
            return rest.lstrip("\n\r")
    # No proper closing found — return original
    return text


def version_callback() -> None:
    """Helper for tests."""
    console.print(f"churn {__version__}")


if __name__ == "__main__":
    app()
