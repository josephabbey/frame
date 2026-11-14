"""Google OAuth and account implementation of :class:`frame.data.AccountAPI`."""

import asyncio
import dataclasses
import logging
from datetime import datetime, timedelta
from urllib.parse import urlencode

from dacite import Config, from_dict

from frame.data.account import Account, AccountAPI, OAuthToken
from frame.flow import FLOW_CLIENT
from frame.loop import LOOP

from .client import GOOGLE_CLIENT

logger = logging.getLogger(__name__)


AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

# Inserted by flow
CLIENT_ID = "__CLIENT_ID"
CLIENT_SECRET = "__CLIENT_SECRET"
REDIRECT_URI = "__REDIRECT_URI"

SCOPES = {"openid"}
ALL_SCOPES: set[str] = SCOPES.copy()


class GoogleAccountAPI(AccountAPI):
  """OAuth token refresh and OpenID Connect profile lookup for Google."""

  def authorization_url(self) -> str:
    query = urlencode(
      {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "access_type": "offline",
        "prompt": "consent",
        "scope": " ".join(ALL_SCOPES),
      }
    )
    url = f"{AUTHORIZATION_URL}?{query}"
    logger.info(f"Google authorization URL: {url}")
    return url

  async def on_authorization_code(self, msg: dict):
    await self.exchange_code(code=msg.get("code"))

  async def exchange_code(self, code: str):
    from .store import GOOGLE_STORE

    logger.info("Exchanging Google access token")
    res = await FLOW_CLIENT.send_json_request(
      {
        "type": "web.request_json",
        "method": "POST",
        "url": TOKEN_URL,
        "data": {
          "code": code,
          "client_id": CLIENT_ID,
          "client_secret": CLIENT_SECRET,
          "redirect_uri": REDIRECT_URI,
          "grant_type": "authorization_code",
        },
      }
    )

    GOOGLE_STORE.token = from_dict(
      OAuthToken,
      res.get("data"),
      Config(
        type_hooks={
          set[str]: lambda s: set(s.split(" ")),
        },
        convert_key=lambda k: "scope" if k == "scopes" else k,
      ),
    )

    global GOOGLE_ACCOUNT_API_TASK
    if GOOGLE_ACCOUNT_API_TASK.done():
      GOOGLE_ACCOUNT_API_TASK = LOOP.create_task(self.run_forever())

  async def refresh_token(self) -> OAuthToken:
    from .store import GOOGLE_STORE

    logger.info("Refreshing Google access token")
    res = await FLOW_CLIENT.send_json_request(
      {
        "type": "web.request_json",
        "method": "POST",
        "url": TOKEN_URL,
        "data": {
          "client_id": CLIENT_ID,
          "client_secret": CLIENT_SECRET,
          "refresh_token": GOOGLE_STORE.token.refresh_token,
          "grant_type": "refresh_token",
        },
      }
    )
    token = from_dict(
      OAuthToken,
      res.get("data"),
      Config(
        type_hooks={
          datetime: lambda v: (
            datetime.now() + timedelta(seconds=v) if isinstance(v, (int, float)) else v
          ),
        },
        convert_key=lambda k: "expires_in" if k == "expires_at" else k,
      ),
    )

    if token.refresh_token is None:
      token = dataclasses.replace(token, refresh_token=GOOGLE_STORE.token.refresh_token)
    GOOGLE_STORE.token = token
    GOOGLE_CLIENT.authorized.set()
    return token

  async def run_forever(self):
    from .store import GOOGLE_STORE

    if GOOGLE_STORE.token:
      while True:
        token = await self.refresh_token()
        if token.expires_at:
          await asyncio.sleep((token.expires_at - datetime.now()).seconds - 300)

  async def get_account(self) -> Account:
    payload = await GOOGLE_CLIENT.request_json(
      "GET",
      USERINFO_URL,
    )
    return Account(
      id=str(payload["sub"]),
      provider="google",
      display_name=str(payload.get("name") or payload.get("email", "Google user")),
      email=payload.get("email"),
      avatar_url=payload.get("picture"),
    )


GOOGLE_ACCOUNT_API = GoogleAccountAPI()


FLOW_CLIENT.register(
  "google.account.authorization_url[get]",
  lambda _: FLOW_CLIENT.send_json(
    {
      "type": "google.account.authorization_url",
      "url": GOOGLE_ACCOUNT_API.authorization_url(),
    }
  ),
)

FLOW_CLIENT.register(
  "google.account.authorization_code",
  GOOGLE_ACCOUNT_API.on_authorization_code,
)


GOOGLE_ACCOUNT_API_TASK = LOOP.create_task(GOOGLE_ACCOUNT_API.run_forever())
