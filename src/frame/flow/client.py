"""WebSocket client integrating Frame with Frame Flow."""

import asyncio
import json
import logging
import random
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Any, cast

import websockets
from websockets.asyncio.client import ClientConnection
from websockets.protocol import State

from frame.data.account import Account, OAuthToken
from frame.google import (
    GoogleAccountAPI,
    GoogleCalendarAPI,
    GoogleIntegration,
    GoogleOAuthConfig,
    GooglePhotosAPI,
    GoogleTasksAPI,
    GoogleTransport,
)
from frame.settings.store import SettingsStore

from .settings import FlowSettings

logger = logging.getLogger(__name__)


def _token_from_google_credentials(creds: Mapping[str, Any]) -> OAuthToken:
    """Build an OAuthToken from a frame-flow google.credentials payload."""
    expiry_date = creds.get("expiry_date")
    expires_at: datetime | None = None
    if isinstance(expiry_date, (int, float)):
        # frame-flow sends JavaScript Date.getTime() milliseconds since epoch
        expires_at = datetime.fromtimestamp(expiry_date / 1000.0, tz=UTC)
    elif isinstance(expiry_date, str):
        expires_at = datetime.fromisoformat(expiry_date)

    scopes_val = creds.get("scopes") or creds.get("scope") or ()
    if isinstance(scopes_val, str):
        scopes = tuple(scopes_val.split())
    elif isinstance(scopes_val, (list, tuple)):
        scopes = tuple(str(s) for s in scopes_val)
    else:
        scopes = ()

    return OAuthToken(
        access_token=str(creds.get("access_token", "")),
        token_type=str(creds.get("token_type", "Bearer")),
        expires_at=expires_at,
        refresh_token=(
            str(creds["refresh_token"])
            if creds.get("refresh_token") is not None
            else None
        ),
        scopes=scopes,
    )


