"""Google Photos Picker flow integrated with the Photos Library API."""

import asyncio
import logging
import re
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from frame.flow import FLOW_CLIENT
from frame.loop import LOOP
from frame.utils import timestamp

from .account import ALL_SCOPES
from .client import GOOGLE_CLIENT
from .photos import GooglePhotosAPI
from .store import GOOGLE_STORE

logger = logging.getLogger(__name__)

BASE_URL = "https://photospicker.googleapis.com/v1"
SCOPES = {
  "https://www.googleapis.com/auth/photospicker.mediaitems.readonly",
}
ALL_SCOPES.update(SCOPES)

DEFAULT_MAX_ITEM_COUNT = 2000
DEFAULT_POLL_INTERVAL = 3.0
DEFAULT_TIMEOUT = 1800.0


@dataclass(frozen=True, slots=True)
class GooglePhotosPickerPollingConfig:
  poll_interval: str = "3s"
  timeout_in: str = "1800s"


@dataclass(frozen=True, slots=True)
class GooglePhotosPickerConfig:
  max_item_count: str = "2000"


@dataclass(frozen=True, slots=True)
class GooglePhotosPickerSession:
  id: str
  picker_uri: str
  expire_time: datetime | None = None
  polling_config: GooglePhotosPickerPollingConfig = field(
    default_factory=GooglePhotosPickerPollingConfig
  )
  picking_config: GooglePhotosPickerConfig = field(
    default_factory=GooglePhotosPickerConfig
  )
  media_items_set: bool = False


@dataclass(frozen=True, slots=True)
class GooglePhotosPickerPendingSelection:
  session: GooglePhotosPickerSession
  album_id: str | None
  title: str


def _pending_to_store(pending: GooglePhotosPickerPendingSelection) -> dict[str, Any]:
  session = pending.session
  return {
    "session": {
      "id": session.id,
      "picker_uri": session.picker_uri,
      "expire_time": session.expire_time.isoformat() if session.expire_time else None,
      "polling_config": {
        "poll_interval": session.polling_config.poll_interval,
        "timeout_in": session.polling_config.timeout_in,
      },
      "picking_config": {"max_item_count": session.picking_config.max_item_count},
      "media_items_set": session.media_items_set,
    },
    "album_id": pending.album_id,
    "title": pending.title,
  }


def _pending_from_store(payload: Any) -> GooglePhotosPickerPendingSelection:
  if isinstance(payload, GooglePhotosPickerPendingSelection):
    return payload
  if not isinstance(payload, Mapping):
    raise TypeError("Pending picker session payload must be a mapping")
  session_payload = payload["session"]
  polling = session_payload.get("polling_config", {})
  picking = session_payload.get("picking_config", {})
  session = GooglePhotosPickerSession(
    id=str(session_payload["id"]),
    picker_uri=str(session_payload["picker_uri"]),
    expire_time=timestamp(session_payload.get("expire_time")),
    polling_config=GooglePhotosPickerPollingConfig(
      poll_interval=str(polling.get("poll_interval", f"{DEFAULT_POLL_INTERVAL}s")),
      timeout_in=str(polling.get("timeout_in", f"{DEFAULT_TIMEOUT}s")),
    ),
    picking_config=GooglePhotosPickerConfig(
      max_item_count=str(picking.get("max_item_count", "2000")),
    ),
    media_items_set=bool(session_payload.get("media_items_set", False)),
  )
  return GooglePhotosPickerPendingSelection(
    session=session,
    album_id=payload.get("album_id"),
    title=str(payload["title"]),
  )


def _seconds(duration: str | None, fallback: float) -> float:
  if not duration:
    return fallback
  match = re.fullmatch(r"(\d+(?:\.\d+)?)s", duration)
  return max(0.0, float(match.group(1))) if match else fallback


def _session_from_payload(payload: Mapping[str, Any]) -> GooglePhotosPickerSession:
  polling = payload.get("pollingConfig") or {}
  picking = payload.get("pickingConfig") or {}
  return GooglePhotosPickerSession(
    id=str(payload["id"]),
    picker_uri=str(payload["pickerUri"]),
    expire_time=timestamp(payload.get("expireTime")),
    polling_config=GooglePhotosPickerPollingConfig(
      poll_interval=str(polling.get("pollInterval", f"{DEFAULT_POLL_INTERVAL}s")),
      timeout_in=str(polling.get("timeoutIn", f"{DEFAULT_TIMEOUT}s")),
    ),
    picking_config=GooglePhotosPickerConfig(
      max_item_count=str(picking.get("maxItemCount", "2000")),
    ),
    media_items_set=bool(payload.get("mediaItemsSet", False)),
  )


