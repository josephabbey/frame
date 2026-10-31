"""Shared primitives for Google API adapters."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from frame.data.account import OAuthToken

from .transport import GoogleTransport


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
