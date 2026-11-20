import asyncio
import json
import logging
import random
from collections.abc import Callable, Coroutine, Mapping
from typing import Any

import websockets
from websockets.asyncio.client import ClientConnection
from websockets.exceptions import ConnectionClosed

from frame.loop import LOOP

from .store import FLOW_STORE

logger = logging.getLogger(__name__)

FLOW_DOMAIN = "localhost:3000"
FLOW_SECURE = False

RECONNECT_DELAY = 2.0  # seconds
MAX_RECONNECT_DELAY = 60.0  # seconds
BACKOFF_FACTOR = 1.5


class FlowClient:
  phone_connected: asyncio.Event
  flow_connected: asyncio.Event
  _connection: ClientConnection | None
  _registered_listeners: dict[str, Callable[[Mapping], Any | Coroutine]]
  _registered_request_listeners: dict[
    str, Callable[[Mapping], Mapping | Coroutine[Any, Any, Mapping]]
  ]
  _outstanding_reqs: dict[int, asyncio.Future[Mapping]]

  def __init__(self) -> None:
    self.phone_connected = asyncio.Event()
    self.flow_connected = asyncio.Event()
    self._connection = None

    self._registered_listeners = {}
    self._registered_request_listeners = {}
    self._outstanding_reqs = {}

    logger.debug(f"Pairing URL: {FLOW_STORE.key}")

  @property
  def websocket_url(self) -> str:
    """The active WebSocket URL for this frame."""
    return f"ws{'s' if FLOW_SECURE else ''}://{FLOW_DOMAIN}/api/socket?role=device&key={FLOW_STORE.key}"

  @property
  def pairing_url(self) -> str:
    return f"http{'s' if FLOW_SECURE else ''}://{FLOW_DOMAIN}/?key={FLOW_STORE.key}"

  def register(
    self, msg_type: str, callback: Callable[[Mapping], Any | Coroutine]
  ) -> Callable[[], None]:
    self._registered_listeners[msg_type] = callback
    logger.info(f"New flow registered: {msg_type}")
    return lambda: (self._registered_listeners.pop(msg_type), None)[-1]

  def register_request(
    self, msg_type: str, callback: Callable[[Mapping], Any | Coroutine]
  ) -> Callable[[], None]:
    self._registered_request_listeners[msg_type] = callback
    logger.info(f"New flow request registered: {msg_type}")
    return lambda: (self._registered_request_listeners.pop(msg_type), None)[-1]

  # Lifecycle management

  async def run_forever(self) -> None:
    """Maintain connection with exponential backoff and jitter."""
    current_delay = RECONNECT_DELAY
    while True:
      try:
        await self.connect()
        current_delay = RECONNECT_DELAY
      except asyncio.CancelledError:
        break

      jitter = random.uniform(0.8, 1.2)
      sleep_time = min(current_delay * jitter, MAX_RECONNECT_DELAY)
      current_delay = min(current_delay * BACKOFF_FACTOR, MAX_RECONNECT_DELAY)
      try:
        await asyncio.sleep(sleep_time)
      except asyncio.CancelledError:
        break

  async def connect(self) -> None:
    """Connect to the WebSocket and process incoming messages."""
    try:
      logger.info("Flow Connecting")
      async with websockets.connect(self.websocket_url) as ws:
        self._connection = ws
        self.flow_connected.set()
        logger.info("Flow Connected: %s", self.websocket_url)

        async for raw in ws:
          await self._handle_message(raw)
    except (
      TimeoutError,
      ConnectionClosed,
      OSError,
    ) as exc:
      logger.warning("Flow connection lost: %s", exc)
    except asyncio.CancelledError:
      raise
    except Exception:
      logger.exception("Unexpected error in Flow client")

    logger.info("Flow Disconnected")
    self.phone_connected.clear()
    self.flow_connected.clear()
    self._connection = None

  async def send_json_now(self, payload: Mapping[str, Any]) -> None:
    """Send a JSON payload over the active WebSocket."""
    if self._connection is None or not self.flow_connected.is_set():
      raise ConnectionError("WebSocket is not connected")
    await self._connection.send(json.dumps(payload))

  async def send_json(self, payload: Mapping[str, Any]) -> None:
    await self.flow_connected.wait()
    await self.send_json_now(payload)

  async def send_message(
    self, message_type: str, fields: Mapping[str, Any] | None = None
  ):
    return await FLOW_CLIENT.send_json({"type": message_type, **(fields or {})})

  req_id = 0

  async def send_json_request_now(self, payload: Mapping[str, Any]) -> Mapping:
    """Send a JSON payload over the active WebSocket and await a response."""
    if self._connection is None or not self.flow_connected.is_set():
      raise ConnectionError("WebSocket is not connected")
    p = dict(payload)
    self.req_id += 1
    p["req_id"] = self.req_id
    future: asyncio.Future[Mapping] = LOOP.create_future()
    self._outstanding_reqs[self.req_id] = future
    await self._connection.send(json.dumps(p))
    return await future

  async def send_json_request(self, payload: Mapping[str, Any]) -> Mapping:
    await self.flow_connected.wait()
    return await self.send_json_request_now(payload)

  async def send_message_request(
    self, message_type: str, fields: Mapping[str, Any] | None = None
  ) -> Mapping:
    await self.flow_connected.wait()
    return await self.send_json_request_now({"type": message_type, **(fields or {})})

  async def _handle_message(self, raw: str | bytes) -> None:
    try:
      payload = json.loads(raw)
      if not isinstance(payload, dict):
        return
    except (ValueError, TypeError, UnicodeError) as exc:
      logger.warning("Received invalid JSON from Flow relay: %r (%s)", raw, exc)
      return

    logger.debug(f"Message: {payload}")

    res_req_id = payload.get("res_req_id")
    if res_req_id:
      req = self._outstanding_reqs.pop(res_req_id)
      req.set_result(payload)
      req.done()
      return

    msg_type = payload.get("type")

    if not isinstance(msg_type, str):
      logger.warning("Invalid Flow message type")
      return

    if msg_type == "phone_connected":
      logger.info("Phone Connected")
      self.phone_connected.set()
      LOOP.create_task(self.send_message("device_already_connected"))
      return

    if msg_type == "phone_already_connected":
      logger.info("Phone Connected")
      self.phone_connected.set()
      return

    if msg_type == "phone_disconnected":
      logger.info("Phone Disconnected")
      self.phone_connected.clear()
      return

    if msg_type in self._registered_listeners:
      callback = self._registered_listeners.get(msg_type)
      if not callback:
        return
      awaitable = callback(payload)
      if isinstance(awaitable, Coroutine):
        asyncio.create_task(awaitable)
    elif msg_type in self._registered_request_listeners:
      callback = self._registered_request_listeners.get(msg_type)
      if not callback:
        return
      # TODO: handle errors in callbacks and respond in a way that rejects the promise
      awaitable = callback(payload)
      asyncio.create_task(self._respond(payload.get("req_id"), awaitable))
    else:
      logger.warning(f"Unhandled Flow message type: {msg_type}")

  async def _respond(
    self, req_id: int, awaitable: Mapping | None | Coroutine[Any, Any, Mapping | None]
  ):
    if isinstance(awaitable, Coroutine):
      awaitable = await awaitable
    if awaitable is None:
      return await self.send_json(
        {
          "res_req_id": req_id,
        }
      )
    await self.send_json({"res_req_id": req_id, **awaitable})


FLOW_CLIENT = FlowClient()
LOOP.create_task(FLOW_CLIENT.run_forever())
