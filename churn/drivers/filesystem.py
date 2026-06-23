"""FileSystemDriver — opportunistic local files.

Supports:
- Directories (recursive walk)
- Single files
- Basic formats: .md, .txt, .rst, .html (raw), .pdf / .docx via unstructured if available

This is the canonical first driver for M002.001.
"""

from __future__ import annotations

import fnmatch
import hashlib
from pathlib import Path
from typing import Any

from churn.drivers.base import FetchedContent, SourceDriver, SourceItem

# Directories skipped during discovery (common noise / VCS / deps)
_SKIP_DIR_NAMES = frozenset({
    ".git",
    ".svn",
    ".hg",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    ".tox",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
})


class FileSystemDriver(SourceDriver):
    name = "filesystem"
    description = "Local filesystem (files and directories). Opportunistic multi-format."

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.root = Path(self.config.get("root", ".")).resolve()

    def list_items(self, query: str | None = None, **kwargs: Any) -> list[SourceItem]:
        """Walk the configured root (or a specific path) and return items."""
        target = Path(query).resolve() if query else self.root
        items: list[SourceItem] = []

        if not target.is_relative_to(self.root):
            return items

        respect_gitignore = self.config.get("respect_gitignore", True)
        gitignore = _load_gitignore_patterns(self.root) if respect_gitignore else []

        if target.is_file():
            if not _is_gitignored(target, self.root, gitignore):
                items.append(self._make_item(target))
            return items

        if not target.exists():
            return items

        max_bytes = int(self.config.get("max_file_bytes", 50 * 1024 * 1024))
        for p in sorted(target.rglob("*")):
            if any(part in _SKIP_DIR_NAMES for part in p.parts):
                continue
            if _is_gitignored(p, self.root, gitignore):
                continue
            if p.is_file():
                try:
                    if p.stat().st_size > max_bytes:
                        continue
                except OSError:
                    continue
                items.append(self._make_item(p))
        return items

    def fetch_item(self, item: SourceItem) -> FetchedContent:
        path = Path(item.path_or_uri).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError(f"Refusing to read {path} outside driver root {self.root}")
        max_bytes = int(self.config.get("max_file_bytes", 50 * 1024 * 1024))
        try:
            size = path.stat().st_size
            if size > max_bytes:
                raise ValueError(f"File exceeds max size ({max_bytes} bytes): {path}")
        except OSError as exc:
            raise ValueError(f"Cannot read {path}: {exc}") from exc
        data = path.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        mime = self._guess_mime(path)
        return FetchedContent(
            item=item,
            content=data,
            mime=mime,
            sha256=sha,
        )

    # --- helpers ----------------------------------------------------------------

    def _make_item(self, path: Path) -> SourceItem:
        try:
            size = path.stat().st_size
        except OSError:
            size = None
        return SourceItem(
            id=str(path.relative_to(self.root)) if path.is_relative_to(self.root) else str(path),
            path_or_uri=str(path),
            size=size,
            metadata={"suffix": path.suffix.lower()},
        )

    @staticmethod
    def _guess_mime(path: Path) -> str | None:
        suffix = path.suffix.lower()
        mapping = {
            ".md": "text/markdown",
            ".txt": "text/plain",
            ".html": "text/html",
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        return mapping.get(suffix)


def _load_gitignore_patterns(root: Path) -> list[tuple[str, bool]]:
    """Parse root .gitignore into (pattern, is_directory) tuples."""
    gi = root / ".gitignore"
    if not gi.is_file():
        return []
    patterns: list[tuple[str, bool]] = []
    for raw in gi.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("!"):
            continue
        is_dir = line.endswith("/")
        patterns.append((line.rstrip("/"), is_dir))
    return patterns


def _is_gitignored(path: Path, root: Path, patterns: list[tuple[str, bool]]) -> bool:
    """Return True when path matches a .gitignore pattern (simple fnmatch subset)."""
    if not patterns:
        return False
    try:
        rel = path.relative_to(root)
    except ValueError:
        return False
    rel_s = str(rel).replace("\\", "/")
    name = path.name
    parts = rel.parts
    for pat, is_dir in patterns:
        if is_dir and pat in parts:
            return True
        if fnmatch.fnmatch(rel_s, pat) or fnmatch.fnmatch(name, pat):
            return True
        if "/" not in pat and fnmatch.fnmatch(rel_s, f"*/{pat}"):
            return True
    return False
