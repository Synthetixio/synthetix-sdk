"""
Base REST client for Synthetix V4 API.
"""

from typing import Any, Optional

import requests


class SynthetixAPIError(Exception):
    """Raised when the API returns a 200 with an error payload."""

    def __init__(self, message: str, response: Any = None):
        super().__init__(message)
        self.response = response


class ClientError(Exception):
    """Raised on 4xx HTTP responses."""

    def __init__(self, status_code: int, message: str):
        super().__init__(f"HTTP {status_code}: {message}")
        self.status_code = status_code


class ServerError(Exception):
    """Raised on 5xx HTTP responses."""

    def __init__(self, status_code: int, message: str):
        super().__init__(f"HTTP {status_code}: {message}")
        self.status_code = status_code


class API:
    """Synchronous REST client using requests.Session."""

    def __init__(self, base_url: str, timeout: Optional[float] = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.timeout = timeout

    def post(self, path: str, payload: dict) -> Any:
        """POST JSON to base_url + path. Returns parsed response data."""
        url = f"{self.base_url}{path}"
        resp = self.session.post(url, json=payload, timeout=self.timeout)

        # HTTP-level errors
        if 400 <= resp.status_code < 500:
            raise ClientError(resp.status_code, resp.text)
        if resp.status_code >= 500:
            raise ServerError(resp.status_code, resp.text)

        try:
            data = resp.json()
        except Exception:
            raise ServerError(resp.status_code, f"Non-JSON response: {resp.text[:200]}")

        # Application-level errors (200 with error payload)
        if isinstance(data, dict):
            if data.get("status") == "error":
                msg = data.get("error", {}).get("message", "") or data.get("reason", str(data))
                raise SynthetixAPIError(msg, response=data)
            if "error" in data and "result" not in data:
                err = data["error"]
                msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
                raise SynthetixAPIError(msg, response=data)

        # Unwrap standard envelope: {"status": "ok", "response": <data>}
        if isinstance(data, dict) and "response" in data and data.get("status") == "ok":
            return data["response"]

        return data
