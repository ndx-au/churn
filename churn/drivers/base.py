"""SourceDriver abstract base class and plugin protocol.

All drivers MUST implement this interface and be registered via
the "churn.drivers" entry point.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SourceItem:
    """Lightweight descriptor of a discoverable item from a source."""
    id: str
    path_or_uri: str
    size: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FetchedContent:
    """Result of fetching a single item."""
    item: SourceItem
    content: bytes
    mime: str | None = None
    sha256: str | None = None


class SourceDriver(ABC):
    """Abstract base for all CHURN source drivers.

    Lifecycle:
        1. driver = DriverClass(config)
        2. await driver.connect()   # or sync equivalent in simple drivers
        3. items = await driver.list_items(...)
        4. content = await driver.fetch_item(item)
        5. (optional) driver.close()

    Drivers are responsible only for connectivity + byte fetch.
    Parsing / normalization / OKF rendering is handled by the core.
    """

    name: str = "base"
    description: str = "Base driver (abstract)"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self._connected = False

    # --- connection / lifecycle -------------------------------------------------

    def connect(self) -> None:
        """Establish connection / validate credentials. Idempotent."""
        self._connected = True

    def close(self) -> None:
        """Release resources."""
        self._connected = False

    # --- discovery --------------------------------------------------------------

    @abstractmethod
    def list_items(self, query: str | None = None, **kwargs: Any) -> list[SourceItem]:
        """Return a list of available items.

        Drivers should be lazy where possible but return a concrete list for CLI friendliness.
        """
        raise NotImplementedError

    # --- fetch ------------------------------------------------------------------

    @abstractmethod
    def fetch_item(self, item: SourceItem) -> FetchedContent:
        """Fetch the raw bytes for one item."""
        raise NotImplementedError

    # --- convenience ------------------------------------------------------------

    def __enter__(self) -> SourceDriver:
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r} connected={self._connected}>"
