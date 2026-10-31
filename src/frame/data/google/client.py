"""Shared primitives for Google API adapters.

The transport is intentionally injected so applications can use ``httpx``,
``aiohttp``, or their own retrying transport without coupling this package to
one HTTP dependency.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from frame.data.account import OAuthToken


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


@dataclass(frozen=True, slots=True)
class GoogleOAuthConfig:
    client_id: str
    client_secret: str
    redirect_uri: str


@dataclass(slots=True)
class GoogleClient:
    """Base client that adds an OAuth bearer token to Google requests."""

    transport: GoogleTransport
    token: OAuthToken

    def authorization_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token.access_token}"}

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, str] | None = None,
        json: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        return await self.transport.request(
            method,
            url,
            headers=self.authorization_headers(),
            params=params,
            json=json,
        )