class FlowClient:
    """Maintains a resilient WebSocket connection to Frame Flow."""

    def __init__(
        self,
        settings: FlowSettings | None = None,
        *,
        settings_store: SettingsStore | None = None,
        websocket_url: str | None = None,
        reconnect_delay: float = 2.0,
        max_reconnect_delay: float = 60.0,
        backoff_factor: float = 1.5,
    ) -> None:
        if settings is not None:
            self.settings = settings
        elif settings_store is not None:
            self.settings = cast(FlowSettings, settings_store.current)
        else:
            self.settings = FlowSettings()

        self.settings_store = settings_store
        self.google = GoogleIntegration(self.settings)
        self._custom_url = websocket_url
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_delay = max_reconnect_delay
        self.backoff_factor = backoff_factor

        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._connection: ClientConnection | None = None
        self._relay_connected = False

        self._connected_listeners: list[Callable[[], None]] = []
        self._disconnected_listeners: list[Callable[[], None]] = []
        self._oauth_listeners: list[Callable[[str, OAuthToken], None]] = []
        self._settings_listeners: list[Callable[[FlowSettings], None]] = []
        self._custom_handlers: dict[str, list[Callable[[dict[str, Any]], Any]]] = {}

    @property
    def websocket_url(self) -> str:
        """The active WebSocket URL for this frame."""
        return self._custom_url or self.settings.websocket_url

    @property
    def is_connected(self) -> bool:
        """Whether the WebSocket connection is open."""
        connection = self._connection
        if connection is None:
            return False
        state = getattr(connection, "state", None)
        if state is not None:
            return state is State.OPEN or state == State.OPEN
        closed = getattr(connection, "closed", None)
        if closed is not None:
            return not bool(closed)
        return False

    def _is_connection_closed(self, connection: Any) -> bool:
        state = getattr(connection, "state", None)
        if state is not None:
            return state is State.CLOSED or state == State.CLOSED
        closed = getattr(connection, "closed", None)
        if closed is not None:
            return bool(closed)
        return False

    @property
    def is_relay_connected(self) -> bool:
        """Whether the relay server has acknowledged frame registration."""
        if not self._relay_connected:
            return False
        if self._connection is None:
            return True
        return self.is_connected

    # Callback registrations

    def on_connected(self, callback: Callable[[], None]) -> Callable[[], None]:
        """Subscribe to relay connection events."""
        self._connected_listeners.append(callback)
        return lambda: self._connected_listeners.remove(callback)

    def on_disconnected(self, callback: Callable[[], None]) -> Callable[[], None]:
        """Subscribe to disconnection events."""
        self._disconnected_listeners.append(callback)
        return lambda: self._disconnected_listeners.remove(callback)

    def on_oauth_credentials(
        self, callback: Callable[[str, OAuthToken], None]
    ) -> Callable[[], None]:
        """Subscribe to OAuth credential arrival (provider, token)."""
        self._oauth_listeners.append(callback)
        return lambda: self._oauth_listeners.remove(callback)

    def on_settings_update(
        self, callback: Callable[[FlowSettings], None]
    ) -> Callable[[], None]:
        """Subscribe to remote settings updates."""
        self._settings_listeners.append(callback)
        return lambda: self._settings_listeners.remove(callback)

    def register_handler(
        self, message_type: str, handler: Callable[[dict[str, Any]], Any]
    ) -> None:
        """Register a handler for a specific message type."""
        self._custom_handlers.setdefault(message_type, []).append(handler)

    # Lifecycle management

    def start(self) -> asyncio.Task[None]:
        """Start the client connection loop in a background task."""
        if self._task is not None and not self._task.done():
            return self._task
        self._running = True
        self._task = asyncio.create_task(self.run_forever())
        return self._task

    async def stop(self) -> None:
        """Stop the client and close the active connection."""
        self._running = False
        if self._connection is not None and not self._is_connection_closed(
            self._connection
        ):
            await self._connection.close()
            self._connection = None
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        self._set_disconnected()

    async def run_forever(self) -> None:
        """Maintain connection with exponential backoff and jitter."""
        self._running = True
        current_delay = self.reconnect_delay
        while self._running:
            try:
                await self.connect_once()
                current_delay = self.reconnect_delay
            except (
                TimeoutError,
                websockets.exceptions.ConnectionClosed,
                OSError,
            ) as exc:
                logger.warning("Flow connection lost: %s", exc)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Unexpected error in Flow client")

            self._set_disconnected()
            if not self._running:
                break

            jitter = random.uniform(0.8, 1.2)
            sleep_time = min(current_delay * jitter, self.max_reconnect_delay)
            current_delay = min(
                current_delay * self.backoff_factor, self.max_reconnect_delay
            )
            try:
                await asyncio.sleep(sleep_time)
            except asyncio.CancelledError:
                break

    async def connect_once(self) -> None:
        """Connect to the WebSocket and process incoming messages."""
        async with websockets.connect(self.websocket_url) as ws:
            self._connection = ws
            logger.info("Connected to Flow WebSocket relay: %s", self.websocket_url)
            async for raw in ws:
                await self._handle_message(raw)

    async def send_json(self, payload: Mapping[str, Any]) -> None:
        """Send a JSON payload over the active WebSocket."""
        if self._connection is None or not self.is_connected:
            raise ConnectionError("WebSocket is not connected")
        await self._connection.send(json.dumps(payload))

    # Internal message handling

    async def _handle_message(self, raw: str | bytes) -> None:
        try:
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                return
        except (ValueError, TypeError, UnicodeError) as exc:
            logger.warning("Received invalid JSON from Flow relay: %r (%s)", raw, exc)
            return

        msg_type = payload.get("type")

        # 1. Connected acknowledgement
        if msg_type == "connected":
            self._relay_connected = True
            for callback in list(self._connected_listeners):
                try:
                    callback()
                except Exception:
                    logger.exception("Error in Flow connected listener")

        # 2. Google OAuth credentials
        elif msg_type == "google.credentials":
            creds = payload.get("credentials")
            if isinstance(creds, Mapping):
                token = _token_from_google_credentials(creds)
                self.settings.google_token = token
                if self.settings_store is not None:
                    self.settings_store.save(self.settings)

                for oauth_cb in list(self._oauth_listeners):
                    try:
                        oauth_cb("google", token)
                    except Exception:
                        logger.exception("Error in Flow OAuth listener")

                # Acknowledge receipt back over socket if possible
                try:
                    await self.send_json(
                        {
                            "type": "oauth.success",
                            "provider": "google",
                            "scopes": list(token.scopes),
                        }
                    )
                except Exception:
                    logger.debug("Failed to send OAuth acknowledgement", exc_info=True)

        # 3. FlowSettings update from phone / web app
        elif msg_type == "settings.update":
            updates = payload.get("settings")
            if isinstance(updates, Mapping):
                for key, val in updates.items():
                    if hasattr(self.settings, key) and key != "frame_key":
                        setattr(self.settings, key, val)
                    else:
                        self.settings.custom[key] = val

                if self.settings_store is not None:
                    self.settings_store.save(self.settings)

                for settings_cb in list(self._settings_listeners):
                    try:
                        settings_cb(self.settings)
                    except Exception:
                        logger.exception("Error in Flow settings listener")

                try:
                    await self.send_json(
                        {
                            "type": "settings.state",
                            "settings": self.settings.to_dict(include_secrets=False),
                        }
                    )
                except Exception:
                    logger.debug("Failed to send settings state", exc_info=True)

        # 4. FlowSettings request
        elif msg_type == "settings.get":
            try:
                await self.send_json(
                    {
                        "type": "settings.state",
                        "settings": self.settings.to_dict(include_secrets=False),
                    }
                )
            except Exception:
                logger.debug("Failed to send settings state", exc_info=True)

        # 5. Ping / Pong
        elif msg_type == "ping":
            try:
                await self.send_json({"type": "pong"})
            except Exception:
                logger.debug("Failed to send pong", exc_info=True)

        # Dispatch any registered custom message handlers
        if msg_type and msg_type in self._custom_handlers:
            for handler in self._custom_handlers[msg_type]:
                try:
                    res = handler(payload)
                    if asyncio.iscoroutine(res):
                        await res
                except Exception:
                    logger.exception("Error in custom handler for %s", msg_type)

    def _set_disconnected(self) -> None:
        was_connected = self._relay_connected or (
            self._connection is not None
            and not self._is_connection_closed(self._connection)
        )
        self._relay_connected = False
        self._connection = None
        if was_connected:
            for callback in list(self._disconnected_listeners):
                try:
                    callback()
                except Exception:
                    logger.exception("Error in Flow disconnected listener")

    # Google Client Integrations (delegated to frame.google)

    def get_google_account_api(
        self,
        transport: GoogleTransport | None = None,
        oauth_config: GoogleOAuthConfig | None = None,
    ) -> GoogleAccountAPI | None:
        return self.google.get_google_account_api(
            transport=transport, oauth_config=oauth_config
        )

    def get_account_api(
        self,
        transport: GoogleTransport | None = None,
        oauth_config: GoogleOAuthConfig | None = None,
    ) -> GoogleAccountAPI | None:
        return self.google.get_account_api(
            transport=transport, oauth_config=oauth_config
        )

    def get_google_photos_api(
        self, transport: GoogleTransport | None = None
    ) -> GooglePhotosAPI | None:
        return self.google.get_google_photos_api(transport=transport)

    def get_photos_api(
        self, transport: GoogleTransport | None = None
    ) -> GooglePhotosAPI | None:
        return self.google.get_photos_api(transport=transport)

    def get_google_calendar_api(
        self, transport: GoogleTransport | None = None
    ) -> GoogleCalendarAPI | None:
        return self.google.get_google_calendar_api(transport=transport)

    def get_calendar_api(
        self, transport: GoogleTransport | None = None
    ) -> GoogleCalendarAPI | None:
        return self.google.get_calendar_api(transport=transport)

    def get_google_tasks_api(
        self, transport: GoogleTransport | None = None
    ) -> GoogleTasksAPI | None:
        return self.google.get_google_tasks_api(transport=transport)

    def get_tasks_api(
        self, transport: GoogleTransport | None = None
    ) -> GoogleTasksAPI | None:
        return self.google.get_tasks_api(transport=transport)

    async def verify_google_account(
        self,
        transport: GoogleTransport | None = None,
        oauth_config: GoogleOAuthConfig | None = None,
    ) -> Account | None:
        before_token = self.settings.google_token
        result = await self.google.verify_account(
            transport=transport, oauth_config=oauth_config
        )
        if (
            self.settings_store is not None
            and self.settings.google_token is not before_token
        ):
            self.settings_store.save(self.settings)
        return result

    async def verify_account(
        self,
        transport: GoogleTransport | None = None,
        oauth_config: GoogleOAuthConfig | None = None,
    ) -> Account | None:
        return await self.verify_google_account(
            transport=transport, oauth_config=oauth_config
        )
