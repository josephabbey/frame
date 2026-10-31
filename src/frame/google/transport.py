"""Urllib-backed asynchronous GoogleTransport implementation."""

import asyncio
import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from typing import Any, Protocol


class GoogleTransport(Protocol):
    """Minimal JSON transport used by the Google provider adapters."""

    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        params: Mapping[str, str] | None = None,
        json: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]: ...


class UrllibGoogleTransport:
    """A standard library HTTP transport satisfying :class:`GoogleTransport`."""

    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        params: Mapping[str, str] | None = None,
        json: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        return await asyncio.to_thread(
            self._request_sync,
            method,
            url,
            headers=headers,
            params=params,
            json_body=json,
        )

    def _request_sync(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        params: Mapping[str, str] | None = None,
        json_body: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        if params:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}{urllib.parse.urlencode(params)}"

        data = None
        req_headers = dict(headers or {})
        if json_body is not None:
            data = json.dumps(json_body).encode("utf-8")
            req_headers["Content-Type"] = "application/json"

        req = urllib.request.Request(
            url,
            data=data,
            headers=req_headers,
            method=method,
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                content = response.read().decode("utf-8")
                if not content:
                    return {}
                parsed = json.loads(content)
                if isinstance(parsed, Mapping):
                    return parsed
                return {"items": parsed}
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"HTTP {exc.code} for {method} {url}: {error_body}"
            ) from exc
