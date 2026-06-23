"""Light HTTP driver test (uses public endpoint, no secrets)."""

import pytest

from churn.drivers import get_driver


@pytest.mark.network
def test_http_driver_live_fetch():
    d = get_driver("http")
    d.connect()
    items = d.list_items("https://httpbin.org/json")
    assert len(items) == 1
    f = d.fetch_item(items[0])
    assert len(f.content) > 10
    assert "json" in (f.mime or "").lower() or f.content[:1] in (b"{", b"[")
    d.close()