class GooglePhotosPickerSessions:
  """Create, poll, enumerate, and delete Google Photos Picker sessions."""

  async def create(self, max_item_count: int) -> GooglePhotosPickerSession:
    payload = await GOOGLE_CLIENT.request_json(
      "POST",
      f"{BASE_URL}/sessions",
      json={"pickingConfig": {"maxItemCount": str(max_item_count)}},
    )
    return _session_from_payload(payload)

  async def wait_until_ready(self, session: GooglePhotosPickerSession) -> bool:
    timeout = _seconds(session.polling_config.timeout_in, DEFAULT_TIMEOUT)
    if timeout == 0:
      return False
    deadline = time.monotonic() + timeout
    poll_interval = _seconds(
      session.polling_config.poll_interval, DEFAULT_POLL_INTERVAL
    )

    while time.monotonic() < deadline:
      await asyncio.sleep(min(poll_interval, max(0, deadline - time.monotonic())))
      state = await GOOGLE_CLIENT.request_json(
        "GET", f"{BASE_URL}/sessions/{session.id}"
      )
      if state.get("mediaItemsSet"):
        return True
      polling = state.get("pollingConfig") or {}
      poll_interval = _seconds(polling.get("pollInterval"), poll_interval)
      timeout_in = polling.get("timeoutIn")
      if timeout_in is not None and _seconds(timeout_in, timeout) == 0:
        return False
    return False

  async def list_media_items(self, session_id: str) -> tuple[Mapping[str, Any], ...]:
    items: list[Mapping[str, Any]] = []
    page_token: str | None = None
    while True:
      params = {"sessionId": session_id, "pageSize": "100"}
      if page_token:
        params["pageToken"] = page_token
      payload = await GOOGLE_CLIENT.request_json(
        "GET", f"{BASE_URL}/mediaItems", params=params
      )
      items.extend(
        item for item in payload.get("mediaItems", []) if isinstance(item, Mapping)
      )
      page_token = payload.get("nextPageToken")
      if not page_token:
        return tuple(items)

  async def delete(self, session_id: str) -> None:
    try:
      await GOOGLE_CLIENT.request_json("DELETE", f"{BASE_URL}/sessions/{session_id}")
    except Exception:
      logger.warning("Could not delete Google Photos Picker session %s", session_id)


GOOGLE_PHOTOS_PICKER_SESSIONS = GooglePhotosPickerSessions()


