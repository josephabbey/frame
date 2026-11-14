"""Shared primitives for Google API adapters."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from frame.web import AuthorizedClient, NotAuthenticated

# Store is imported lazily to avoid circular imports during package initialization.


@dataclass(slots=True, kw_only=True)
class GoogleClient(AuthorizedClient):
  """Base client that adds an OAuth bearer token to Google requests."""

  def authorization_headers(self) -> dict[str, str]:
    from .store import GOOGLE_STORE

    if GOOGLE_STORE.token:
      return {"Authorization": f"Bearer {GOOGLE_STORE.token.access_token}"}
    raise NotAuthenticated()

  async def request_json(
    self,
    method: str,
    url: str,
    *,
    headers: Mapping[str, str] | None = None,
    params: Mapping[str, str] | None = None,
    json: Mapping[str, Any] | None = None,
  ) -> Mapping[str, Any]:
    return await super().request_json(
      method,
      url,
      headers=(
        {**self.authorization_headers(), **headers}
        if headers
        else self.authorization_headers()
      ),
      params=params,
      json=json,
    )

  async def request(
    self,
    method: str,
    url: str,
    *,
    headers: Mapping[str, str] | None = None,
    params: Mapping[str, str] | None = None,
    json: Mapping[str, Any] | None = None,
    content: bytes | None = None,
  ) -> bytes:
    return await super().request(
      method,
      url,
      headers=(
        {**self.authorization_headers(), **headers}
        if headers
        else self.authorization_headers()
      ),
      params=params,
      json=json,
      content=content,
    )


GOOGLE_CLIENT = GoogleClient()
