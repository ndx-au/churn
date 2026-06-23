"""Driver discovery via entry points + built-in drivers."""

from __future__ import annotations

import importlib.metadata as importlib_metadata
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from churn.drivers.base import SourceDriver


def discover_drivers() -> dict[str, type[SourceDriver]]:
    """Discover all drivers registered under the 'churn.drivers' entry point group."""
    drivers: dict[str, type[SourceDriver]] = {}

    # Built-in drivers
    try:
        from churn.drivers.filesystem import FileSystemDriver

        drivers["filesystem"] = FileSystemDriver
    except Exception:
        pass

    try:
        from churn.drivers.http import HTTPDriver

        drivers["http"] = HTTPDriver
    except Exception:
        pass

    try:
        from churn.drivers.s3 import S3Driver

        drivers["s3"] = S3Driver
    except Exception:
        pass

    # External / installed drivers (cannot override built-ins)
    _builtin_names = frozenset(drivers.keys())
    try:
        eps = importlib_metadata.entry_points(group="churn.drivers")
        for ep in eps:
            if ep.name in _builtin_names:
                import warnings
                warnings.warn(
                    f"Skipping external driver {ep.name!r}: built-in name reserved",
                    stacklevel=2,
                )
                continue
            try:
                driver_cls = ep.load()
                drivers[ep.name] = driver_cls
            except Exception as exc:  # pragma: no cover
                # Never let one bad driver break discovery
                import warnings
                warnings.warn(f"Failed to load driver {ep.name}: {exc}", stacklevel=2)
    except Exception:
        pass

    return drivers


def get_driver(name: str, config: dict | None = None) -> SourceDriver:
    """Instantiate a driver by registered name."""
    drivers = discover_drivers()
    if name not in drivers:
        available = ", ".join(sorted(drivers.keys())) or "(none)"
        raise KeyError(f"Unknown driver {name!r}. Available: {available}")
    return drivers[name](config)