class GooglePhotosPickerAPI(GooglePhotosAPI):
  """Add Picker selection and Flow operations to the Library API provider."""

  async def create_selection(
    self,
    *,
    album_id: str | None = None,
    title: str | None = None,
    max_item_count: int = DEFAULT_MAX_ITEM_COUNT,
  ) -> GooglePhotosPickerPendingSelection:
    from .store import GOOGLE_STORE

    if not 1 <= max_item_count <= DEFAULT_MAX_ITEM_COUNT:
      raise ValueError(f"max_item_count must be between 1 and {DEFAULT_MAX_ITEM_COUNT}")
    albums = await self.list_albums()
    existing_album = next((album for album in albums if album.id == album_id), None)
    if album_id and existing_album is None:
      raise ValueError(f"Unknown Google Photos album: {album_id}")

    title = title or (existing_album.title if existing_album else "Frame Photos")
    session = await GOOGLE_PHOTOS_PICKER_SESSIONS.create(max_item_count)
    pending = GooglePhotosPickerPendingSelection(
      session=session,
      album_id=album_id,
      title=title,
    )
    pending_sessions = dict(GOOGLE_STORE.photos_picker_pending_sessions)
    pending_sessions[session.id] = _pending_to_store(pending)
    GOOGLE_STORE.photos_picker_pending_sessions = pending_sessions
    LOOP.create_task(self._finish_selection(pending))
    return pending

  async def _finish_selection(
    self, pending: GooglePhotosPickerPendingSelection
  ) -> None:
    from .store import GOOGLE_STORE

    session_id = pending.session.id
    try:
      ready = await GOOGLE_PHOTOS_PICKER_SESSIONS.wait_until_ready(pending.session)
      if not ready:
        await self._send_flow(
          "google.photos.picker.cancelled", {"albumId": pending.album_id}
        )
        return

      items = await GOOGLE_PHOTOS_PICKER_SESSIONS.list_media_items(session_id)
      album_id, imported_count = await self.import_picked_items(
        items, album_id=pending.album_id, album_title=pending.title
      )
      if album_id is None:
        await self._send_flow(
          "google.photos.picker.completed", {"albumId": None, "photoCount": 0}
        )
      else:
        photos = await self.list_photos(album_id=album_id)
        albums = await self.list_albums()
        album = next((item for item in albums if item.id == album_id), None)
        await self._send_flow(
          "google.photos.picker.completed",
          {
            "albumId": album_id,
            "title": album.title if album else pending.title,
            "photoCount": len(photos),
            "addedCount": imported_count,
          },
        )
    except asyncio.CancelledError:
      raise
    except Exception as exc:
      logger.exception("Google Photos Picker session %s failed", session_id)
      await self._send_flow(
        "google.photos.picker.error",
        {"albumId": pending.album_id, "message": str(exc)},
      )
    finally:
      await GOOGLE_PHOTOS_PICKER_SESSIONS.delete(session_id)
      pending_sessions = dict(GOOGLE_STORE.photos_picker_pending_sessions)
      pending_sessions.pop(session_id, None)
      GOOGLE_STORE.photos_picker_pending_sessions = pending_sessions

  async def _send_flow(self, message_type: str, fields: Mapping[str, Any]) -> None:
    try:
      await FLOW_CLIENT.send_json({"type": message_type, **fields})
    except Exception:
      logger.warning("Could not send Flow message %s", message_type, exc_info=True)

  async def _on_select(self, message: dict) -> None:
    album_id = message.get("albumId")
    try:
      pending = await self.create_selection(
        album_id=str(album_id) if album_id else None,
        title=str(message["title"]) if message.get("title") else None,
        max_item_count=int(message.get("maxItemCount", DEFAULT_MAX_ITEM_COUNT)),
      )
      picker_uri = pending.session.picker_uri.rstrip("/") + "/autoclose"
      await self._send_flow(
        "google.photos.picker.session",
        {
          "albumId": pending.album_id,
          "title": pending.title,
          "sessionId": pending.session.id,
          "url": picker_uri,
          "pickerUri": picker_uri,
        },
      )
    except Exception as exc:
      logger.exception("Could not start Google Photos Picker session")
      await self._send_flow(
        "google.photos.picker.error",
        {"albumId": str(album_id) if album_id else None, "message": str(exc)},
      )

  async def _on_list_albums(self, _: dict) -> None:
    try:
      albums = await self.list_albums()
      await self._send_flow(
        "google.photos.picker.albums",
        {
          "albums": [
            {
              "id": album.id,
              "title": album.title,
              "coverPhotoId": album.cover_photo_id,
            }
            for album in albums
          ]
        },
      )
    except Exception as exc:
      logger.exception("Could not list Google Photos albums")
      await self._send_flow("google.photos.picker.error", {"message": str(exc)})


GOOGLE_PHOTOS_PICKER_API = GooglePhotosPickerAPI()

FLOW_CLIENT.register(
  "google.photos.picker.select[post]", GOOGLE_PHOTOS_PICKER_API._on_select
)
FLOW_CLIENT.register(
  "google.photos.picker.amend[post]", GOOGLE_PHOTOS_PICKER_API._on_select
)
FLOW_CLIENT.register(
  "google.photos.picker.albums[get]", GOOGLE_PHOTOS_PICKER_API._on_list_albums
)


def resume_pending_picker_sessions() -> None:
  """Resume in-flight Picker sessions after a process restart."""

  valid_pending_sessions: dict[str, Any] = {}
  for (
    session_id,
    pending_payload,
  ) in GOOGLE_STORE.photos_picker_pending_sessions.items():
    try:
      LOOP.create_task(
        GOOGLE_PHOTOS_PICKER_API._finish_selection(_pending_from_store(pending_payload))
      )
      valid_pending_sessions[session_id] = pending_payload
    except KeyError, TypeError, ValueError:
      logger.exception("Discarding an invalid stored Google Photos Picker session")
  if len(valid_pending_sessions) != len(GOOGLE_STORE.photos_picker_pending_sessions):
    GOOGLE_STORE.photos_picker_pending_sessions = valid_pending_sessions
