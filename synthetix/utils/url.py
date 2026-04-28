"""URL utilities."""

from urllib.parse import urlparse, urlunparse

_WS_TO_HTTP_SCHEME = {"wss": "https", "ws": "http"}


def ws_to_http(ws_url: str) -> str:
    """Convert a WebSocket URL to its HTTP equivalent.

    ``wss://`` becomes ``https://``, ``ws://`` becomes ``http://``.
    Non-WebSocket schemes (``http``, ``https``) are returned unchanged.
    """
    parsed = urlparse(ws_url)
    scheme = _WS_TO_HTTP_SCHEME.get(parsed.scheme, parsed.scheme)
    return urlunparse(parsed._replace(scheme=scheme))
