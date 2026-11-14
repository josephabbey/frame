import asyncio
import json
import logging
import random
from collections.abc import Callable, Coroutine, Mapping
from typing import Any

import websockets
from websockets.asyncio.client import ClientConnection
from websockets.protocol import State

from frame.loop import LOOP

from .store import FLOW_STORE

logger = logging.getLogger(__name__)

FLOW_DOMAIN = "localhost:3000"
FLOW_SECURE = False

RECONNECT_DELAY = 2.0  # seconds
MAX_RECONNECT_DELAY = 60.0  # seconds
BACKOFF_FACTOR = 1.5


class FlowClient:
  _connected_listeners: list[Callable[[], None]]
  _disconnected_listeners: list[Callable[[], None]]
  _registered_listeners: dict[str, Callable[[dict], Any | Coroutine]]
  _outstanding_reqs: dict[int, asyncio.Future[dict]]

  def __init__(self) -> None:
    self.connected = asyncio.Event()
    self._connection: ClientConnection | None = None
    self._relay_connected = asyncio.Event()

    self._connected_listeners = []
    self._disconnected_listeners = []
    self._registered_listeners = {}
    self._outstanding_reqs = {}

    logger.debug(f"Pairing URL: {FLOW_STORE.key}")

  @property
  def websocket_url(self) -> str:
    """The active WebSocket URL for this frame."""
    return f"ws{'s' if FLOW_SECURE else ''}://{FLOW_DOMAIN}/api/socket?role=device&key={FLOW_STORE.key}"

  @property
  def pairing_url(self) -> str:
    return f"http{'s' if FLOW_SECURE else ''}://{FLOW_DOMAIN}/?key={FLOW_STORE.key}"

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
    if not self._relay_connected.is_set():
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

  def register(
    self, msg_type: str, callback: Callable[[dict], Any | Coroutine]
  ) -> Callable[[], None]:
    self._registered_listeners[msg_type] = callback
    logger.info(f"New flow registered: {msg_type}")
    return lambda: (self._registered_listeners.pop(msg_type), None)[-1]

  # Lifecycle management

  async def run_forever(self) -> None:
    """Maintain connection with exponential backoff and jitter."""
    self._running = True
    current_delay = RECONNECT_DELAY
    while self._running:
      try:
        await self.connect_once()
        current_delay = RECONNECT_DELAY
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
      sleep_time = min(current_delay * jitter, MAX_RECONNECT_DELAY)
      current_delay = min(current_delay * BACKOFF_FACTOR, MAX_RECONNECT_DELAY)
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

  async def send_json_now(self, payload: Mapping[str, Any]) -> None:
    """Send a JSON payload over the active WebSocket."""
    if self._connection is None or not self.is_connected:
      raise ConnectionError("WebSocket is not connected")
    await self._connection.send(json.dumps(payload))

  async def send_json(self, payload: Mapping[str, Any]) -> None:
    await self.connected.wait()
    await self.send_json_now(payload)

  req_id = 0

  async def send_json_request_now(self, payload: Mapping[str, Any]) -> dict:
    """Send a JSON payload over the active WebSocket and await a response."""
    if self._connection is None or not self.is_connected:
      raise ConnectionError("WebSocket is not connected")
    p = dict(payload)
    self.req_id += 1
    p["req_id"] = self.req_id
    future: asyncio.Future[dict] = LOOP.create_future()
    self._outstanding_reqs[self.req_id] = future
    await self._connection.send(json.dumps(p))
    return await future

  async def send_json_request(self, payload: Mapping[str, Any]) -> dict:
    await self.connected.wait()
    return await self.send_json_request_now(payload)

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

    logger.debug(f"Message: {payload}")

    if not isinstance(msg_type, str):
      logger.warning("Invalid Flow message type")
      return

    req_id = payload.get("req_id")
    if req_id:
      req = self._outstanding_reqs.pop(req_id)
      req.set_result(payload)
      req.done()
      return

    if msg_type == "connected":
      self._relay_connected.set()
      self.connected.set()
      for callback in list(self._connected_listeners):
        try:
          callback()
        except Exception:
          logger.exception("Error in Flow connected listener")
      return

    callback = self._registered_listeners.get(msg_type)
    if callback is None:
      logger.warning("Unhandled Flow message type")
    else:
      awaitable = callback(payload)
      if isinstance(awaitable, Coroutine):
        asyncio.create_task(awaitable)

  def _set_disconnected(self) -> None:
    was_connected = self._relay_connected or (
      self._connection is not None and not self._is_connection_closed(self._connection)
    )
    self._relay_connected.clear()
    self._connection = None
    self.connected.clear()
    if was_connected:
      for callback in list(self._disconnected_listeners):
        try:
          callback()
        except Exception:
          logger.exception("Error in Flow disconnected listener")


FLOW_CLIENT = FlowClient()
LOOP.create_task(FLOW_CLIENT.run_forever())
