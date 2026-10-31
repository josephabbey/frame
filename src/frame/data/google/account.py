"""Google OAuth and account implementation of :class:`frame.data.AccountAPI`."""

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

from frame.data.account import Account, AccountAPI, OAuthToken

from .client import GoogleClient, GoogleOAuthConfig, GoogleTransport

_AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


class GoogleAccountAPI(GoogleClient, AccountAPI):
    """OAuth token refresh and OpenID Connect profile lookup for Google."""

    def __init__(
        self,
        transport: GoogleTransport,
        token: OAuthToken,
        oauth: GoogleOAuthConfig,
    ) -> None:
        super().__init__(transport, token)
        self.oauth = oauth

    def authorization_url(self, *, state: str, scopes: tuple[str, ...]) -> str:
        query = urlencode(
            {
                "client_id": self.oauth.client_id,
                "redirect_uri": self.oauth.redirect_uri,
                "response_type": "code",
                "access_type": "offline",
                "prompt": "consent",
                "scope": " ".join(scopes),
                "state": state,
            }
        )
        return f"{_AUTHORIZATION_URL}?{query}"

    async def get_account(self, token: OAuthToken) -> Account:
        payload = await self.transport.request(
            "GET",
            _USERINFO_URL,
            headers={"Authorization": f"Bearer {token.access_token}"},
        )
        return Account(
            id=str(payload["sub"]),
            provider="google",
            display_name=str(payload.get("name") or payload.get("email", "Google user")),
            email=payload.get("email"),
            avatar_url=payload.get("picture"),
        )

    async def exchange_code(self, code: str) -> OAuthToken:
        return await self._token_from_payload(
            await self.transport.request(
                "POST",
                _TOKEN_URL,
                json={
                    "code": code,
                    "client_id": self.oauth.client_id,
                    "client_secret": self.oauth.client_secret,
                    "redirect_uri": self.oauth.redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
        )

    async def refresh_token(self, refresh_token: str) -> OAuthToken:
        return await self._token_from_payload(
            await self.transport.request(
                "POST",
                _TOKEN_URL,
                json={
                    "client_id": self.oauth.client_id,
                    "client_secret": self.oauth.client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
        )

    @staticmethod
    async def _token_from_payload(payload: Mapping[str, Any]) -> OAuthToken:
        expires_in = payload.get("expires_in")
        return OAuthToken(
            access_token=str(payload["access_token"]),
            token_type=str(payload.get("token_type", "Bearer")),
            expires_at=(
                datetime.now(UTC) + timedelta(seconds=int(expires_in))
                if expires_in is not None
                else None
            ),
            refresh_token=(
                str(payload["refresh_token"])
                if payload.get("refresh_token") is not None
                else None
            ),
            scopes=tuple(str(payload.get("scope", "")).split()),
        )
