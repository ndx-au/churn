"""HTTPDriver — fetch content over HTTP/HTTPS.

Opportunistic. Supports simple GET + basic auth via query or config.
Uses httpx + tenacity for resilience (M002).
"""

from __future__ import annotations

import hashlib
from typing import Any

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from churn.drivers.base import FetchedContent, SourceDriver, SourceItem


class HTTPDriver(SourceDriver):
    name = "http"
    description = "HTTP/HTTPS fetch (GET). Basic resilience + headers."

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.timeout = float(self.config.get("timeout", 30))
        self.headers = dict(self.config.get("headers", {}))
        self.max_bytes = int(self.config.get("max_bytes", 50 * 1024 * 1024))
        auth = self.config.get("auth")
        self._auth: httpx.Auth | tuple[str, str] | None = auth
        self._client: httpx.Client | None = None

    def connect(self) -> None:
        self._client = httpx.Client(
            timeout=self.timeout,
            headers=self.headers,
            auth=self._auth,
            follow_redirects=True,
        )
        super().connect()

    def close(self) -> None:
        if self._client:
            self._client.close()
        super().close()

    def list_items(self, query: str | None = None, **kwargs: Any) -> list[SourceItem]:
        """For HTTP driver, a 'query' is typically a single URL or a manifest."""
        if not query:
            return []
        # Treat query as direct URL for v1
        return [SourceItem(id=query, path_or_uri=query, metadata={"url": query})]

    @staticmethod
    def _is_retryable(exc: BaseException) -> bool:
        if isinstance(exc, httpx.HTTPStatusError):
            return exc.response.status_code >= 500 or exc.response.status_code == 429
        return isinstance(exc, (httpx.TimeoutException, httpx.TransportError))

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=1, max=8),
        retry=retry_if_exception(_is_retryable),
        reraise=True,
    )
    def fetch_item(self, item: SourceItem) -> FetchedContent:
        if not self._client:
            self.connect()
        assert self._client is not None
        with self._client.stream("GET", item.path_or_uri) as resp:
            resp.raise_for_status()
            chunks: list[bytes] = []
            total = 0
            for chunk in resp.iter_bytes():
                total += len(chunk)
                if total > self.max_bytes:
                    raise ValueError(
                        f"Response exceeds max size ({self.max_bytes} bytes): {item.path_or_uri}"
                    )
                chunks.append(chunk)
            data = b"".join(chunks)
        sha = hashlib.sha256(data).hexdigest()
        raw_mime = resp.headers.get("content-type")
        mime = raw_mime.split(";", 1)[0].strip() if raw_mime else None
        return FetchedContent(item=item, content=data, mime=mime, sha256=sha)
