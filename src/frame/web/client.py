import asyncio
import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

import httpx
from httpx_file import FileTransport

logger = logging.getLogger(__name__)


_client = httpx.AsyncClient(timeout=30, mounts={"file://": FileTransport()})


@dataclass(slots=True, kw_only=True)
class WebClient:
  async def request_json(
    self,
    method: str,
    url: str,
    *,
    headers: Mapping[str, str] | None = None,
    params: Mapping[str, str] | None = None,
    json: Mapping[str, Any] | None = None,
  ) -> Mapping[str, Any]:
    logger.debug(f"Request: {method} {url} {headers} {params} {json}")

    try:
      response = await _client.request(
        method=method,
        url=url,
        headers=headers,
        params=params,
        json=json,
      )
      response.raise_for_status()

      content = response.text.strip()
      if not content:
        return {}

      parsed = response.json()
      logger.debug(f"Response: {parsed}")
      if isinstance(parsed, Mapping):
        return parsed
      return {"items": parsed}

    except httpx.HTTPStatusError as exc:
      error_body = exc.response.text
      raise RuntimeError(
        f"HTTP {exc.response.status_code} for {method} {url}: {error_body}"
      ) from exc

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
    logger.debug(f"Request: {method} {url} {headers} {params} {json}")

    try:
      response = await _client.request(
        method=method,
        url=url,
        headers=headers,
        params=params,
        json=json,
        content=content,
      )
      response.raise_for_status()

      return response.content

    except httpx.HTTPStatusError as exc:
      error_body = exc.response.text
      raise RuntimeError(
        f"HTTP {exc.response.status_code} for {method} {url}: {error_body}"
      ) from exc


class NotAuthenticated(Exception): ...


@dataclass(slots=True, kw_only=True)
class AuthorizedWebClient(WebClient):
  authorized: asyncio.Event = field(default_factory=asyncio.Event)

  async def request_json(
    self,
    method: str,
    url: str,
    *,
    headers: Mapping[str, str] | None = None,
    params: Mapping[str, str] | None = None,
    json: Mapping[str, Any] | None = None,
  ) -> Mapping[str, Any]:
    logger.debug("Waiting for authorization")
    await self.authorized.wait()
    logger.debug("Authorized")
    return await super().request_json(
      method=method,
      url=url,
      headers=headers,
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
    logger.debug("Waiting for authorization")
    await self.authorized.wait()
    logger.debug("Authorized")
    return await super().request(
      method=method,
      url=url,
      headers=headers,
      params=params,
      json=json,
      content=content,
    )


WEB_CLIENT = WebClient()
