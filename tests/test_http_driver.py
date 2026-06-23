"""Light HTTP driver test (uses public endpoint, no secrets)."""

from unittest.mock import MagicMock, patch

import pytest

from churn.drivers import get_driver


def test_http_driver_uses_basic_auth_from_config():
    mock_resp = MagicMock()
    mock_resp.headers = {"content-type": "application/json"}
    mock_resp.iter_bytes.return_value = [b'{"ok":true}']
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.stream.return_value = mock_resp

    with patch("httpx.Client", return_value=mock_client) as client_cls:
        d = get_driver("http", {"auth": ("user", "secret")})
        d.connect()
        items = d.list_items("https://example.com/api")
        f = d.fetch_item(items[0])
        d.close()

    client_cls.assert_called_once()
    assert client_cls.call_args.kwargs["auth"] == ("user", "secret")
    assert len(f.content) > 0


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
